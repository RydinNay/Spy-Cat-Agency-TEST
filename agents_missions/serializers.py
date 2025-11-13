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
        if self.instance:
            self.fields['name'].read_only = True
            self.fields['country'].read_only = True

    def update(self, instance, validated_data):
        if instance.mission.agent is None:
            raise serializers.ValidationError(
                "You cannot change the target in a mission without an agent."
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
        new_agent = validated_data.get('agent', instance.agent)

        if new_agent != instance.agent:
            if instance.status != SpyMission.MissionStatus.NOT_STARTED:
                raise serializers.ValidationError({
                    "agent_id": "You can only change the agent for missions in NOT_STARTED status."
                })

            # Проверяем только активные миссии нового агента
            active_missions = SpyMission.objects.filter(agent=new_agent)\
                .exclude(id=instance.id)\
                .exclude(status__in=[SpyMission.MissionStatus.DONE, SpyMission.MissionStatus.FAILED])
            if active_missions.exists():
                raise serializers.ValidationError({
                    "agent_id": "This agent has already been assigned to an active mission."
                })

            instance.agent = new_agent

        if instance.agent is not None:
            instance.status = validated_data.get('status', instance.status)
        else:
            if 'status' in validated_data:
                raise serializers.ValidationError(
                    "You cannot change the status of a mission without an agent."
                )

        instance.save()

        targets_data = self.initial_data.get('targets')
        if targets_data is not None:
            if instance.agent is None:
                raise serializers.ValidationError(
                    "You cannot update mission targets without an agent."
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
                    partial=True,
                    context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

        self.update_mission_status(instance)
        return instance

    def update_mission_status(self, mission):
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
