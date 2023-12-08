from datetime import datetime, tzinfo, timedelta

import pytest
from _decimal import Decimal
from django.contrib.auth.models import User
from django.utils.timezone import now, localdate
from rest_framework.test import APIClient

from homeinventoryapi.models import ShoppingList, ShoppingListItem, InventoryItem

inventoryitem_json = {
            'name': 'chocolate',
            'quantity': '3',
            'barcode': '98435135138854',
            'brand': 'Lindt',
            'grocery_store': 'ALDI',
            'payed_price': '4.12',
            'min_alert': '3',
            'shoppinglistitem_id': '1'
        }

shoppinglistitem_json = {
    'item_name': 'chocolate',
    'item_quantity': '3',
    'item_brand': 'Lindt',
    'item_grocery_store': 'ALDI',
    'expected_item_price_max': '4.12'
}

shoppinglist_json = {
    "shoppinglist_items":
        [
            {
                "item_name": "blusa manga longa",
                "item_quantity": "1",
                "item_brand": "Duffy",
                "item_grocery_store": "LIDL",
                "expected_item_price_max": "5.34"
            },
            {
                "item_name": "cerveja",
                "item_quantity": "2",
                "item_brand": "Kaiser",
                "item_grocery_store": "CONTINENTE",
                "expected_item_price_max": "2.45"
            }
        ]
    }


@pytest.mark.django_db
def save_a_shoppinglistitem(user, json_dict=None, created=None):
    if not json_dict: json_dict = shoppinglistitem_json
    shoplist = ShoppingList.objects.create(buyer=user)
    if created:
        shoplist.created = created
        shoplist.save()
    assert shoplist is not None
    shoppinglistitem = ShoppingListItem.objects.create(item_name=json_dict['item_name'],
                                                item_quantity=json_dict['item_quantity'],
                                                item_brand=json_dict['item_brand'],
                                                item_grocery_store=json_dict['item_grocery_store'],
                                                expected_item_price_max=Decimal(json_dict['expected_item_price_max']),
                                                shoppinglist=shoplist)
    if created:
        shoppinglistitem.created = created
        shoppinglistitem.save()
    assert shoppinglistitem is not None
    return shoppinglistitem

@pytest.mark.django_db
def save_an_inventory_item(user, json_dict=None, barcode=None, created=None):
    shopitem:ShoppingListItem = save_a_shoppinglistitem(user, created=created)
    if not json_dict: json_dict = inventoryitem_json
    inv = InventoryItem.objects\
        .create(name=json_dict['name'],quantity=json_dict['quantity'],
                barcode=barcode or json_dict['barcode'],brand=json_dict['brand'],
                grocery_store=json_dict['grocery_store'],
                payed_price=Decimal(json_dict['payed_price']),
                min_alert=json_dict['min_alert'],
                shoppinglistitem_id=shopitem.id or json_dict['shoppinglistitem_id'],
                creator=shopitem.shoppinglist.buyer)
    if created:
        inv.created = created
        inv.save()
    return inv

def create_similar_inventoryitems(user)->list[InventoryItem]:
    inv1:InventoryItem=save_an_inventory_item(user, barcode='298749384777')
    created = inv1.created
    inv1.created = created - timedelta(days=20)
    inv1.runout_at = created - timedelta(days=10)
    inv1.save() # 10 days of consumption
    inv2=save_an_inventory_item(user, barcode='334395792438')
    created = inv2.created
    inv2.created = created - timedelta(days=30)
    inv2.runout_at = created - timedelta(days=15)
    inv2.save() # 15 days of consumption
    inv3=save_an_inventory_item(user, barcode='093434545563')
    created = inv3.created
    inv3.created = created - timedelta(days=13)
    inv3.runout_at = created - timedelta(days=7)
    inv3.save() # 6 days of consumption
    total_consumption_in_seconds_avg = ((inv1.runout_at.date() - inv1.created.date()).total_seconds() +
                                       (inv2.runout_at.date() - inv2.created.date()).total_seconds() +
                                       (inv3.runout_at.date() - inv3.created.date()).total_seconds()) / 3
    return [inv1, inv2, inv3], total_consumption_in_seconds_avg

