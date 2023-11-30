import logging

from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from homeinventoryapi.models import ShoppingListItem, InventoryItem, ShoppingListStatus, ShoppingList
from homeinventoryapi.serializers import UserSerializer, ShoppingListItemSerializer, \
    InventoryItemSerializer, ShoppingListSerializer


@api_view(["GET"])
def api_root(request, format=None):
    logging.debug('getting into api_root()')
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "shoppinglistitems": reverse("shoppinglistitem-list", request=request, format=format),
            "shoppinglist": reverse("shoppinglist-list", request=request, format=format),
            "inventoryitems": reverse("inventoryitem-list", request=request, format=format),
        }
    )

# Only GET and DELETE(when item runs out) are allowed. InventoryItem creation is done by POST /shoppinglistitem
class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # show inventory_item pre-filled with shoppinglistitem(through GET) in the app screen to streamline the process
    def create(self, request, *args, **kwargs):
        logging.debug('getting into InventoryItemViewSet.create')
        if 'shoppinglistitem_id' not in request.data:
            return Response('shoppinglistitem_id not found in payload', status=status.HTTP_400_BAD_REQUEST)
        shoppinglistitem_id = request.data['shoppinglistitem_id']
        result = is_shoppinglistitem_in_use(shoppinglistitem_id)
        if not result:
            inventory_fields = populate_inventory_fields(shoppinglistitem_id, request)
            serializer: InventoryItemSerializer = self.get_serializer(data=inventory_fields)
            serializer.is_valid(raise_exception=True)
            serializer.save(creator=self.request.user, shoppinglistitem_id=shoppinglistitem_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        response = {'message': 'PUT method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        response = {'message': 'PATCH method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        logging.debug('getting into ShoppingListViewSet.perform_create()')
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        saved_shoppinglist = serializer.save(buyer=self.request.user, status=ShoppingListStatus.CREATED)

        if 'shoppinglist_items' in self.request.data:
            shoppinglist_items = self.request.data['shoppinglist_items']
            for item in shoppinglist_items:
                item['shoppinglist'] = serializer.data['url'] #http://testserver/shoppinglist/1/
                item_serializer = ShoppingListItemSerializer(data=item)
                item_serializer.is_valid(raise_exception=True)
                item_serializer.save(shoppinglist=saved_shoppinglist)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(f'shoppinglist_items not found in the payload',
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        response = {'message': 'PUT method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        response = {'message': 'PATCH method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

class ShoppingListItemViewSet(viewsets.ModelViewSet):
    queryset = ShoppingListItem.objects.all()
    serializer_class = ShoppingListItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        logging.debug('getting into ShoppingListItemViewSet.create()')
        shoppinglist_id = request.data['shoppinglist_id']
        shoppinglist = ShoppingList.objects.filter(pk=shoppinglist_id)
        if not shoppinglist.exists():
            return Response(f'shoppinglist does not exist: {shoppinglist_id}', status=status.HTTP_400_BAD_REQUEST)

        request.data['shoppinglist'] = reverse("shoppinglist-detail", args=shoppinglist_id)
        item_serializer:ShoppingListItemSerializer = self.get_serializer(data=request.data)
        item_serializer.is_valid(raise_exception=True)
        item_serializer.save(shoppinglist=shoppinglist.get())
        headers = self.get_success_headers(item_serializer.data)
        return Response(item_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        logging.debug('getting into ShoppingListItemViewSet.perform_update()')
        serializer.is_valid(raise_exception=True)
        shoppinglist = get_shoppinglist(self.request)
        if shoppinglist:
            shoppinglist_status = get_status(request=self.request)
            shoppinglist.status = shoppinglist_status
            shoppinglist.save()
            serializer.save(shoppinglist_id=shoppinglist.id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

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

def get_shoppinglist(request) -> ShoppingList:
    if 'shoppinglist_id' not in request.data: return False
    shoppinglist_id = request.data['shoppinglist_id']
    query = ShoppingList.objects.filter(pk=shoppinglist_id)
    if query.exists():
        return query.get()
    else:
        return Response(f'shoppinglist does not exist: {shoppinglist_id}', status=status.HTTP_400_BAD_REQUEST)

def get_status(request):
    logging.debug('update without barcode')
    if 'barcode' not in request.data:
        logging.debug('update without barcode')
        return ShoppingListStatus.UPDATED
    else:
        logging.debug('update with barcode')
        return ShoppingListStatus.SHOPPED

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

def get_field_in_request_or_none(request, fields) -> str:
    temp = [request.data[f] for f in fields if f in request.data]
    if len(temp) > 0:
        return temp[0]
    return None

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

