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
            serializer.save(buyer=self.request.user,
                            status=ShoppingListItemStatus.CREATED)

    def perform_update(self, serializer):
        logger.debug('getting into perform_update()')
        updated_shoplistitem = serializer.save(buyer=self.request.user,
                                               status=ShoppingListItemStatus.SHOPPED)
        barcode = None
        payed_price = None
        if 'barcode' in self.request.data:
            barcode = self.request.data['barcode']
        if 'payed_price' in self.request.data:
            payed_price = self.request.data['payed_price']

        inv = InventoryItem(creator=self.request.user, name=updated_shoplistitem.item_name,
                            brand=updated_shoplistitem.item_brand, barcode=barcode, payed_price=payed_price,
                            grocery_store=updated_shoplistitem.item_grocery_store,
                            quantity=updated_shoplistitem.item_quantity, shoppinglistitem=updated_shoplistitem)
        InventoryItem.save(inv)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    logger.debug('getting into UserViewSet')

