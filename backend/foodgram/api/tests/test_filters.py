from rest_framework.test import override_settings

from .fixtures import Fixture, TEMP_MEDIA_ROOT


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FiltersTests(Fixture):

    def test_filters(self):
        ...
