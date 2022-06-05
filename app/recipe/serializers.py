"""
Serializers for the Recipe app.
"""

from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the Recipe model."""

    class Meta:
        """Meta class for the RecipeSerializer."""

        model = Recipe
        fields = (
            'id',
            'title',
            'time_minutes',
            # 'description',
            'price',
            'link',
            # 'user',
            # 'ingredients',
            # 'tags',
            # 'created_at',
            # 'updated_at',
        )
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
