from django.urls import reverse
from rest_framework.test import override_settings

from foodgram import settings
from recipes.models import Cart, Favorite, Recipe

from .fixtures import TEMP_MEDIA_ROOT, Fixture


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FiltersTests(Fixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
