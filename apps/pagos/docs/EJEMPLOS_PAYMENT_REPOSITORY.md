# Ejemplos Prácticos: Payment Repository

Este archivo contiene ejemplos completos y listos para usar del `PaymentRepository`.

## Configuración Inicial

```python
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.billing.models import Invoice
from apps.administrador.models import Usuarios

# Instanciar repositorio
repo = PaymentRepository()
```

## Ejemplo 1: Crear un Pago Simple

```python
def create_simple_payment(invoice_id, user_id, amount):
    """Crear un pago básico por transferencia bancaria"""

    payment_data = {
        'invoice_id': invoice_id,
        'user_id': user_id,
        'amount': Decimal(str(amount)),
        'currency': 'USD',
        'payment_method': 'BT',  # Bank Transfer
        'payment_reference_number': 'TRANS-2026-001',
        'payer_name': 'Juan Pérez',
        'status': 'P',  # Pendiente por verificar
    }

    payment = repo.create(payment_data)
    print(f"✓ Pago creado: {payment.payment_number}")
    print(f"  Monto: ${payment.amount}")
    print(f"  Estado: {payment.get_status_display()}")

    return payment


# Uso
payment = create_simple_payment(
    invoice_id=123,
    user_id=456,
    amount=500.00
)
```

## Ejemplo 2: Crear Pago con Asignaciones

```python
def create_payment_with_allocations(invoice_id, user_id, total_amount, concepts):
    """
    Crear un pago con distribución detallada por conceptos.
    
    Args:
        invoice_id: ID de la factura
        user_id: ID del usuario
        total_amount: Monto total del pago
        concepts: Lista de tuplas (invoice_detail_id, concept_id, amount)
    """

    payment_data = {
        'invoice_id': invoice_id,
        'user_id': user_id,
        'amount': Decimal(str(total_amount)),
        'currency': 'USD',
        'payment_method': 'BT',
        'payment_reference_number': f'TRANS-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
        'payer_name': 'María González',
        'status': 'D',  # Disponible
    }

    # Preparar asignaciones
    allocations = []
    for detail_id, concept_id, amount in concepts:
        allocations.append({
            'invoice_detail_id': detail_id,
            'concept_id': concept_id,
            'amount_applied': Decimal(str(amount)),
            'status': 'PAID'
        })

    payment = repo.create(payment_data, allocations)

    print(f"✓ Pago creado: {payment.payment_number}")
    print(f"  Total: ${payment.amount}")
    print(f"  Asignaciones: {len(allocations)}")
    for alloc in payment.allocations.all():
        print(f"    - Concepto {alloc.concept_id}: ${alloc.amount_applied}")

    return payment


# Uso
payment = create_payment_with_allocations(
    invoice_id=123,
    user_id=456,
    total_amount=1000.00,
    concepts=[
        (1, 10, 600.00),  # (invoice_detail_id, concept_id, amount)
        (2, 11, 400.00),
    ]
)
```

## Ejemplo 3: Verificar Pago por Tesorería

```python
def verify_payment_by_treasury(payment_id, verification_date=None):
    """
    Verificar un pago después de revisar el comprobante.
    
    Args:
        payment_id: ID del pago
        verification_date: Fecha de verificación (opcional, por defecto hoy)
    """

    # Obtener pago actual
    payment = repo.get_by_id(payment_id)

    if not payment:
        print(f"❌ Pago {payment_id} no encontrado")
        return None

    print(f"Verificando pago: {payment.payment_number}")
    print(f"  Estado actual: {payment.get_status_display()}")
    print(f"  Monto: ${payment.amount}")

    try:
        # Verificar
        verified_payment = repo.verify(payment_id, verification_date)

        print(f"✓ Pago verificado exitosamente")
        print(f"  Nuevo estado: {verified_payment.get_status_display()}")
        print(f"  Fecha verificación: {verified_payment.verification_date}")

        return verified_payment

    except ValueError as e:
        print(f"❌ Error: {e}")
        return None


# Uso
verify_payment_by_treasury(payment_id=123)

# Con fecha específica
verify_payment_by_treasury(
    payment_id=123,
    verification_date=date(2026, 1, 12)
)
```

## Ejemplo 4: Rechazar un Pago

```python
def reject_payment_with_reason(payment_id, reason="Comprobante inválido"):
    """
    Rechazar un pago con motivo.
    
    Args:
        payment_id: ID del pago
        reason: Motivo del rechazo
    """

    payment = repo.get_by_id(payment_id)

    if not payment:
        print(f"❌ Pago no encontrado")
        return None

    print(f"Rechazando pago: {payment.payment_number}")
    print(f"  Motivo: {reason}")

    try:
        rejected_payment = repo.reject(payment_id)

        print(f"✓ Pago rechazado")
        print(f"  Estado: {rejected_payment.get_status_display()}")

        # Opcional: Notificar al usuario (implementar en otro servicio)
        # send_payment_rejection_notification(rejected_payment, reason)

        return rejected_payment

    except ValueError as e:
        print(f"❌ Error: {e}")
        return None


# Uso
reject_payment_with_reason(
    payment_id=123,
    reason="El comprobante no corresponde al monto declarado"
)
```

## Ejemplo 5: Listar Pagos con Filtros

```python
def get_pending_payments_report(start_date, end_date):
    """
    Generar reporte de pagos pendientes en un período.
    
    Args:
        start_date: Fecha inicio
        end_date: Fecha fin
    """

    filters = {
        'status': 'P',  # Pendientes
        'start_date': start_date,
        'end_date': end_date
    }

    payments = repo.list_all(filters)

    print(f"=== PAGOS PENDIENTES ({start_date} - {end_date}) ===")
    print(f"Total: {payments.count()}\n")

    total_amount = Decimal('0.00')

    for payment in payments:
        print(f"{payment.payment_number}")
        print(f"  Estudiante: {payment.user_name}")
        print(f"  Factura: {payment.invoice.invoice_number}")
        print(f"  Monto: ${payment.amount} {payment.currency}")
        print(f"  Fecha: {payment.payment_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Método: {payment.get_payment_method_display()}")
        if payment.payment_reference_number:
            print(f"  Referencia: {payment.payment_reference_number}")
        print()

        total_amount += payment.amount

    print(f"TOTAL PENDIENTE: ${total_amount}")

    return payments


# Uso
today = date.today()
last_week = today - timedelta(days=7)

get_pending_payments_report(
    start_date=last_week,
    end_date=today
)
```

## Ejemplo 6: Buscar Pagos de un Estudiante

```python
def get_student_payment_history(user_id):
    """
    Obtener historial completo de pagos de un estudiante.
    
    Args:
        user_id: ID del usuario/estudiante
    """

    payments = repo.get_payments_by_user(user_id)

    if not payments:
        print(f"No se encontraron pagos para el usuario {user_id}")
        return []

    print(f"=== HISTORIAL DE PAGOS ===")
    print(f"Usuario ID: {user_id}")
    print(f"Total pagos: {len(payments)}\n")

    total_paid = Decimal('0.00')
    total_pending = Decimal('0.00')

    for payment in payments:
        status_symbol = {
            'V': '✓',
            'P': '⏳',
            'D': '📋',
            'R': '❌',
            'X': '⚠'
        }.get(payment.status, '?')

        print(f"{status_symbol} {payment.payment_number}")
        print(f"   Fecha: {payment.payment_date.strftime('%Y-%m-%d')}")
        print(f"   Monto: ${payment.amount}")
        print(f"   Estado: {payment.get_status_display()}")
        print(f"   Factura: {payment.invoice.invoice_number if payment.invoice else 'N/A'}")
        print()

        if payment.status == 'V':
            total_paid += payment.amount
        elif payment.status == 'P':
            total_pending += payment.amount

    print(f"TOTAL VERIFICADO: ${total_paid}")
    print(f"TOTAL PENDIENTE: ${total_pending}")

    return payments


# Uso
get_student_payment_history(user_id=456)
```

## Ejemplo 7: Calcular Balance de Factura

```python
def calculate_invoice_balance(invoice_id):
    """
    Calcular el balance actual de una factura.
    
    Args:
        invoice_id: ID de la factura
    """

    # Obtener factura
    from apps.billing.models import Invoice
    try:
        invoice = Invoice.objects.get(pk=invoice_id)
    except Invoice.DoesNotExist:
        print(f"❌ Factura {invoice_id} no encontrada")
        return None

    # Calcular total pagado verificado
    total_paid = repo.calculate_total_payments_by_invoice(invoice_id)

    # Calcular balance pendiente
    balance = invoice.total - total_paid

    print(f"=== BALANCE DE FACTURA ===")
    print(f"Número: {invoice.invoice_number}")
    print(f"Estudiante: {invoice.user.nombre} {invoice.user.apellido}")
    print()
    print(f"Total factura: ${invoice.total}")
    print(f"Total pagado:  ${total_paid}")
    print(f"Balance:       ${balance}")
    print()

    if balance <= 0:
        print("✓ Factura completamente pagada")
    else:
        print(f"⚠ Pendiente de pago: ${balance}")

    # Listar pagos
    payments = repo.get_verified_payments_by_invoice(invoice_id)
    if payments:
        print(f"\nPagos verificados ({len(payments)}):")
        for payment in payments:
            print(f"  - {payment.payment_number}: ${payment.amount} ({payment.payment_date.strftime('%Y-%m-%d')})")

    return {
        'invoice': invoice,
        'total': invoice.total,
        'paid': total_paid,
        'balance': balance,
        'payments': payments
    }


# Uso
calculate_invoice_balance(invoice_id=123)
```

## Ejemplo 8: Anular un Pago con Validaciones

```python
def cancel_payment_with_validation(payment_id, user_id, reason):
    """
    Anular un pago con validaciones adicionales.
    
    Args:
        payment_id: ID del pago
        user_id: ID del usuario que anula (para auditoría)
        reason: Motivo de anulación
    """

    # Obtener pago
    payment = repo.get_by_id_with_relations(payment_id)

    if not payment:
        print(f"❌ Pago no encontrado")
        return False

    print(f"Solicitando anulación de pago: {payment.payment_number}")
    print(f"  Monto: ${payment.amount}")
    print(f"  Estado actual: {payment.get_status_display()}")
    print(f"  Motivo: {reason}")
    print()

    # Validaciones adicionales
    if payment.status == 'X':
        print("❌ El pago ya está anulado")
        return False

    if payment.status == 'V':
        print("⚠ ADVERTENCIA: El pago está verificado")
        confirm = input("¿Está seguro que desea anular? (si/no): ")
        if confirm.lower() != 'si':
            print("Operación cancelada")
            return False

    try:
        # Anular pago
        success = repo.cancel(payment_id)

        if success:
            print(f"✓ Pago anulado exitosamente")

            # Registrar en log de auditoría (implementar en otro servicio)
            # audit_log.record_payment_cancellation(
            #     payment_id=payment_id,
            #     cancelled_by=user_id,
            #     reason=reason
            # )

            return True
        else:
            print(f"❌ No se pudo anular el pago")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# Uso
cancel_payment_with_validation(
    payment_id=123,
    user_id=789,  # Usuario admin/tesorería
    reason="Pago duplicado"
)
```

## Ejemplo 9: Reporte de Pagos por Asesor

```python
def generate_advisor_payments_report(advisor_id, start_date, end_date):
    """
    Generar reporte de pagos gestionados por un asesor.
    
    Args:
        advisor_id: ID del asesor
        start_date: Fecha inicio
        end_date: Fecha fin
    """

    # Obtener todos los pagos del asesor
    all_payments = repo.get_payments_by_advisor(advisor_id)

    # Filtrar por fecha
    payments = [
        p for p in all_payments
        if start_date <= p.payment_date.date() <= end_date
    ]

    if not payments:
        print(f"No hay pagos para el período {start_date} - {end_date}")
        return None

    # Agrupar por estado
    by_status = {}
    totals_by_status = {}

    for payment in payments:
        status = payment.get_status_display()
        if status not in by_status:
            by_status[status] = []
            totals_by_status[status] = Decimal('0.00')

        by_status[status].append(payment)
        totals_by_status[status] += payment.amount

    print(f"=== REPORTE DE PAGOS POR ASESOR ===")
    print(f"Asesor ID: {advisor_id}")
    if payments:
        print(f"Asesor: {payments[0].advisor_name}")
    print(f"Período: {start_date} - {end_date}")
    print(f"Total pagos: {len(payments)}\n")

    for status, payment_list in by_status.items():
        print(f"\n{status}: {len(payment_list)} pago(s)")
        print(f"Total: ${totals_by_status[status]}")
        print("-" * 50)

        for payment in payment_list:
            print(f"  {payment.payment_number}")
            print(f"    Estudiante: {payment.user_name}")
            print(f"    Monto: ${payment.amount}")
            print(f"    Fecha: {payment.payment_date.strftime('%Y-%m-%d')}")

    print(f"\n{'=' * 50}")
    print(f"TOTAL GENERAL: ${sum(totals_by_status.values())}")

    return {
        'advisor_id': advisor_id,
        'period': (start_date, end_date),
        'total_payments': len(payments),
        'by_status': by_status,
        'totals_by_status': totals_by_status
    }


# Uso
from datetime import date, timedelta

today = date.today()
first_day_month = date(today.year, today.month, 1)

generate_advisor_payments_report(
    advisor_id=789,
    start_date=first_day_month,
    end_date=today
)
```

## Ejemplo 10: Buscar Pagos con Texto Libre

```python
def search_payments(search_term):
    """
    Buscar pagos por número, referencia, nombre del pagador, etc.
    
    Args:
        search_term: Término de búsqueda
    """

    filters = {
        'search': search_term
    }

    payments = repo.list_all(filters)

    print(f"=== BÚSQUEDA DE PAGOS ===")
    print(f"Término: '{search_term}'")
    print(f"Resultados: {payments.count()}\n")

    if payments.count() == 0:
        print("No se encontraron pagos")
        return []

    for payment in payments[:10]:  # Mostrar primeros 10
        print(f"📄 {payment.payment_number}")
        print(f"   Estudiante: {payment.user_name}")
        print(f"   Pagador: {payment.payer_name}")
        print(f"   Monto: ${payment.amount}")
        print(f"   Estado: {payment.get_status_display()}")
        if payment.payment_reference_number:
            print(f"   Ref: {payment.payment_reference_number}")
        print()

    if payments.count() > 10:
        print(f"... y {payments.count() - 10} más")

    return payments


# Uso
search_payments("Juan")
search_payments("PAY-2026")
search_payments("TRANS-001")
```

## Notas de Uso

### Manejo de Errores

Todos los métodos pueden lanzar excepciones. Siempre envuelve las llamadas en try-except:

```python
try:
    payment = repo.create(payment_data)
except ValueError as e:
    # Error de validación
    print(f"Error de validación: {e}")
except Exception as e:
    # Otro error
    print(f"Error inesperado: {e}")
```

### Transacciones

Los métodos `create`, `update`, `cancel`, `verify`, y `reject` ya usan transacciones atómicas internamente.

### Performance

Para listados grandes, considera paginar los resultados:

```python
payments = repo.list_all(filters)
paginated = payments[0:50]  # Primeros 50
```

### Type Hints

El repositorio usa type hints. Aprovecha la validación de tu IDE:

```python
from typing import List
from apps.pagos.models import Payment

payments: List[Payment] = repo.get_payments_by_user(123)
```

