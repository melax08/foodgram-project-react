import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_hex(value):
    find_hex = re.match('^#[0-9a-fA-F]{6}$', value)
    if not find_hex:
        raise ValidationError(
            _('%(value)s is not a HEX-code. Example: #FF0000 (red).'),
            params={'value': value},
        )
