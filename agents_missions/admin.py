from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import SpyMission, SpyTarget
from .serializers import SpyMissionSerializer, SpyTargetSerializer


@admin.register(SpyMission)
class SpyMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'status')
    search_fields = ('agent__name',)
    list_filter = ('status',)

    def save_model(self, request, obj, form, change):
        # Prepare data as from API
        targets_data = []
        if hasattr(obj, 'targets'):
            for target in obj.targets.all():
                targets_data.append({
                    'id': target.id,
                    'name': target.name,
                    'country': target.country,
                    'notes': target.notes,
                    'status': target.status
                })

        data = {
            'agent_id': obj.agent.id if obj.agent else None,
            'status': obj.status,
            'targets': targets_data
        }

        serializer = SpyMissionSerializer(instance=obj if change else None, data=data, partial=change)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            messages.success(request, "✅ SpyMission saved successfully via serializer.")
        except DRFValidationError as e:
            messages.error(request, f"❌ Validation error: {e}")
            raise Exception(f"Validation error from serializer: {e}")
        except Exception as e:
            messages.error(request, f"❌ Unexpected error: {e}")
            raise

    def has_delete_permission(self, request, obj=None):
        if obj and obj.agent is not None:
            return False
        return super().has_delete_permission(request, obj)
