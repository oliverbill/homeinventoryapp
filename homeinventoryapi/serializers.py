from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, ModelSerializer

from homeinventoryapi.models import ShoppingListItem, InventoryItem, GroceryStore


class InventoryItemSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="inventoryitem-detail")
    shoppinglistitem = serializers.HyperlinkedRelatedField(
        many=False, view_name="shoppinglistitem-detail", read_only=True
    )

    class Meta:
        model = InventoryItem
        fields = '__all__'
        read_only_fields = ['stockout_at', 'status', 'creator']

    def validate_shoppinglistitem_id(self, value):
        value_trimmed = value.replace(" ", "")
        if not value_trimmed.isdigit()():
            raise serializers.ValidationError(f'shoppinglistitem_id must be numeric: {value}')
        return value

    def is_valid(self, *, raise_exception=False):
        shoppinglistitem_id = self.initial_data['shoppinglistitem_id']
        shoppinglistitem_already_used = InventoryItem.objects.filter(shoppinglistitem_id=shoppinglistitem_id).exists()
        if not shoppinglistitem_already_used:
            shoppinglistitem_exists = ShoppingListItem.objects.filter(pk=shoppinglistitem_id).exists()
            if not shoppinglistitem_exists:
                return f"shoppinglistitem does not exists: {shoppinglistitem_id}"
        else:
            return f"shoppinglistitem already related to another inventoryitem: {shoppinglistitem_id}"
        self.is_valid_from_super(True)
        return self.initial_data

    # metodo copiado de BaseSerializer para q os atributos "_validated_data" e "_errors"
    # sejam criados. Nao deu certo chamar por delegacao: self.base_serializer.is_valid.
    def is_valid_from_super(self, raise_exception=False):
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self.errors)

        return not bool(self._errors)

class ShoppingListItemSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="shoppinglistitem-detail")

    class Meta:
        model = ShoppingListItem
        fields = '__all__'
        read_only_fields = ['buyer', 'status']

    def validate_item_name(self, value):
        value_trimmed = value.replace(" ", "")
        if value_trimmed.isdigit():
            raise serializers.ValidationError(f'item name must be alphabetic: {value}')
        return value

    def validate_item_grocery_store(self, value):
        if [item for item in GroceryStore.choices if value in item] is None:
            raise serializers.ValidationError(f'item grocery store must be any of {GroceryStore.choices}: {value}')
        return value

class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="user-detail")
    inventoryitems = serializers.HyperlinkedRelatedField(
        many=True, view_name="inventoryitem-detail", read_only=True
    )
    shoppinglistitems = serializers.HyperlinkedRelatedField(
        many=True, view_name="shoppinglistitem-detail", read_only=True
    )

    class Meta:
        model = User
        fields = '__all__'

