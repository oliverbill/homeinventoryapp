import logging

from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from homeinventoryapi.models import ShoppingListItem, InventoryItem, ShoppingListItemStatus
from homeinventoryapi.serializers import UserSerializer, ShoppingListItemSerializer, \
    InventoryItemSerializer


@api_view(["GET"])
def api_root(request, format=None):
    logging.debug('getting into api_root()')
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "shoppinglistitems": reverse("shoppinglistitem-list", request=request, format=format),
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
        serializer:InventoryItemSerializer = self.get_serializer(data=request.data)
        result = serializer.is_valid()
        if type(result) == str:
            logging.debug('serializer validation failed')
            self.queryset = InventoryItem.objects.all()
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        shoppinglistitem_id = self.request.data['shoppinglistitem_id']
        serializer.save(creator=self.request.user, shoppinglistitem_id=shoppinglistitem_id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request):
        response = {'message': 'PUT method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request):
        response = {'message': 'PATCH method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

class ShoppingListItemViewSet(viewsets.ModelViewSet):
    queryset = ShoppingListItem.objects.all()
    serializer_class = ShoppingListItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        logging.debug('getting into ShoppingListItemViewSet.perform_create()')
        if serializer.is_valid():
            serializer.save(buyer=self.request.user,
                            status=ShoppingListItemStatus.CREATED)

    def perform_update(self, serializer):
        logging.debug('getting into ShoppingListItemViewSet.perform_update()')
        if serializer.is_valid():
            if 'barcode' not in self.request.data:
                logging.debug('update without barcode')
                serializer.save(buyer=self.request.user,
                                status=ShoppingListItemStatus.UPDATED)
            else:
                logging.debug('update with barcode')
                serializer.save(buyer=self.request.user,
                                status=ShoppingListItemStatus.SHOPPED)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

