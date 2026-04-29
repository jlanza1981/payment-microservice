from django.urls import path, include

from apps.orden_pagos.presentation.views.payment_link_validation_view import *

urlpatterns = [
    path('payment/', include([
        path('', PaymentOrderViewSet.as_view({'get': 'list', 'post': 'create'})),
        path('by-number/<str:order_number>/', PaymentOrderViewSet.as_view({'get': 'get_payment_order_by_number'})),
        path('<int:pk>/', PaymentOrderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
        path('<int:pk>/change-status/', PaymentOrderViewSet.as_view({'post': 'change_status'})),
        path('<int:pk>/structure/', PaymentOrderViewSet.as_view({'get': 'structure'})),
        path('<int:pk>/mark-as-paid/', PaymentOrderViewSet.as_view({'post': 'mark_as_paid'})),
        path('<int:pk>/cancel/', PaymentOrderViewSet.as_view({'post': 'cancel'})),
        path('<int:pk>/verify/', PaymentOrderViewSet.as_view({'post': 'verify'})),
        path('validate-token/<str:token>/', PaymentLinkValidationView.as_view({'post': 'validate'})),

    ])),
]
