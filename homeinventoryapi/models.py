from django.db import models
from django.db.models import DateTimeField, CharField, \
    DecimalField, PositiveSmallIntegerField
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from homeinventoryapp import settings


class GroceryStore(models.TextChoices):
    ALDI = "ALDI"
    CONTINENTE = "CONTINENTE"
    LIDL = "LIDL"
    PINGO_DOCE = "PINGO DOCE"
    INTERMARCHE = "INTERMARCHE"
    OUTRO = "OUTRO"

class InventoryItemStatus(models.TextChoices):
    STORED = "STORED"
    RUNOUT = "RUNOUT"

class ShoppingListItemStatus(models.TextChoices):
    CREATED = "CREATED"
    SHOPPED = "SHOPPED"
    NOT_SHOPPED = "NOT_SHOPPED"
    UPDATED = "UPDATED"

class ShoppingListItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    item_name = CharField(max_length=100)
    item_quantity = PositiveSmallIntegerField(default=1)
    item_brand = CharField(null=True, max_length=50)
    item_grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    expected_item_price_max = DecimalField(decimal_places=2, max_digits=10)
    status = CharField(choices=ShoppingListItemStatus.choices, max_length=50, default=ShoppingListItemStatus.CREATED)

    buyer = models.ForeignKey(
        "auth.User", related_name="shoppinglistitems", on_delete=models.CASCADE
    )
    class Meta:
        ordering = ['created']

    def from_json(self, buyer, json_data):
        self.status = json_data['status']
        self.item_quantity = json_data['item_quantity']
        self.item_grocery_store = json_data['item_grocery_store']
        self.expected_item_price_max = json_data['expected_item_price_max']
        self.item_brand = json_data['item_brand']
        self.item_name = json_data['item_name']
        self.buyer = buyer
        return self

class InventoryItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    name = CharField(max_length=50)
    brand = CharField(max_length=100)
    grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    quantity = PositiveSmallIntegerField(null=True)
    payed_price = DecimalField(null=True, decimal_places=2, max_digits=10)
    barcode = CharField(max_length=50)
    status = CharField(choices=InventoryItemStatus.choices, max_length=50, default=InventoryItemStatus.STORED)
    # calculated fields
    min_alert = PositiveSmallIntegerField(default=1)
    stockout_at = DateTimeField(null=True, blank=True)

    shoppinglistitem = models.OneToOneField(ShoppingListItem, on_delete=models.CASCADE)

    creator = models.ForeignKey(
        "auth.User", related_name="inventoryitems", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['updated']

    def from_json(self, creator, shoppinglistitem, json_data):
        self.creator = creator
        self.name = json_data['name']
        self.brand = json_data['brand']
        self.barcode = json_data['barcode']
        self.payed_price = json_data['payed_price']
        self.grocery_store = json_data['grocery_store']
        self.quantity = json_data['quantity']
        self.shoppinglistitem = shoppinglistitem
        self.status = json_data['status']
        return self

    def from_shoppinglistitem(self, req_user, barcode, payed_price, updated_shoplistitem):
        self.creator = req_user
        self.name = updated_shoplistitem.item_name
        self.brand = updated_shoplistitem.item_brand
        self.barcode = barcode
        self.payed_price = payed_price
        self.grocery_store = updated_shoplistitem.item_grocery_store
        self.quantity = updated_shoplistitem.item_quantity
        self.shoppinglistitem = updated_shoplistitem
        self.status = InventoryItemStatus.STORED
        return self
