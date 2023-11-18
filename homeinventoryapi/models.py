from django.db import models
from django.db.models import DateTimeField, CharField, \
    DecimalField, PositiveSmallIntegerField

class GroceryStore(models.TextChoices):
    ALDI = "ALDI"
    CONTINENTE = "CONTINENTE"
    LIDL = "LIDL"
    PINGO_DOCE = "PINGO_DOCE"
    INTERMARCHE = "INTERMARCHE"
    OUTRO = "OUTRO"

class InventoryStatus(models.TextChoices):
    CREATED = "CREATED"
    STORED = "STORED"
    RUNOUT = "RUNOUT"

class ShoppingListItemStatus(models.TextChoices):
    CREATED = "CREATED"
    SHOPPED = "SHOPPED"
    NOT_SHOPPED = "NOT_SHOPPED"

class ShoppingListItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    item_name = CharField(max_length=100)
    item_quantity = PositiveSmallIntegerField(default=1)
    item_brand = CharField(null=True, max_length=50)
    item_grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    expected_item_price_max = DecimalField(decimal_places=2, max_digits=10)
    status = CharField(choices=InventoryStatus.choices, max_length=50, default=ShoppingListItemStatus.CREATED)

    buyer = models.ForeignKey(
        "auth.User", related_name="shoppinglistitems", on_delete=models.CASCADE
    )
    class Meta:
        ordering = ['created']

class InventoryItem(models.Model):
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    name = CharField(max_length=50)
    brand = CharField(max_length=100)
    grocery_store = CharField(choices=GroceryStore.choices, max_length=50)
    quantity = PositiveSmallIntegerField(null=True)
    payed_price = DecimalField(null=True, decimal_places=2, max_digits=10)
    barcode = CharField(null=True, max_length=50)
    # calculated fields
    min_alert = PositiveSmallIntegerField(default=1)
    stockout_at = DateTimeField(null=True, blank=True)
    status = CharField(choices=InventoryStatus.choices, max_length=50, default=InventoryStatus.CREATED)

    shoppinglistitem = models.OneToOneField(ShoppingListItem, on_delete=models.CASCADE)

    creator = models.ForeignKey(
        "auth.User", related_name="inventoryitems", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['updated']

