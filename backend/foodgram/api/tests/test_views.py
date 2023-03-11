from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate

from recipes.models import Recipe, Tag, Ingredient

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
        # self.authorized_client.force_login(self.user)

    def test_get_recipe(self):
        """Smoke test. Anonim user can see the recipes."""
        response = self.authorized_client.get(
            reverse('api:recipes-list'),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_create_recipe(self):
    #     """
    #     Ensure user can create a recipe.
    #     """
    #     # url = reverse('api:recipes')
    #     data = {
    #         'ingredients': [{
    #             "id": 1,
    #             "amount": 5
    #         }],
    #         'tags': [1],
    #         'image': 'data:image/png;base64,iVBORw0K',
    #         'name': 'Boiled potato',
    #         'text': 'Very delicious',
    #         'cooking_time': 5
    #     }
    #     response = self.authorized_client.post('/api/recipes/', data, format='json')
    #     force_authenticate(response, user=self.authorized_client)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Recipe.objects.count(), 1)
    #     self.assertEqual(Recipe.objects.get().name, 'Boiled potato')
