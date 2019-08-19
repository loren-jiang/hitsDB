from rest_framework import serializers
from .models import Compound, Library

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = ('zinc_id','smiles')
        
    def create(self, validated_data):
        return Compound.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key in validated_data:
            instance[key] = validated_data[key]
        instance.save()
        return instance

class NoSaveCompoundSerializer(CompoundSerializer):

    def __init__(self, *args, **kwargs):
        super(NoSaveCompoundSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        print("hi")
        c = Compound(**validated_data)
        return c

