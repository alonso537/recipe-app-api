"""
Serializers for the Recipe app.
"""

from pkg_resources import require
from rest_framework import serializers


from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model."""

    class Meta:
        """Meta class for the TagSerializer."""

        model = Tag
        fields = [
            'id',
            'name',
        ]
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the Recipe model."""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        """Meta class for the RecipeSerializer."""

        model = Recipe
        fields = [
            'id',
            'title',
            'time_minutes',
            # 'description',
            'price',
            'link',
            # 'user',
            # 'ingredients',
            'tags',
            # 'created_at',
            # 'updated_at',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Get or create tags."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj[0])

    def create(self, validated_data):
        """Create and return a new Recipe instance."""
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        #

        return recipe

    def update(self, instance, validated_data):
        """Update and return an existing Recipe instance."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
