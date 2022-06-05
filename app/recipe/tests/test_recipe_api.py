"""
Test for models.
"""

from decimal import Decimal


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create a recipe."""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.50'),
        'description': 'Sample description',
        'link': 'http://example.com',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create a user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='userExample.com', password='testpass')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_list_limited_to_user(self):
        """Test retrieving recipes for user."""
        other_user = create_user(
            email='other@example.com',
            password='testpass'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving a recipe detail."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': Decimal('5.08'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test updating a recipe with patch."""
        original_link = 'http://example.com'
        recipe = create_recipe(
            user=self.user,
            link=original_link,
            title='Original title',
        )

        payload = {
            'title': 'New title',
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test updating a recipe with put."""
        recipe = create_recipe(
            user=self.user,
            title='Original title',
            link='http://example.com',
            description='Original description',
        )

        payload = {
            'title': 'New title',
            'link': 'http://example.com/new',
            'description': 'New description',
            'time_minutes': 20,
            'price': Decimal('9.00'),

        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test updating a recipe with put."""
        new_user = create_user(email='user3@email.com', password='testpass')
        recipe = create_recipe(
            user=self.user,
        )

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_user(self):
        """Test deleting a recipe for other user."""
        other_user = create_user(
            email='example@email.com', password='testpass')

        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': Decimal('5.08'),
            'tags': [{'name': 'tag1'}, {'name': 'tag2'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')

        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': Decimal('5.08'),
            'tags': [{'name': 'Indian'}, {'name': 'tag2'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag on recipe update."""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'tag1'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='tag1')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assing_tag(self):
        """Test updating a recipe and assign a tag."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test updating a recipe and clear tags."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.tags.count(), 0)
