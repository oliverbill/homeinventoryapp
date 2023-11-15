from django.contrib.auth.models import User
from rest_framework import serializers

from homeinventoryapi.models import ShoppingListItem, InventoryItem, GroceryStore, ShoppingListItemStatus


class InventoryItemSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="inventoryitem-detail")
    shoppinglistitem = serializers.HyperlinkedRelatedField(
        many=False, view_name="shoppinglistitem-detail", read_only=True
    )

    class Meta:
        model = InventoryItem
        fields = '__all__'
        read_only_fields = ['stockout_at', 'status', 'creator']

class ShoppingListItemSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="shoppinglistitem-detail")

    class Meta:
        model = ShoppingListItem
        fields = '__all__'
        read_only_fields = ['buyer', 'status']

    def validate_item_name(self, value):
        value_trimmed = value.replace(" ", "")
        if not value_trimmed.isalpha():
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

