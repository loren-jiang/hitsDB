from rest_framework import serializers
from .models import Compound, Library

class CompoundSerializer(serializers.ModelSerializer):
    zinc_id = serializers.CharField(max_length=30)
    smiles = serializers.CharField(max_length=200)

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

    def validate_zinc_id(self, value):
        if not str(value).startswith("zinc"):
            raise serializers.ValidationError(u'Does not have the right prefix "zinc".')
        return value


# class NoSaveCompoundSerializer(serializers.Serializer):
#     zinc_id = serializers.CharField(max_length=30)
#     smiles = serializers.CharField(max_length=200)

#     def create(self, validated_data):
#         c = Compound(**validated_data)
#         return c
#     def validate_zinc_id(self, value):
#         print("inside validate_zinc_id")
#         if not str(value).startswith("zinc"):
#             raise serializers.ValidationError(u'Does not have the right prefix "zinc".')
#         return value

class NoSaveCompoundSerializer(CompoundSerializer):
    class Meta(CompoundSerializer.Meta):
        model = Compound
        fields = CompoundSerializer.Meta.fields

    def create(self, validated_data):
        c = Compound(**validated_data)
        return c