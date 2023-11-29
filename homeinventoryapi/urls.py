from django.urls import path, include
from rest_framework.routers import DefaultRouter
from homeinventoryapi import views, admin
from rest_framework.authtoken.views import obtain_auth_token

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'inventoryitem', views.InventoryItemViewSet, basename="inventoryitem")
router.register(r'shoppinglistitem', views.ShoppingListItemViewSet, basename="shoppinglistitem")
router.register(r'shoppinglist', views.ShoppingListViewSet, basename="shoppinglist")
router.register(r'users', views.UserViewSet, basename="user")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('gettoken/', obtain_auth_token),
]



