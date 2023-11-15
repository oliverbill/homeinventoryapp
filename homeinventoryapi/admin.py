from django.contrib import admin

from homeinventoryapi.models import ShoppingListItem, InventoryItem

admin.site.register(ShoppingListItem)
admin.site.register(InventoryItem)