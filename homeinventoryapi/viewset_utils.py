import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

from homeinventoryapi.models import ShoppingListItem, ShoppingList, ShoppingListStatus, InventoryItem


def save_shoppinglistitem(request, saved_shoppinglist, serializer, viewset:viewsets.ModelViewSet):
    request.data['shoppinglist_id'] = saved_shoppinglist.id
    result = serializer.is_valid()
    if type(result) == str:
        logging.debug('serializer validation failed')
        viewset.queryset = ShoppingListItem.objects.all()
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(shoppinglist=saved_shoppinglist)
    headers = viewset.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


def is_shoppinglistitem_in_use(shoppinglistitem_id):
    shoppinglistitem_already_used = InventoryItem.objects.filter(shoppinglistitem_id=shoppinglistitem_id).exists()
    if not shoppinglistitem_already_used:
        shoppinglistitem_exists = ShoppingListItem.objects.filter(pk=shoppinglistitem_id).exists()
        if not shoppinglistitem_exists:
            msg = f"shoppinglistitem does not exists: {shoppinglistitem_id}"
        else:
            return False
    else:
        msg = f"shoppinglistitem already related to another inventoryitem: {shoppinglistitem_id}"
    return msg


def get_field_in_request_or_none(request, fields) -> str:
    temp = [request.data[f] for f in fields if f in request.data]
    if len(temp) > 0:
        return temp[0]
    return None


def populate_inventory_fields(shoppinglistitem_id, request):
    shoppinglistitem = ShoppingListItem.objects.get(pk=shoppinglistitem_id)
    name = get_field_in_request_or_none(request, ['name']) or shoppinglistitem.item_name
    brand = get_field_in_request_or_none(request, ['brand']) or shoppinglistitem.item_brand
    grocery_store = get_field_in_request_or_none(request, ['grocery_store']) or shoppinglistitem.item_grocery_store
    quantity = get_field_in_request_or_none(request, ['quantity']) or shoppinglistitem.item_quantity
    payed_price = get_field_in_request_or_none(request, ['payed_price']) or shoppinglistitem.expected_item_price_max
    barcode = get_field_in_request_or_none(request, ['barcode'])
    if not barcode:
        return Response('barcode not found in payload', status=status.HTTP_400_BAD_REQUEST)
    inventory_fields = {
        'name': name,
        'brand': brand,
        'grocery_store': grocery_store,
        'quantity': quantity,
        'payed_price': payed_price,
        'barcode': barcode
    }
    return inventory_fields
