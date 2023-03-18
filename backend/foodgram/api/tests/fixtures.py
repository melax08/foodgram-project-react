import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase, override_settings

from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Tag, TagRecipe)
from users.models import Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
base64img = ('data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP'
             '///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class Fixture(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser',
                                            password='ItSTOOhard3',
                                            email='test@2241.ru')
        cls.tag = Tag.objects.create(name='test', color='#FF0000', slug='test')
        cls.ingredient = Ingredient.objects.create(name='Potato',
                                                   measurement_unit='kg')
        cls.recipe = Recipe.objects.create(author=cls.user,
                                           name='Fried chicken',
                                           image=base64img,
                                           text='Nice taste',
                                           cooking_time=10)
        cls.recipe_ingredient = IngredientRecipe.objects.create(
            ingredient=cls.ingredient,
            amount=2,
            recipe=cls.recipe
        )
        Token.objects.create(user=cls.user)
        cls.token = Token.objects.get(user__username='TestUser')
        cls.another_user = User.objects.create_user(username='SecondUser',
                                                    password='SecondPass',
                                                    email='second@2241.ru')
        Token.objects.create(user=cls.another_user)
        cls.another_token = Token.objects.get(user__username='SecondUser')
        cls.recipe_tag = TagRecipe.objects.create(
            tag=cls.tag,
            recipe=cls.recipe
        )
        cls.favorite = Favorite.objects.create(user=cls.another_user,
                                               recipe=cls.recipe)
        cls.cart = Cart.objects.create(user=cls.another_user,
                                       recipe=cls.recipe)
        cls.follow = Follow.objects.create(user=cls.user,
                                           author=cls.another_user)

        objects_list = (Recipe(author=cls.user,
                               name=f'Fried chicken №{number}',
                               text='Nice taste',
                               cooking_time=10) for number in range(
            settings.REST_FRAMEWORK.get('PAGE_SIZE')))
        Recipe.objects.bulk_create(objects_list)
        Favorite.objects.create(user=cls.another_user,
                                recipe=Recipe.objects.get(
                                    name='Fried chicken №2'))
        Favorite.objects.create(user=cls.another_user,
                                recipe=Recipe.objects.get(
                                    name='Fried chicken №4'))
        Cart.objects.create(user=cls.another_user,
                            recipe=Recipe.objects.get(
                                name='Fried chicken №0'))
        Cart.objects.create(user=cls.another_user,
                            recipe=Recipe.objects.get(
                                name='Fried chicken №1'))
        cls.another_recipe = Recipe.objects.create(author=cls.another_user,
                                                   name='Kebab',
                                                   image=base64img,
                                                   text='well done',
                                                   cooking_time=55)

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
