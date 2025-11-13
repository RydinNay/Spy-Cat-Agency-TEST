from rest_framework import serializers
from .models import SpyCats
import requests

class SpyCatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyCats
        fields = ['id', 'name', 'breed', 'salary']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['name'].read_only = True
            self.fields['breed'].read_only = True

    def validate_breed(self, value):
        response = requests.get("https://api.thecatapi.com/v1/breeds")
        if response.status_code != 200:
            raise serializers.ValidationError("Failed to verify breed with TheCatAPI.")
        breeds = [breed['name'].lower() for breed in response.json()]
        if value.lower() not in breeds:
            raise serializers.ValidationError(f"Breed '{value}' not found in TheCatAPI.")
        return value
