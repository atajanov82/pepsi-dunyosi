from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductListView.as_view()),
    path('buy/',      views.BuyView.as_view()),
    path('my/',       views.MyPurchasesView.as_view()),
]
