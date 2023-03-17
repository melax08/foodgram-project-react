import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, override_settings

from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Tag, TagRecipe)
from recipes.validators import validate_hex
from users.models import Follow

from .fixtures import base64img

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ModelsTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser',
                                            password='ItSTOOhard3',
                                            email='test@2241.ru')
        cls.another_user = User.objects.create_user(username='SecondUser',
                                                    password='SecondPass',
                                                    email='second@2241.ru')
        cls.tag = Tag.objects.create(name='test', color='#FF0000', slug='test')
        cls.ingredient = Ingredient.objects.create(name='Potato',
                                                   measurement_unit='kg')
        cls.recipe = Recipe.objects.create(author=ModelsTests.user,
                                           name='Fried chicken',
                                           image=base64img,
                                           text='Nice taste',
                                           cooking_time=10)
        cls.recipe_ingredient = IngredientRecipe.objects.create(
            ingredient=ModelsTests.ingredient,
            amount=2,
            recipe=ModelsTests.recipe
        )
        cls.recipe_tag = TagRecipe.objects.create(
            tag=ModelsTests.tag,
            recipe=ModelsTests.recipe
        )
        cls.favorite = Favorite.objects.create(user=ModelsTests.another_user,
                                               recipe=ModelsTests.recipe)
        cls.cart = Cart.objects.create(user=ModelsTests.another_user,
                                       recipe=ModelsTests.recipe)
        cls.follow = Follow.objects.create(user=ModelsTests.user,
                                           author=ModelsTests.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_hex_validator(self):
        """Test HEX color validator for color field."""
        wrong_test_value = 'Something else'
        correct_test_value = '#FF1234'

        # Direct test
        self.assertIsNone(validate_hex(correct_test_value))
        with self.assertRaises(ValidationError):
            validate_hex(wrong_test_value)

        # Create model object test
        tag = Tag.objects.create(name='slug',
                                 slug='slug',
                                 color=wrong_test_value)
        self.assertRaises(ValidationError, tag.full_clean)

    def test_models_have_correct_objects_name(self):
        """Models __str__ methods are working properly."""
        self.assertEqual(str(ModelsTests.recipe), ModelsTests.recipe.name)
        self.assertEqual(str(ModelsTests.tag), ModelsTests.tag.name)
        self.assertEqual(str(ModelsTests.ingredient),
                         ModelsTests.ingredient.name)
        self.assertEqual(str(ModelsTests.user), ModelsTests.user.username)
        expected_ing_recipe_str = (
            f'Ингредиент "{ModelsTests.ingredient.name}" для рецепта '
            f'"{ModelsTests.recipe.name}" в количестве: '
            f'{ModelsTests.recipe_ingredient.amount} '
            f'{ModelsTests.ingredient.measurement_unit}')
        self.assertEqual(str(ModelsTests.recipe_ingredient),
                         expected_ing_recipe_str)

        expected_tag_recipe_str = (f'Тег "{ModelsTests.tag}" '
                                   f'для рецепта "{ModelsTests.recipe}"')
        self.assertEqual(str(ModelsTests.recipe_tag), expected_tag_recipe_str)

        expected_favorite_str = (f'У пользователя {ModelsTests.another_user} '
                                 f'в избранном рецепт: {ModelsTests.recipe}')
        self.assertEqual(str(ModelsTests.favorite), expected_favorite_str)

        expected_cart_str = (f'У пользователя {ModelsTests.another_user} '
                             f'в корзине рецепт {ModelsTests.recipe}')
        self.assertEqual(str(ModelsTests.cart), expected_cart_str)

        expected_follow_str = (f'Пользователь "{ModelsTests.user}" подписан '
                               f'на автора "{ModelsTests.another_user}"')
        self.assertEqual(str(ModelsTests.follow), expected_follow_str)
