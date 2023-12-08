from datetime import timedelta

from django.db import models
from django.db.models import DateTimeField, CharField, \
    DecimalField, PositiveSmallIntegerField


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

class ShoppingListStatus(models.TextChoices):
    CREATED = "CREATED"
    SHOPPED = "SHOPPED"
    CANCELED = "CANCELED"
    UPDATED = "UPDATED"

class ShoppingList(models.Model):
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    status = CharField(choices=ShoppingListStatus.choices, max_length=50, default=ShoppingListStatus.CREATED)
    buyer = models.ForeignKey(
        "auth.User", related_name="shoppinglists", on_delete=models.CASCADE
    )

class ShoppingListItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    item_name = CharField(max_length=100)
    item_quantity = PositiveSmallIntegerField(default=1)
    item_brand = CharField(null=True, max_length=50)
    item_grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    expected_item_price_max = DecimalField(null=True, decimal_places=2, max_digits=10)
    shoppinglist = models.ForeignKey(to=ShoppingList, related_name="shoppinglistitems", on_delete=models.CASCADE)

    class Meta:
        ordering = ['created']

class InventoryItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    runout_at = DateTimeField(null=True)
    name = CharField(max_length=50)
    brand = CharField(max_length=100)
    grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    quantity = PositiveSmallIntegerField(null=True)
    payed_price = DecimalField(null=True, decimal_places=2, max_digits=10)
    barcode = CharField(max_length=50, unique=True)
    status = CharField(choices=InventoryItemStatus.choices, max_length=50, default=InventoryItemStatus.STORED)
    # armario superior da cozinha, armario abaixo da pia
    container = CharField(max_length=100, blank=True, default='armario abaixo da pia')
    # calculated fields
    min_alert = PositiveSmallIntegerField(default=1)
    stockout_at = DateTimeField(null=True, blank=True)

    shoppinglistitem = models.OneToOneField(ShoppingListItem, on_delete=models.CASCADE)

    creator = models.ForeignKey(
        "auth.User", related_name="inventoryitems", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['updated']

