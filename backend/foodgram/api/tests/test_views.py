import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase, override_settings

from recipes.models import Ingredient, Recipe, Tag

from .fixtures import base64img

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser',
                                            password='ItSTOOhard3',
                                            email='test@2241.ru')
        cls.tag = Tag.objects.create(name='test', color='#FF0000', slug='test')
        cls.ingredient = Ingredient.objects.create(name='Potato',
                                                   measurement_unit='kg')
        cls.recipe = Recipe.objects.create(author=RecipeTests.user,
                                           name='Fried chicken',
                                           image=base64img,
                                           text='Nice taste',
                                           cooking_time=10)
        Token.objects.create(user=RecipeTests.user)
        cls.token = Token.objects.get(user__username='TestUser')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = APIClient()
        self.authorized_client = APIClient()
        self.authorized_client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_api_create_recipe(self):
        """Authorized user can add recipes and anonymous is not."""
        current_recipes_count = Recipe.objects.count()
        data = {
            'ingredients': [{
                "id": 1,
                "amount": 5
            }],
            'tags': [1],
            'image': base64img,
            'name': 'Boiled potato',
            'text': 'Very delicious',
            'cooking_time': 5
        }
        auth_response = self.authorized_client.post(
            reverse('api:recipes-list'), data, format='json')
        self.assertEqual(auth_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), current_recipes_count + 1)
        self.assertEqual(Recipe.objects.first().name, 'Boiled potato')

        # Anonim user try to create recipe via POST-request
        anonim_response = self.guest_client.post(
            reverse('api:recipes-list'), data, format='json')
        self.assertEqual(anonim_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Recipe.objects.count(), current_recipes_count + 1)
        self.assertEqual(Recipe.objects.first().name, 'Boiled potato')

    def test_api_anonymous_user_requests(self):
        """Unauthorized user gets the right response codes
        with GET-requests."""
        urls = {
            reverse('api:recipes-list'): status.HTTP_200_OK,
            reverse(
                'api:recipes-download-shopping-cart'
            ): status.HTTP_401_UNAUTHORIZED,
            reverse('api:tags-list'): status.HTTP_200_OK,
            reverse('api:tags-detail',
                    kwargs={'pk': RecipeTests.tag.id}): status.HTTP_200_OK,
            reverse('api:ingredients-list'): status.HTTP_200_OK,
            reverse('api:ingredients-detail',
                    kwargs={
                        'pk': RecipeTests.ingredient.id
                    }): status.HTTP_200_OK,
            reverse('api:users-list'): status.HTTP_401_UNAUTHORIZED,
            reverse('api:users-detail',
                    kwargs={
                        'id': RecipeTests.user.id
                    }): status.HTTP_401_UNAUTHORIZED,
            reverse('api:users-subscriptions'): status.HTTP_401_UNAUTHORIZED,
            reverse('api:users-me'): status.HTTP_401_UNAUTHORIZED,
            'unexists-url': status.HTTP_404_NOT_FOUND
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, format='json')
                self.assertEqual(response.status_code, status_code)

    def test_api_authorized_user_requests(self):
        """Authorized user gets the right response codes with GET-requests."""
        urls = {
            reverse('api:recipes-list'): status.HTTP_200_OK,
            reverse(
                'api:recipes-download-shopping-cart'
            ): status.HTTP_200_OK,
            reverse('api:tags-list'): status.HTTP_200_OK,
            reverse('api:tags-detail',
                    kwargs={'pk': RecipeTests.tag.id}): status.HTTP_200_OK,
            reverse('api:ingredients-list'): status.HTTP_200_OK,
            reverse('api:ingredients-detail',
                    kwargs={
                        'pk': RecipeTests.ingredient.id
                    }): status.HTTP_200_OK,
            reverse('api:users-list'): status.HTTP_200_OK,
            reverse('api:users-detail',
                    kwargs={
                        'id': RecipeTests.user.id
                    }): status.HTTP_200_OK,
            reverse('api:users-subscriptions'): status.HTTP_200_OK,
            reverse('api:users-me'): status.HTTP_200_OK,
            'unexists-url': status.HTTP_404_NOT_FOUND
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, format='json')
                self.assertEqual(response.status_code, status_code)

    def test_api_anonymous_user_register(self):
        """Anonymous user can create an account."""
        current_users_count = User.objects.count()
        data = {
            "email": "test@example.ru",
            "username": "another",
            "first_name": "another",
            "last_name": "another",
            "password": "VerYHaRd12"
        }
        response = self.guest_client.post(reverse('api:users-list'),
                                          data,
                                          format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), current_users_count + 1)
        self.assertEqual(User.objects.last().username, 'another')
        data.pop('password')
        data['id'] = User.objects.last().id
        self.assertEqual(data, response.data)

    def test_api_user_change_password(self):
        """User can change password, anonymous get error."""
        new_password = 'NewTooHardPass'
        data = {
            "new_password": new_password,
            "current_password": "ItSTOOhard3"
        }
        response = self.authorized_client.post(
            reverse('api:users-set-password'),
            data,
            format='json'
        )
        user = User.objects.get(username=RecipeTests.user.username)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(user.check_password(new_password))

        guest_response = self.guest_client.post(
            reverse('api:users-set-password'),
            data,
            format='json'
        )
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_api_guest_can_login_user_logout(self):
        """Guest can get auth token via password and email. User can logout."""
        password = 'ItsHardToExplain'
        email = 'token@2241.ru'
        user = User.objects.create_user(email=email,
                                        password=password,
                                        username='TokenUser')
        data = {
            "password": password,
            "email": email
        }

        # Test login
        response = self.guest_client.post('/api/auth/token/login/',
                                          data,
                                          format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_user_token = Token.objects.get(user__username=user.username).key
        self.assertEqual(response.data.get('auth_token'), new_user_token)

        # Test logout
        new_authorized_client = APIClient()
        new_authorized_client.credentials(
            HTTP_AUTHORIZATION='Token ' + new_user_token)
        response = new_authorized_client.post('/api/auth/token/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(
            user__username=user.username).exists())
