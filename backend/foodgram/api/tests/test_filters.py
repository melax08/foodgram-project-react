from django.urls import reverse
from rest_framework import status
from rest_framework.test import override_settings

from foodgram import settings
from recipes.models import Cart, Favorite, Recipe, TagRecipe
from users.models import Follow

from .fixtures import TEMP_MEDIA_ROOT, Fixture


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FiltersTests(Fixture):

    def test_favorite_filter(self):
        """Filter by Favorite model works fine."""
        url = reverse('api:recipes-list')
        user_favorite_count = Favorite.objects.count()

        # While filter is True, show only favorited recipes.
        response = self.authorized_client_second.get(url + '?is_favorited=1',
                                                     format='json')
        self.assertEqual(len(response.data.get('results')),
                         user_favorite_count)
        self.assertEqual(response.data.get('results')[0].get('name'),
                         'Fried chicken №4')

        # While filter is False, show all recipes.
        response = self.authorized_client_second.get(url + '?is_favorited=0',
                                                     format='json')
        self.assertEqual(len(response.data.get('results')),
                         settings.REST_FRAMEWORK.get('PAGE_SIZE'))

    def test_cart_filter(self):
        """Filter by Cart model works fine."""
        url = reverse('api:recipes-list')
        user_cart_count = Cart.objects.count()

        # While filter is True, show only recipes that in shopping cart.
        response = self.authorized_client_second.get(
            url + '?is_in_shopping_cart=1',
            format='json'
        )
        self.assertEqual(len(response.data.get('results')),
                         user_cart_count)
        self.assertEqual(response.data.get('results')[0].get('name'),
                         'Fried chicken №1')

        # While filter is False, show all recipes.
        response = self.authorized_client_second.get(
            url + '?is_in_shopping_cart=0',
            format='json'
        )
        self.assertEqual(len(response.data.get('results')),
                         settings.REST_FRAMEWORK.get('PAGE_SIZE'))

    def test_author_filter(self):
        """Filter by Author works fine."""
        author = FiltersTests.another_user
        response = self.guest_client.get(
            reverse('api:recipes-list') + f'?author={author.id}',
            format='json'
        )
        self.assertEqual(len(response.data.get('results')),
                         Recipe.objects.filter(author=author).count())
        self.assertEqual(response.data.get('results')[0].get('name'),
                         FiltersTests.another_recipe.name)

    def test_tags_filter(self):
        """Filter by tags works fine."""
        url = reverse('api:recipes-list')
        count_of_recipes_with_tag = TagRecipe.objects.filter(
            tag=FiltersTests.tag).count()
        response = self.authorized_client.get(
            url + '?tags=test', format='json')
        self.assertEqual(len(response.data.get('results')),
                         count_of_recipes_with_tag)
        self.assertEqual(response.data.get('results')[0].get('name'),
                         FiltersTests.recipe.name)

    def test_subscriptions_recipes_limit(self):
        """Limit of recipes works fine in subscriptions."""
        Follow.objects.create(user=FiltersTests.another_user,
                              author=FiltersTests.user)
        url = reverse('api:users-subscriptions')

        test_limit_correct = 2
        test_limit_wrong = 'Something else'

        # recipes_limit param works as expected.
        response = self.authorized_client_second.get(
            url + f'?recipes_limit={test_limit_correct}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results')[0].get('recipes')),
                         test_limit_correct)

        # Validation error if not positive numeric value in recipes_limit.
        response = self.authorized_client_second.get(
            url + f'?recipes_limit={test_limit_wrong}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('recipes_limit'))
