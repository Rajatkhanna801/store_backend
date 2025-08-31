from django.urls import path
from .views import CartViewSet

cart_list = CartViewSet.as_view({"get": "list"})
cart_add = CartViewSet.as_view({"post": "add"})
cart_update = CartViewSet.as_view({"patch": "update_item"})
cart_remove = CartViewSet.as_view({"delete": "remove_item"})

urlpatterns = [
    path("", cart_list, name="cart"),
    path("add/", cart_add, name="cart-add"),
    path("items/<int:item_id>/update/", cart_update, name="cart-item-update"),
    path("items/<int:item_id>/remove/", cart_remove, name="cart-item-remove"),
]
