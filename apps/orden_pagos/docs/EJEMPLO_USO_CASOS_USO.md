# Ejemplos Prácticos de Uso - Casos de Uso de Órdenes de Pago

## Índice

1. [Generar PDF Simple](#1-generar-pdf-simple)
2. [Enviar Enlace de Pago](#2-enviar-enlace-de-pago)
3. [Vista DRF Completa](#3-vista-drf-completa)
4. [Comando de Gestión](#4-comando-de-gestión)
5. [Script de Administración](#5-script-de-administración)

---

## 1. Generar PDF Simple

### Caso: Necesitas generar un PDF para descargarlo directamente

```python
# En tu vista o servicio
from django.http import HttpResponse
from apps.orden_pagos.application.use_cases import GeneratePaymentOrderPDFUseCase
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


def descargar_pdf_orden(request, order_id):
    """Vista para descargar el PDF de una orden."""
    # Obtener la orden
    repository = PaymentOrderRepository()
    orden = repository.get_by_id(order_id)

    if not orden:
        return HttpResponse('Orden no encontrada', status=404)

    # Verificar permisos (ejemplo)
    if not request.user.has_perm('orden_pagos.view_paymentorder'):
        return HttpResponse('Sin permisos', status=403)

    # Generar PDF
    generador_pdf = GeneratePaymentOrderPDFUseCase()
    contenido_pdf = generador_pdf.execute(orden)

    # Preparar respuesta
    response = HttpResponse(contenido_pdf, content_type='application/pdf')
    filename = f'orden_pago_{orden.order_number}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    return response
```

---

## 2. Enviar Enlace de Pago

### Caso A: Envío Asíncrono con Celery (Recomendado)

```python
# En tu vista o servicio
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.orden_pagos.tasks import enviar_enlace_pago_orden


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_enlace_pago_api(request, order_id):
    """API para enviar enlace de pago de forma asíncrona."""
    try:
        # Disparar tarea asíncrona
        tarea = enviar_enlace_pago_orden.delay(order_id)

        return Response({
            'success': True,
            'message': 'Envío de enlace programado',
            'task_id': tarea.id
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Caso B: Envío Síncrono Directo

```python
# En tu vista o servicio
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from rest_framework.exceptions import ValidationError


@api_view(['POST'])
def enviar_enlace_directo(request, order_id):
    """Envío síncrono del enlace de pago."""
    try:
        # Instanciar casos de uso
        repository = PaymentOrderRepository()
        generador_pdf = GeneratePaymentOrderPDFUseCase()
        enviar_enlace = SendPaymentLinkUseCase(repository, generador_pdf)

        # Ejecutar
        resultado = enviar_enlace.execute(order_id)

        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e.detail)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 3. Vista DRF Completa

### ViewSet con Acciones Personalizadas

```python
# apps/orden_pagos/presentation/views/payment_order_viewset.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.orden_pagos.tasks import enviar_enlace_pago_orden


class PaymentOrderViewSet(viewsets.ModelViewSet):
    """ViewSet completo para órdenes de pago."""
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='enviar-enlace')
    def enviar_enlace_pago(self, request, pk=None):
        """
        Envía el enlace de pago al estudiante y asesor (asíncrono).
        
        POST /api/v1/ordenes-pago/{id}/enviar-enlace/
        """
        try:
            # Envío asíncrono
            tarea = enviar_enlace_pago_orden.delay(int(pk))

            return Response({
                'success': True,
                'message': 'Envío de enlace programado',
                'task_id': tarea.id
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='enviar-enlace-sync')
    def enviar_enlace_pago_sync(self, request, pk=None):
        """
        Envía el enlace de pago de forma síncrona.
        
        POST /api/v1/ordenes-pago/{id}/enviar-enlace-sync/
        """
        try:
            repository = PaymentOrderRepository()
            generador_pdf = GeneratePaymentOrderPDFUseCase()
            enviar_enlace = SendPaymentLinkUseCase(repository, generador_pdf)

            resultado = enviar_enlace.execute(int(pk))

            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='descargar-pdf')
    def descargar_pdf(self, request, pk=None):
        """
        Descarga el PDF de la orden.
        
        GET /api/v1/ordenes-pago/{id}/descargar-pdf/
        """
        try:
            repository = PaymentOrderRepository()
            orden = repository.get_by_id(int(pk))

            if not orden:
                return Response({
                    'error': 'Orden no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)

            # Generar PDF
            generador_pdf = GeneratePaymentOrderPDFUseCase()
            contenido_pdf = generador_pdf.execute(orden)

            # Retornar como descarga
            response = HttpResponse(contenido_pdf, content_type='application/pdf')
            filename = f'orden_{orden.order_number}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 4. Comando de Gestión

### Comando para enviar enlaces masivos

```python
# apps/orden_pagos/management/commands/enviar_enlaces_pendientes.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.orden_pagos.models import PaymentOrder
from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


class Command(BaseCommand):
    help = 'Envía enlaces de pago a órdenes pendientes sin envío'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Órdenes creadas en los últimos N días'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin enviar realmente'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']

        # Filtrar órdenes
        fecha_desde = timezone.now() - timedelta(days=dias)
        ordenes = PaymentOrder.objects.filter(
            status='PENDING',
            payment_link_date__isnull=True,
            created_at__gte=fecha_desde
        ).select_related('student', 'advisor')

        total = ordenes.count()
        self.stdout.write(f'Órdenes encontradas: {total}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN activado'))
            for orden in ordenes:
                self.stdout.write(
                    f'  - {orden.order_number}: {orden.student.email}'
                )
            return

        # Enviar enlaces
        repository = PaymentOrderRepository()
        generador_pdf = GeneratePaymentOrderPDFUseCase()
        enviar_enlace = SendPaymentLinkUseCase(repository, generador_pdf)

        exitosos = 0
        fallidos = 0

        for orden in ordenes:
            try:
                resultado = enviar_enlace.execute(orden.id)
                if resultado['success']:
                    exitosos += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {orden.order_number}: Enviado'
                        )
                    )
                else:
                    fallidos += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ {orden.order_number}: {resultado["message"]}'
                        )
                    )
            except Exception as e:
                fallidos += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ {orden.order_number}: {str(e)}'
                    )
                )

        # Resumen
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'Total procesadas: {total}')
        self.stdout.write(self.style.SUCCESS(f'Exitosas: {exitosos}'))
        self.stdout.write(self.style.ERROR(f'Fallidas: {fallidos}'))
```

**Uso del comando:**

```bash
# Ver qué órdenes se procesarían (dry-run)
python manage.py enviar_enlaces_pendientes --dry-run

# Enviar enlaces de órdenes de los últimos 7 días
python manage.py enviar_enlaces_pendientes

# Enviar enlaces de órdenes de los últimos 30 días
python manage.py enviar_enlaces_pendientes --dias=30
```

---

## 5. Script de Administración

### Script para reenviar enlaces

```python
# scripts/reenviar_enlace_pago.py
"""
Script para reenviar el enlace de pago de una orden específica.

Uso:
    python manage.py shell < scripts/reenviar_enlace_pago.py
"""

from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


def reenviar_enlace(numero_orden):
    """Reenvía el enlace de pago de una orden."""
    try:
        # Obtener orden
        repository = PaymentOrderRepository()
        orden = repository.get_by_order_number(numero_orden)

        if not orden:
            print(f'❌ Orden {numero_orden} no encontrada')
            return False

        print(f'📧 Reenviando enlace para orden {numero_orden}...')
        print(f'   Estudiante: {orden.student.nombre} {orden.student.apellido}')
        print(f'   Email: {orden.student.email}')
        print(f'   Estado: {orden.status}')

        # Enviar enlace
        generador_pdf = GeneratePaymentOrderPDFUseCase()
        enviar_enlace = SendPaymentLinkUseCase(repository, generador_pdf)

        resultado = enviar_enlace.execute(orden.id)

        if resultado['success']:
            print(f'✅ Enlace reenviado exitosamente')
            print(f'   Correos enviados: {", ".join(resultado["emails_sent"])}')
            return True
        else:
            print(f'❌ Error al reenviar: {resultado["message"]}')
            return False

    except Exception as e:
        print(f'❌ Error inesperado: {str(e)}')
        return False


# Ejemplo de uso
if __name__ == '__main__':
    # Cambiar por el número de orden real
    NUMERO_ORDEN = 'OP-2024-001'
    reenviar_enlace(NUMERO_ORDEN)
```

**Uso del script:**

```bash
# Opción 1: Con shell de Django
python manage.py shell
>>> from scripts.reenviar_enlace_pago import reenviar_enlace
>>> reenviar_enlace('OP-2024-001')

# Opción 2: Ejecutar directamente
python manage.py shell < scripts/reenviar_enlace_pago.py
```

---

## Bonus: Testing

### Test Unitario Simple

```python
# apps/orden_pagos/tests/test_use_cases.py

from django.test import TestCase
from unittest.mock import Mock, patch

from apps.orden_pagos.application.use_cases import (
    GeneratePaymentOrderPDFUseCase,
    SendPaymentLinkUseCase
)


class GeneratePDFUseCaseTest(TestCase):
    """Tests para GeneratePaymentOrderPDFUseCase."""

    def test_generate_pdf_success(self):
        """Debe generar un PDF correctamente."""
        # Arrange
        payment_order = Mock()
        payment_order.get_order_structure.return_value = {
            'order_number': 'OP-2024-001'
        }
        payment_order.order_number = 'OP-2024-001'

        use_case = GeneratePaymentOrderPDFUseCase()

        # Act
        with patch('apps.orden_pagos.application.use_cases.generate_payment_order_pdf.render_to_string'):
            with patch('apps.orden_pagos.application.use_cases.generate_payment_order_pdf.HTML'):
                pdf_content = use_case.execute(payment_order)

        # Assert
        self.assertIsNotNone(pdf_content)


class SendPaymentLinkUseCaseTest(TestCase):
    """Tests para SendPaymentLinkUseCase."""

    @patch('apps.orden_pagos.application.use_cases.send_payment_link.EmailMultiAlternatives')
    def test_send_link_success(self, mock_email):
        """Debe enviar el enlace correctamente."""
        # Arrange
        mock_repository = Mock()
        mock_pdf_generator = Mock()
        mock_pdf_generator.execute.return_value = b'PDF content'

        payment_order = Mock()
        payment_order.status = 'PENDING'
        payment_order.order_number = 'OP-2024-001'
        payment_order.student.email = 'student@test.com'
        payment_order.advisor.email = 'advisor@test.com'

        mock_repository.get_by_id_with_relations.return_value = payment_order

        use_case = SendPaymentLinkUseCase(mock_repository, mock_pdf_generator)

        # Act
        result = use_case.execute(order_id=1)

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(len(result['emails_sent']), 2)
```

---

## Resumen de Endpoints

| Método | Endpoint                                        | Descripción              |
|--------|-------------------------------------------------|--------------------------|
| POST   | `/api/v1/ordenes-pago/{id}/enviar-enlace/`      | Envía enlace (asíncrono) |
| POST   | `/api/v1/ordenes-pago/{id}/enviar-enlace-sync/` | Envía enlace (síncrono)  |
| GET    | `/api/v1/ordenes-pago/{id}/descargar-pdf/`      | Descarga PDF             |

## Comandos de Gestión

```bash
# Enviar enlaces pendientes
python manage.py enviar_enlaces_pendientes [--dias=7] [--dry-run]
```

---

**Fecha:** 2025-01-28
**Versión:** 1.0

