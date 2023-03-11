from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from recipes.models import Ingredient, Tag

User = get_user_model()


class RecipeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.tag = Tag.objects.create(name='test', color='#FF0000', slug='test')
        cls.ingredient = Ingredient.objects.create(name='Potato',
                                                   measurement_unit='kg')

    def setUp(self):
        self.authorized_client = APIClient()

    def test_get_recipe(self):
        """Smoke test. Anonim user can see the recipes."""
        response = self.authorized_client.get(
            reverse('api:recipes-list'),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
