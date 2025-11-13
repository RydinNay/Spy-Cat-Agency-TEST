from django.db import models

from agents_cats.models import SpyCats


class SpyMission(models.Model):
    class MissionStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    agent = models.ForeignKey(
        SpyCats,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions'
    )

    status = models.CharField(
        max_length=20,
        choices=MissionStatus.choices,
        default=MissionStatus.NOT_STARTED
    )


class SpyTarget(models.Model):
    class TargetStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    mission = models.ForeignKey(
        SpyMission,
        on_delete=models.CASCADE,
        related_name='targets'
    )
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=200)
    notes = models.TextField(max_length=3000, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TargetStatus.choices,
        default=TargetStatus.NOT_STARTED
    )