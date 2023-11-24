from unittest import TestCase

import pytest
from rest_framework.exceptions import ValidationError

from homeinventoryapi.serializers import ShoppingListItemSerializer


class InventoryItemE2ETest(TestCase):
    def test_validate_item_name_fails_with_number(self):
        serializer = ShoppingListItemSerializer()
        with pytest.raises(ValidationError):
            serializer.validate_item_name("12124")

    def test_validate_item_name_succeeds_with_aplha(self):
        serializer = ShoppingListItemSerializer()
        result = serializer.validate_item_name("asdas12124")
        assert result == "asdas12124"

    def test_validate_item_name_succeeds_with_hiphen(self):
        serializer = ShoppingListItemSerializer()
        result = serializer.validate_item_name("coca-cola")
        assert result == "coca-cola"