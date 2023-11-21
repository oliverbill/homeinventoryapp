import logging

from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, status
from rest_framework.authentication import TokenAuthentication
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

# Only GET and DELETE(when item runs out) are allowed. InventoryItem creation is done by POST /shoppinglistitem
class InventoryItemViewSet(viewsets.ModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # show inventory_item pre-filled with shoppinglistitem(through GET) in the app screen to streamline the process
    def perform_create(self, serializer):
        if serializer.is_valid():
            # POST request has to contain 'shoppinglistitem_id'
            if 'shoppinglistitem_id' in self.request.data:
                id = self.request.data['shoppinglistitem_id']
                updated_shoplistitem = ShoppingListItem.objects.get(pk=id)
                serializer.save(creator=self.request.user, shoppinglistitem=updated_shoplistitem)

    def update(self, request):
        response = {'message': 'PUT method is not allowed.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request):
        response = {'message': 'PATCH method is not allowed.'}
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
        if serializer.is_valid():
            if 'barcode' not in self.request.data:
                serializer.save(buyer=self.request.user,
                                status=ShoppingListItemStatus.UPDATED)
            else:
                serializer.save(buyer=self.request.user,
                                status=ShoppingListItemStatus.SHOPPED)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    logger = logging.getLogger(__name__)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    logger.debug('getting into UserViewSet')

