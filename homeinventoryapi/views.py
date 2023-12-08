import logging

from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.utils import json

from homeinventoryapi.models import ShoppingListItem, InventoryItem, ShoppingListStatus, ShoppingList, \
    InventoryItemStatus
from homeinventoryapi.serializers import UserSerializer, ShoppingListItemSerializer, \
    InventoryItemSerializer, ShoppingListSerializer
from homeinventoryapi.viewset_utils import is_shoppinglistitem_in_use, \
    populate_inventory_fields


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
        in_use = is_shoppinglistitem_in_use(shoppinglistitem_id)
        if not in_use:
            shoplistitem:ShoppingListItem = ShoppingListItem.objects.get(pk=shoppinglistitem_id)
            shoplistitem.shoppinglist.status = ShoppingListStatus.SHOPPED
            shoplistitem.shoppinglist.save()
            shoplistitem.refresh_from_db()
            inventory_fields = populate_inventory_fields(shoppinglistitem_id, request)
            serializer: InventoryItemSerializer = self.get_serializer(data=inventory_fields)
            serializer.is_valid(raise_exception=True)
            serializer.save(creator=self.request.user, shoppinglistitem_id=shoppinglistitem_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(in_use, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        response = {'message': 'PUT method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        response = {'message': 'PATCH method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance:InventoryItem = self.get_object()
        instance.status = InventoryItemStatus.RUNOUT
        instance.quantity = 0
        instance.runout_at = now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        shoppinglistitem_id = self.kwargs['pk']
        item:ShoppingListItem = ShoppingListItem.objects.get(pk=shoppinglistitem_id)
        shoppinglist = item.shoppinglist
        shoppinglist.status = ShoppingListStatus.UPDATED
        shoppinglist.save()
        serializer.save(shoppinglist_id=shoppinglist.id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

