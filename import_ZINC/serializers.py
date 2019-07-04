from rest_framework import serializers
from .models import Compound, Library

class CompoundJSONSerializer(serializers.Serializer):
    zinc_id = serializers.CharField(max_length=30)
    smiles = serializers.CharField(max_length=200)

    def create(self, validated_data):
        c = Compound(**validated_data)
        return c