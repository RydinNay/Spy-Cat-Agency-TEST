from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import SpyMission, SpyTarget
from .serializers import SpyMissionSerializer
from agents_cats.models import SpyCats


class SpyTargetInline(admin.TabularInline):
    model = SpyTarget
    fields = ('name', 'country', 'notes', 'status')
    extra = 1
    can_delete = True

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields or [])
        if obj is None or (obj and obj.agent is None):
            readonly.append('status')
        if obj:
            readonly += ['name', 'country']
        return readonly

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj else self.extra

    def has_add_permission(self, request, obj=None):
        return False if obj else True

    def has_delete_permission(self, request, obj=None):
        return False if obj else True


@admin.register(SpyMission)
class SpyMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'status')
    search_fields = ('agent__name',)
    list_filter = ('status',)
    inlines = [SpyTargetInline]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields or [])
        readonly.append('status')
        if obj and obj.status != SpyMission.MissionStatus.NOT_STARTED:
            readonly.append('agent')
        return readonly

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'agent':
            busy_agent_ids = SpyMission.objects.filter(
                status__in=[SpyMission.MissionStatus.NOT_STARTED, SpyMission.MissionStatus.IN_PROGRESS]
            ).exclude(agent__isnull=True).values_list('agent_id', flat=True)

            qs = SpyCats.objects.all().exclude(id__in=busy_agent_ids)

            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    mission = SpyMission.objects.get(pk=int(obj_id))
                    if mission.agent:
                        qs = qs | SpyCats.objects.filter(id=mission.agent.id)
                except (ValueError, SpyMission.DoesNotExist):
                    pass

            kwargs['queryset'] = qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.agent:
            active_mission = SpyMission.objects.filter(
                agent=obj.agent
            ).exclude(id=obj.id).filter(
                status__in=[SpyMission.MissionStatus.NOT_STARTED, SpyMission.MissionStatus.IN_PROGRESS]
            ).exists()
            if active_mission:
                messages.error(request, "❌ Этот агент уже назначен на активную миссию.")
                return

        super().save_model(request, obj, form, change)

        self.update_mission_status(obj)

        if obj.agent:
            targets = obj.targets.all()
            targets_data = [
                {'id': t.id, 'name': t.name, 'country': t.country, 'notes': t.notes, 'status': t.status}
                for t in targets
            ]
            serializer = SpyMissionSerializer(instance=obj, data={'agent_id': obj.agent.id, 'targets': targets_data}, partial=True)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except DRFValidationError as e:
                messages.error(request, f"❌ Validation error: {e}")
                raise
            except Exception as e:
                messages.error(request, f"❌ Unexpected error: {e}")
                raise

    def save_formset(self, request, form, formset, change):
        formset.save()
        mission = form.instance
        self.update_mission_status(mission)

        if mission.agent:
            targets = mission.targets.all()
            targets_data = [
                {'id': t.id, 'name': t.name, 'country': t.country, 'notes': t.notes, 'status': t.status}
                for t in targets
            ]
            serializer = SpyMissionSerializer(instance=mission, data={'agent_id': mission.agent.id, 'targets': targets_data}, partial=True)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except DRFValidationError as e:
                messages.error(request, f"❌ Validation error: {e}")
                raise
            except Exception as e:
                messages.error(request, f"❌ Unexpected error: {e}")
                raise

    def update_mission_status(self, mission):
        if mission.agent is None:
            return

        targets = mission.targets.all()
        if not targets:
            return

        statuses = [t.status for t in targets]

        if all(s == SpyTarget.TargetStatus.FAILED for s in statuses):
            mission.status = SpyMission.MissionStatus.FAILED
        elif all(s in [SpyTarget.TargetStatus.DONE, SpyTarget.TargetStatus.FAILED] for s in statuses):
            mission.status = SpyMission.MissionStatus.DONE
        elif any(s != SpyTarget.TargetStatus.NOT_STARTED for s in statuses):
            mission.status = SpyMission.MissionStatus.IN_PROGRESS

        mission.save()

    def has_delete_permission(self, request, obj=None):
        if obj and obj.agent is not None:
            return False
        return super().has_delete_permission(request, obj)
