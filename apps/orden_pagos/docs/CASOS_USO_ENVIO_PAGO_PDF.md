# Casos de Uso para Envío de Enlaces de Pago y Generación de PDF

## Resumen

Se han separado las responsabilidades de envío de enlaces de pago y generación de PDFs en casos de uso dedicados,
siguiendo el principio de responsabilidad única (SRP - Single Responsibility Principle).

## Casos de Uso Creados

### 1. `GeneratePaymentOrderPDFUseCase`

**Ubicación:** `apps/orden_pagos/application/use_cases/generate_payment_order_pdf.py`

**Responsabilidad:** Generar el PDF de una orden de pago con parámetros flexibles.

**Características:**

- Reutilizable en diferentes contextos
- Configurable (template, CSS, base_url)
- Maneja la generación con WeasyPrint
- Incluye método alternativo con datos personalizados

**Uso básico:**

```python
from apps.orden_pagos.application.use_cases import GeneratePaymentOrderPDFUseCase

# Instanciar el caso de uso
pdf_generator = GeneratePaymentOrderPDFUseCase()

# Generar PDF desde una orden
pdf_content = pdf_generator.execute(payment_order)

# Generar PDF con configuración personalizada
pdf_content = pdf_generator.execute(
    payment_order,
    base_url='http://example.com',
    template_name='pdf_order_payment.html',
    css_filename='custom_styles.css'
)

# Generar PDF con datos personalizados (sin instancia del modelo)
order_structure = {
    'order_number': 'OP-2024-001',
    'student': {'nombre': 'Juan', 'apellido': 'Pérez'},
    # ... más datos
}
pdf_content = pdf_generator.generate_with_custom_data(order_structure)
```

**Retorna:** `bytes` - Contenido del PDF generado

---

### 2. `SendPaymentLinkUseCase`

**Ubicación:** `apps/orden_pagos/application/use_cases/send_payment_link.py`

**Responsabilidad:** Enviar enlace de pago al estudiante y asesor, incluyendo el PDF adjunto.

**Características:**

- Valida que la orden esté en estado PENDING
- Genera el enlace de pago
- Usa `GeneratePaymentOrderPDFUseCase` para generar el PDF
- Envía correos al estudiante y asesor
- Actualiza fecha de envío del enlace
- Manejo robusto de errores

**Uso básico:**

```python
from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)
from apps.orden_pagos.infrastructure.repository.payment_order_repository import (
    PaymentOrderRepository
)

# Instanciar dependencias
repository = PaymentOrderRepository()
pdf_generator = GeneratePaymentOrderPDFUseCase()

# Instanciar el caso de uso
send_link_use_case = SendPaymentLinkUseCase(repository, pdf_generator)

# Ejecutar
result = send_link_use_case.execute(order_id=123)

# Con base_url personalizada
result = send_link_use_case.execute(order_id=123, base_url='http://example.com')
```

**Retorna:** `Dict[str, Any]` con la siguiente estructura:

```python
{
    'success': True / False,
    'message': 'Mensaje descriptivo',
    'emails_sent': ['email1@example.com', 'email2@example.com'],
    'order_number': 'OP-2024-001',
    'errors': []  # Solo si hubo errores parciales
}
```

---

## Integración con Celery

La tarea de Celery `enviar_enlace_pago_orden` ha sido refactorizada para usar estos casos de uso:

**Ubicación:** `apps/orden_pagos/tasks.py`

```python
from celery import shared_task
from apps.orden_pagos.application.use_cases import (
    SendPaymentLinkUseCase,
    GeneratePaymentOrderPDFUseCase
)


@shared_task
def enviar_enlace_pago_orden(order_id, base_url=None):
    repository = PaymentOrderRepository()
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    send_link_use_case = SendPaymentLinkUseCase(repository, pdf_generator)

    return send_link_use_case.execute(order_id, base_url)
```

**Uso:**

```python
# Desde una vista o servicio
from apps.orden_pagos.tasks import enviar_enlace_pago_orden

# Ejecutar de forma asíncrona
result = enviar_enlace_pago_orden.delay(order_id=123)

# Ejecutar de forma síncrona (para testing o debugging)
result = enviar_enlace_pago_orden(order_id=123)
```

---

## Función Auxiliar (Retrocompatibilidad)

La función `generar_pdf_orden_pago` se mantiene como wrapper para compatibilidad:

```python
def generar_pdf_orden_pago(payment_order, base_url=None):
    """
    Wrapper para compatibilidad con código existente.
    Internamente usa GeneratePaymentOrderPDFUseCase.
    """
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    return pdf_generator.execute(payment_order, base_url)
```

---

## Ventajas de esta Arquitectura

### 1. Separación de Responsabilidades

- **GeneratePaymentOrderPDFUseCase:** Solo genera PDFs
- **SendPaymentLinkUseCase:** Solo envía enlaces de pago

### 2. Reutilización

Los casos de uso pueden ser utilizados desde:

- Tareas de Celery
- Vistas de Django/DRF
- Comandos de gestión
- Scripts de administración
- Tests unitarios

### 3. Testabilidad

Cada caso de uso puede ser testeado independientemente:

```python
def test_generate_pdf():
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    pdf_content = pdf_generator.execute(payment_order)
    assert pdf_content is not None
    assert len(pdf_content) > 0


def test_send_payment_link():
    repository = MockRepository()
    pdf_generator = MockPDFGenerator()
    use_case = SendPaymentLinkUseCase(repository, pdf_generator)

    result = use_case.execute(order_id=1)
    assert result['success'] is True
```

### 4. Mantenibilidad

- Lógica concentrada en un solo lugar
- Fácil de modificar sin afectar otros componentes
- Documentación clara de responsabilidades

### 5. Flexibilidad

- Parámetros configurables
- Fácil de extender con nuevas funcionalidades
- Permite diferentes implementaciones

---

## Ejemplos de Uso Avanzado

### Generar PDF para descarga directa en una vista

```python
from django.http import HttpResponse
from apps.orden_pagos.application.use_cases import GeneratePaymentOrderPDFUseCase
from apps.orden_pagos.infrastructure.repository.payment_order_repository import (
    PaymentOrderRepository
)


def download_payment_order_pdf(request, order_id):
    # Obtener la orden
    repository = PaymentOrderRepository()
    payment_order = repository.get_by_id(order_id)

    if not payment_order:
        return HttpResponse('Orden no encontrada', status=404)

    # Generar PDF
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    pdf_content = pdf_generator.execute(payment_order)

    # Retornar como descarga
    response = HttpResponse(pdf_content, content_type='application/pdf')
    filename = f'orden_{payment_order.order_number}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
```

### Enviar enlace desde una vista de DRF

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class PaymentOrderViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=['post'])
    def send_payment_link(self, request, pk=None):
        """Enviar enlace de pago al estudiante y asesor."""
        try:
            repository = PaymentOrderRepository()
            pdf_generator = GeneratePaymentOrderPDFUseCase()
            use_case = SendPaymentLinkUseCase(repository, pdf_generator)

            result = use_case.execute(order_id=pk)

            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

### Generar múltiples PDFs en batch

```python
def generate_batch_pdfs(order_ids):
    """Genera PDFs para múltiples órdenes."""
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    repository = PaymentOrderRepository()

    results = []
    for order_id in order_ids:
        payment_order = repository.get_by_id(order_id)
        if payment_order:
            pdf_content = pdf_generator.execute(payment_order)
            results.append({
                'order_id': order_id,
                'order_number': payment_order.order_number,
                'pdf_size': len(pdf_content),
                'success': True
            })
        else:
            results.append({
                'order_id': order_id,
                'success': False,
                'error': 'Orden no encontrada'
            })

    return results
```

---

## Migraciones y Compatibilidad

### Código anterior (deprecated pero funcional)

```python
# Esto sigue funcionando por retrocompatibilidad
from apps.orden_pagos.tasks import generar_pdf_orden_pago

pdf = generar_pdf_orden_pago(payment_order)
```

### Código nuevo (recomendado)

```python
# Usar directamente el caso de uso
from apps.orden_pagos.application.use_cases import GeneratePaymentOrderPDFUseCase

pdf_generator = GeneratePaymentOrderPDFUseCase()
pdf = pdf_generator.execute(payment_order)
```

---

## Notas Importantes

1. **Validaciones:** El caso de uso `SendPaymentLinkUseCase` valida que la orden esté en estado PENDING antes de enviar.

2. **Transacciones:** El envío de correos no está en una transacción de base de datos. Si falla el envío a un
   destinatario, se intenta enviar al otro.

3. **Logging:** Todos los casos de uso incluyen logging detallado para facilitar el debugging.

4. **Errores:** Los errores se manejan de forma granular, retornando información detallada sobre qué salió bien y qué
   falló.

5. **Configuración:** El enlace de pago actualmente apunta a
   `https://www.lcmundo.com/pago-online/orden/{numero}/pagar/`. Ajustar según necesidad.

---

## TODO / Mejoras Futuras

- [ ] Implementar plantillas de correo más dinámicas
- [ ] Agregar soporte para múltiples idiomas en correos
- [ ] Implementar cola de reintento para correos fallidos
- [ ] Agregar métricas y monitoreo de envíos
- [ ] Crear tests unitarios completos
- [ ] Implementar cache para PDFs generados frecuentemente
- [ ] Agregar webhooks para notificar estado de envío

