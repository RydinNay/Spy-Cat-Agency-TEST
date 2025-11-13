from django.db import models

class SpyCats(models.Model):
    name = models.CharField(max_length=100)
    experience = models.FloatField(default=0.0)
    breed = models.CharField(max_length=100)
    salary = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.name} ({self.breed})"