"""
URL configuration for Payment Microservice.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from ninja import NinjaAPI

# Import routers from apps
# These will be imported when the apps are properly configured
# from apps.orden_pagos.presentation.api.routers.router import payment_orders_router
# from apps.pagos.presentation.api.routers import payments_router
# from apps.billing.presentation.api.routers import billing_router
# from apps.payment_providers.presentation.api.routers import webhooks_router

# Create Ninja API instance
api = NinjaAPI(
    title="Payment Microservice API",
    version="1.0.0",
    description="""
    Sistema completo de gestión de pagos como microservicio independiente.
    
    ## Características
    - Gestión de órdenes de pago
    - Procesamiento de pagos (PayPal, Stripe)
    - Facturación automática
    - Generación de PDFs
    - Envío de notificaciones
    
    ## Autenticación
    La API utiliza Bearer Token Authentication. Incluye el token en el header:
    `Authorization: Bearer <your-token>`
    """,
    docs_url="/api-docs/",  # Swagger UI - mismo patrón que API original
)

# Health check endpoint
@api.get("/health", tags=["Health"])
def health_check(request):
    """Check if the service is running"""
    return {"status": "healthy", "service": "payment-microservice", "version": "1.0.0"}

# Register routers from apps
# api.add_router("/payment-orders", payment_orders_router, tags=["Payment Orders"])
# api.add_router("/payments", payments_router, tags=["Payments"])
# api.add_router("/invoices", billing_router, tags=["Invoicing"])
# api.add_router("/webhooks", webhooks_router, tags=["Webhooks"])

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Ninja API - includes automatic OpenAPI/Swagger docs
    # Documentación disponible en: /api/v1/api-docs/
    path('api/v1/', api.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Payment Microservice Admin"
admin.site.site_title = "Payment Microservice"
admin.site.index_title = "Gestión del Sistema de Pagos"


