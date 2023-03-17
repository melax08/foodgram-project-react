from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import override_settings

from recipes.models import Tag
from recipes.validators import validate_hex

from .fixtures import TEMP_MEDIA_ROOT, Fixture

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ModelsTests(Fixture):

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
