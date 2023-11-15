import logging

from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from homeinventoryapi.models import ShoppingListItem, InventoryItem, ShoppingListItemStatus
from homeinventoryapi.serializers import UserSerializer, ShoppingListItemSerializer, \
    InventoryItemSerializer

logger = logging.getLogger('views.api_root()')

@api_view(["GET"])
def api_root(request, format=None):
    logger.debug('getting into api_root()')
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "shoppinglistitems": reverse("shoppinglistitem-list", request=request, format=format),
            "inventoryitems": reverse("inventoryitem-list", request=request, format=format),
        }
    )

class InventoryItemViewSet(viewsets.ModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        logger.debug('getting into create()')
        response = {'message': 'POST method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        logger.debug('getting into destroy()')
        response = {'message': 'DELETE method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

class ShoppingListItemViewSet(viewsets.ModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = ShoppingListItem.objects.all()
    serializer_class = ShoppingListItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        logger.debug('getting into perform_create()')
        if serializer.is_valid():
            newshoppinglistitem = serializer.save(buyer=self.request.user,
                                                  status=ShoppingListItemStatus.CREATED)

            inv = InventoryItem(creator=self.request.user, name=newshoppinglistitem.item_name,
                                brand=newshoppinglistitem.item_brand,
                                grocery_store=newshoppinglistitem.item_grocery_store,
                                quantity=newshoppinglistitem.item_quantity, shoppinglistitem=newshoppinglistitem)
            InventoryItem.save(inv)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    logger.debug('getting into UserViewSet')

