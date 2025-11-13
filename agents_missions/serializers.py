from rest_framework import serializers
from agents_cats.models import SpyCats
from .models import SpyMission, SpyTarget


class SpyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyTarget
        fields = ['id', 'name', 'country', 'notes', 'status']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Після створення робимо name та country readonly
        if self.instance:
            self.fields['name'].read_only = True
            self.fields['country'].read_only = True

    def update(self, instance, validated_data):
        """
        Оновлювати notes і status можна лише якщо місія має агента
        і таргет або місія не DONE
        """
        if instance.mission.agent is None:
            raise serializers.ValidationError(
                "Не можна змінювати таргет у місії без агента."
            )

        if instance.status != SpyTarget.TargetStatus.DONE and \
           instance.mission.status != SpyMission.MissionStatus.DONE:
            for field in ['notes', 'status']:
                if field in validated_data:
                    setattr(instance, field, validated_data[field])
        else:
            if 'status' in validated_data:
                setattr(instance, 'status', validated_data['status'])

        instance.save()
        return instance


class SpyMissionSerializer(serializers.ModelSerializer):
    targets = SpyTargetSerializer(many=True, required=False)
    agent_id = serializers.PrimaryKeyRelatedField(
        source='agent',
        queryset=SpyCats.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = SpyMission
        fields = ['id', 'agent_id', 'status', 'targets']
        read_only_fields = ['id']

    def create(self, validated_data):
        targets_data = validated_data.pop('targets', [])
        mission = SpyMission.objects.create(**validated_data)
        for target_data in targets_data:
            SpyTarget.objects.create(mission=mission, **target_data)
        self.update_mission_status(mission)
        return mission

    def update(self, instance, validated_data):
        # Залишаємо старого агента, якщо не передано
        agent = validated_data.get('agent', instance.agent)

        # Заборона зміни агента, якщо місія вже не NOT_STARTED
        if agent != instance.agent and instance.status != SpyMission.MissionStatus.NOT_STARTED:
            agent = instance.agent

        # Перевірка зайнятості агента по активних місіях
        if agent != instance.agent:
            old_missions = SpyMission.objects.filter(agent=agent).exclude(id=instance.id)
            # Звільняємо агента у завершених місіях
            old_missions.filter(status=SpyMission.MissionStatus.DONE).update(agent=None)
            if old_missions.exclude(status=SpyMission.MissionStatus.DONE).exists():
                raise serializers.ValidationError({
                    "agent_id": "Цей агент уже призначений на активну місію."
                })

        instance.agent = agent

        # Статус можна міняти лише якщо є агент
        if instance.agent is not None:
            instance.status = validated_data.get('status', instance.status)
        else:
            if 'status' in validated_data:
                raise serializers.ValidationError(
                    "Не можна змінювати статус місії без агента."
                )

        instance.save()

        # --- Оновлення таргетів через self.initial_data ---
        targets_data = self.initial_data.get('targets')
        if targets_data is not None:
            if instance.agent is None:
                raise serializers.ValidationError(
                    "Не можна оновлювати таргети місії без агента."
                )

            for target_data in targets_data:
                target_id = target_data.get('id')
                if not target_id:
                    continue
                try:
                    target = instance.targets.get(id=target_id)
                except SpyTarget.DoesNotExist:
                    continue

                serializer = SpyTargetSerializer(
                    instance=target,
                    data=target_data,
                    partial=True,  # Важливо, щоб не чекати name і country
                    context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

        self.update_mission_status(instance)
        return instance

    def update_mission_status(self, mission):
        """
        Автооновлення статусу місії за статусами таргетів:
        - Якщо хоч один таргет in_progress, місія стає in_progress
        - Якщо всі DONE або DONE+FAILED -> місія DONE
        - Якщо всі FAILED -> місія FAILED
        """
        if mission.agent is None:
            return

        targets = mission.targets.all()
        if not targets:
            return

        statuses = [t.status for t in targets]

        if mission.status == SpyMission.MissionStatus.NOT_STARTED and \
           any(s != SpyTarget.TargetStatus.NOT_STARTED for s in statuses):
            mission.status = SpyMission.MissionStatus.IN_PROGRESS
            mission.save()
            return

        if all(s == SpyTarget.TargetStatus.FAILED for s in statuses):
            mission.status = SpyMission.MissionStatus.FAILED
        elif all(s in [SpyTarget.TargetStatus.DONE, SpyTarget.TargetStatus.FAILED] for s in statuses):
            mission.status = SpyMission.MissionStatus.DONE

        mission.save()
