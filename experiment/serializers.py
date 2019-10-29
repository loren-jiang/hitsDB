# from rest_framework import serializers
# from .models import Compound, Library
# # TO DO --> implement model serialization for experiment views
# class CompoundSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Compound
#         fields = ('zinc_id', 'smiles', )

#     def create(self, validated_data):
#         return Compound(**validated_data)

#     # def update(self, instance, validated_data):
#     #     # instance.smiles = validated_data.get('email', instance.email)

#     # #     instance.content = validated_data.get('content', instance.content)
#     # #     instance.created = validated_data.get('created', instance.created)
#     #     return instance