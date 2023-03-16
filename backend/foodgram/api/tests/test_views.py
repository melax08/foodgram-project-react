import json
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase, override_settings

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Follow

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
        cls.another_user = User.objects.create_user(username='SecondUser',
                                                    password='SecondPass',
                                                    email='second@2241.ru')
        Token.objects.create(user=RecipeTests.another_user)
        cls.another_token = Token.objects.get(user__username='SecondUser')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = APIClient()
        self.authorized_client = APIClient()
        self.authorized_client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.authorized_client_second = APIClient()
        self.authorized_client_second.credentials(
            HTTP_AUTHORIZATION='Token ' + self.another_token.key)

    def test_api_create_recipe(self):
        """Authorized user can add recipes and anonymous is not.
        the author of the recipe is automatically
        set to the user who send request."""
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
        # Authenticated user can create a recipe.
        auth_response = self.authorized_client.post(
            reverse('api:recipes-list'), data, format='json')
        self.assertEqual(auth_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), current_recipes_count + 1)
        self.assertEqual(Recipe.objects.first().name, 'Boiled potato')

        # Author of boiled potato is request user.
        self.assertEqual(Recipe.objects.first().author, RecipeTests.user)

        # Anonymous can't create a recipe
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
            reverse('api:recipes-detail',
                    kwargs={'pk': RecipeTests.recipe.id}): status.HTTP_200_OK,
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
            reverse('api:recipes-detail',
                    kwargs={'pk': RecipeTests.recipe.id}): status.HTTP_200_OK,
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

    def test_api_patch_recipe(self):
        """Users can modify itself recipes via PATCH-requests."""
        recipes_count = Recipe.objects.count()
        new_text = 'More nice taste'
        data = {
            'ingredients': [{
                "id": 1,
                "amount": 666
            }],
            'tags': [1],
            'image': base64img,
            'name': 'Fried chicken',
            'text': new_text,
            'cooking_time': 1000
        }
        url = reverse('api:recipes-detail', kwargs={
            'pk': RecipeTests.recipe.id})

        response = self.authorized_client.patch(
            url,
            data,
            format='json'
        )

        # Author can modify recipe
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe.objects.first().text, new_text)
        self.assertEqual(Recipe.objects.count(), recipes_count)

        # Guest can't modify recipes
        data['text'] = 'Guest recipe!!!'
        guest_response = self.guest_client.patch(url, data, format='json')
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Recipe.objects.first().text, new_text)
        self.assertEqual(Recipe.objects.count(), recipes_count)

        # Only author can modify recipe
        data['text'] = "I also can change someone else's recipe!"
        another_user_response = self.authorized_client_second.patch(
            url,
            data,
            format='json'
        )
        self.assertEqual(another_user_response.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recipe.objects.first().text, new_text)
        self.assertEqual(Recipe.objects.count(), recipes_count)

    def test_api_delete_recipe(self):
        """Users can delete itself recipes via DELETE-requests."""
        recipe = Recipe.objects.create(author=RecipeTests.user,
                                       text="Kill me please",
                                       cooking_time=1)
        recipes_count = Recipe.objects.count()

        url = reverse('api:recipes-detail', kwargs={'pk': recipe.id})

        # Guest can't delete recipe
        guest_response = self.guest_client.delete(url)
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Recipe.objects.count(), recipes_count)

        # Only author can delete recipe
        another_user_response = self.authorized_client_second.delete(url)
        self.assertEqual(another_user_response.status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recipe.objects.count(), recipes_count)

        # Author can delete recipe
        author_response = self.authorized_client.delete(url)
        self.assertEqual(author_response.status_code,
                         status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.count(), recipes_count - 1)

    def test_api_user_subscribe(self):
        """Authorized user can subscribe to authors."""
        count_of_follows = Follow.objects.count()
        url = reverse('api:users-subscribe',
                      kwargs={'id': RecipeTests.another_user.id})
        response = self.authorized_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), count_of_follows + 1)
        self.assertTrue(Follow.objects.filter(
            user=RecipeTests.user,
            author=RecipeTests.another_user
        ).exists())

        count_of_follows = Follow.objects.count()

        # Can't subscribe twice to the same author
        response = self.authorized_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Follow.objects.count(), count_of_follows)

        # Can't subscribe itself
        response = self.authorized_client.post(reverse(
            'api:users-subscribe', kwargs={'id': RecipeTests.user.id}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Follow.objects.count(), count_of_follows)

        # Can't subscribe to non-existent author
        response = self.authorized_client.post(reverse(
            'api:users-subscribe', kwargs={'id': 666}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Follow.objects.count(), count_of_follows)

        # Guest can't subscribe
        guest_response = self.guest_client.post(url)
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Follow.objects.count(), count_of_follows)

    def test_api_user_unsubscribe(self):
        """Authorized user can unsubscribe from author."""
        url = reverse('api:users-subscribe',
                      kwargs={'id': RecipeTests.another_user.id})
        Follow.objects.create(user=RecipeTests.user,
                              author=RecipeTests.another_user)
        count_of_follows = Follow.objects.count()

        # Guest can't unsubscribe
        guest_response = self.guest_client.delete(url)
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Follow.objects.count(), count_of_follows)

        # Can't unsubscribe from non-existent author
        response = self.authorized_client.delete(
            reverse('api:users-subscribe', kwargs={'id': 666}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Follow.objects.count(), count_of_follows)

        # User can unsubscribe from author
        response = self.authorized_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Follow.objects.count(), count_of_follows - 1)
        self.assertFalse(Follow.objects.filter(
            user=RecipeTests.user,
            author=RecipeTests.another_user
        ).exists())

        # A user cannot unsubscribe from an author they are not following
        response = self.authorized_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Follow.objects.count(), count_of_follows - 1)

    def test_api_user_subscriptions_list(self):
        """The user can see who he is subscribed to."""
        url = reverse('api:users-subscriptions')
        Follow.objects.create(user=RecipeTests.another_user,
                              author=RecipeTests.user)

        expected_data = {
            'email': RecipeTests.user.email,
            'id': RecipeTests.user.id,
            'username': RecipeTests.user.username,
            'first_name': '',
            'last_name': '',
            'is_subscribed': True,
            'recipes': [
                {
                    'id': RecipeTests.recipe.id,
                    'name': RecipeTests.recipe.name,
                    'image': RecipeTests.recipe.image.url,
                    'cooking_time': RecipeTests.recipe.cooking_time
                }
            ],
            'recipes_count': RecipeTests.user.recipes.count()
        }

        # Guest can't see the subscriptions list
        guest_response = self.guest_client.get(url, format='json')
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertIsNotNone(guest_response.data.get('detail'))

        # The user can see who he is subscribed to.
        response = self.authorized_client_second.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(
                json.dumps(response.data.get('results')[0])
            ), expected_data)

    def test_api_recipe_add_to_favorite(self):
        """Authorized user can add recipe to favorite."""
        favorites_count = Favorite.objects.count()
        url = reverse('api:recipes-favorite',
                      kwargs={'pk': RecipeTests.recipe.id})

        # Guest can't add recipe to favorite
        guest_response = self.guest_client.post(url)
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(favorites_count, Favorite.objects.count())

        # Can't add non-existent recipe to favorite
        response = self.authorized_client_second.post(
            reverse('api:recipes-favorite', kwargs={'pk': 666}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Favorite.objects.count(), favorites_count)
        self.assertFalse(Favorite.objects.filter(user=RecipeTests.another_user,
                                                 recipe=666))

        # User can add recipe to favorite
        response = self.authorized_client_second.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), favorites_count + 1)
        self.assertTrue(Favorite.objects.filter(
            user=RecipeTests.another_user, recipe=RecipeTests.recipe).exists())

        # User can't add the same recipe to favorite again
        response = self.authorized_client_second.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Favorite.objects.count(), favorites_count + 1)

    def test_api_recipe_delete_from_favorite(self):
        """Authorized user can delete recipe from favorite."""
        url = reverse('api:recipes-favorite',
                      kwargs={'pk': RecipeTests.recipe.id})
        Favorite.objects.create(user=RecipeTests.another_user,
                                recipe=RecipeTests.recipe)
        favorites_count = Favorite.objects.count()

        # Guest can't delete recipe from favorite
        guest_response = self.guest_client.delete(url)
        self.assertEqual(guest_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(favorites_count, Favorite.objects.count())

        # User can't delete non-existent recipe
        response = self.authorized_client_second.delete(
            reverse('api:recipes-favorite', kwargs={'pk': 666}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(favorites_count, Favorite.objects.count())

        # User can delete recipe from favorite
        response = self.authorized_client_second.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), favorites_count - 1)
        self.assertFalse(Favorite.objects.filter(
            user=RecipeTests.another_user, recipe=RecipeTests.recipe).exists())

        # User can't delete recipe from favorite twice
        response = self.authorized_client_second.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Favorite.objects.count(), favorites_count - 1)

    def test_api_recipe_shopping_cart(self):
        pass

    def test_api_download_shopping_cart(self):
        pass
