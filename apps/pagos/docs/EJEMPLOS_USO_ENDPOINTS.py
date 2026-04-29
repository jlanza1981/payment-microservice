"""
Ejemplos Prácticos de Uso: CreatePaymentUseCase

Este archivo contiene 5 ejemplos completos de uso del caso de uso CreatePayment
con diferentes escenarios del mundo real.

Author: Sistema LC Mundo
Date: 2026-01-12
"""

from decimal import Decimal

from django.utils import timezone

from apps.administrador.models import Usuarios
from apps.billing.models import Invoice, InvoiceDetail
from apps.orden_pagos.models import PaymentOrder, PaymentOrderDetails, PaymentConcept
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePaymentUseCase
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository


# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

def setup_use_case():
    """Inicializa el caso de uso con su repositorio."""
    repository = PaymentRepository()
    use_case = CreatePaymentUseCase(repository)
    return use_case


# ============================================================================
# EJEMPLO 1: PAGO EXONERADO COMPLETO
# ============================================================================

def ejemplo_1_pago_exonerado_completo():
    """
    Escenario: Estudiante con beca completa (exonerado del pago)

    Flujo:
    1. Crear orden de pago exonerada
    2. Generar factura
    3. Crear pago exonerado automático

    Resultado:
    - Orden: status='EXONERATED'
    - Factura: status='P' (Pagada)
    - Pago: status='V' (Verificado), method='EX'
    """
    print("=" * 60)
    print("EJEMPLO 1: PAGO EXONERADO COMPLETO")
    print("=" * 60)

    # Obtener datos
    student = Usuarios.objects.get(id=1)  # Ajustar ID
    advisor = Usuarios.objects.get(id=2)  # Ajustar ID
    concept_matricula = PaymentConcept.objects.get(name='Matrícula')

    # 1. Crear orden exonerada
    order = PaymentOrder.objects.create(
        student=student,
        advisor=advisor,
        status='EXONERATED',
        allows_partial_payment=False,
        total_order=Decimal('1500.00')
    )
    print(f"✓ Orden creada: {order.order_number}")

    # 2. Agregar detalles a la orden
    order_detail = PaymentOrderDetails.objects.create(
        payment_order=order,
        payment_concept=concept_matricula,
        description='Matrícula curso intensivo',
        quantity=1,
        unit_price=Decimal('1500.00'),
        discount=Decimal('0.00')
    )
    print(f"✓ Detalle agregado: {order_detail.description}")

    # 3. Crear factura
    invoice = Invoice.objects.create(
        user=student,
        advisor=advisor,
        payment_order=order,
        status='E',  # Exonerada
        subtotal=Decimal('1500.00'),
        taxes=Decimal('0.00'),
        total=Decimal('1500.00'),
        balance_due=Decimal('1500.00'),
        currency='USD'
    )
    print(f"✓ Factura creada: {invoice.invoice_number}")

    # 4. Crear detalle de factura
    invoice_detail = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_matricula,
        description='Matrícula curso intensivo',
        quantity=1,
        unit_price=Decimal('1500.00'),
        discount=Decimal('0.00')
    )
    print(f"✓ Detalle de factura creado")

    # 5. Crear pago exonerado usando el caso de uso
    use_case = setup_use_case()

    payment = use_case.create_exonerated_payment(
        invoice=invoice,
        user=student,
        advisor=advisor,
        amount=Decimal('1500.00'),
        currency='USD',
        notes='Estudiante con beca completa'
    )

    print(f"✓ Pago exonerado creado: {payment.payment_number}")
    print(f"  - Método: {payment.get_payment_method_display()}")
    print(f"  - Estado: {payment.get_status_display()}")
    print(f"  - Monto: ${payment.amount}")

    # 6. Verificar resultados
    invoice.refresh_from_db()
    print(f"\n✓ Balance de factura: ${invoice.balance_due}")
    print(f"✓ Estado de factura: {invoice.get_status_display()}")

    return {
        'order': order,
        'invoice': invoice,
        'payment': payment
    }


# ============================================================================
# EJEMPLO 2: PAGO ANTICIPADO POR PAYPAL
# ============================================================================

def ejemplo_2_pago_anticipado_paypal():
    """
    Escenario: Estudiante paga por PayPal antes de generar la factura

    Flujo:
    1. Estudiante realiza pago por PayPal
    2. Sistema registra pago sin factura
    3. Más tarde se genera la factura
    4. Se asocia la factura al pago

    Resultado:
    - Pago: invoice=None → invoice=FAC-00001
    - Factura: balance_due actualizado
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 2: PAGO ANTICIPADO POR PAYPAL")
    print("=" * 60)

    # Obtener datos
    student = Usuarios.objects.get(id=1)
    advisor = Usuarios.objects.get(id=2)
    concept_mensualidad = PaymentConcept.objects.get(name='Mensualidad')

    # PASO 1: Simular respuesta de PayPal
    paypal_response = {
        'id': 'PAYPAL-TXN-987654321',
        'status': 'COMPLETED',
        'amount': {
            'total': '500.00',
            'currency': 'USD'
        },
        'payer': {
            'payer_info': {
                'email': 'estudiante@example.com',
                'first_name': 'Juan',
                'last_name': 'Pérez'
            }
        }
    }
    print(f"✓ Pago recibido de PayPal: {paypal_response['id']}")

    # PASO 2: Registrar pago sin factura
    use_case = setup_use_case()

    payment = use_case.create_advance_payment(
        user=student,
        advisor=advisor,
        amount=Decimal(paypal_response['amount']['total']),
        payment_method='PP',
        payment_reference_number=paypal_response['id'],
        currency=paypal_response['amount']['currency'],
        status='D'  # Disponible (PayPal ya verificó)
    )

    print(f"✓ Pago anticipado registrado: {payment.payment_number}")
    print(f"  - Factura: {payment.invoice}")  # None
    print(f"  - Monto: ${payment.amount}")
    print(f"  - Estado: {payment.get_status_display()}")

    # PASO 3: Más tarde, crear orden y factura
    print("\n--- Generando factura (tiempo después) ---")

    order = PaymentOrder.objects.create(
        student=student,
        advisor=advisor,
        status='ACTIVE',
        allows_partial_payment=True,
        total_order=Decimal('500.00')
    )
    print(f"✓ Orden creada: {order.order_number}")

    invoice = Invoice.objects.create(
        user=student,
        advisor=advisor,
        payment_order=order,
        status='I',  # Emitida
        subtotal=Decimal('500.00'),
        total=Decimal('500.00'),
        balance_due=Decimal('500.00'),
        currency='USD'
    )
    print(f"✓ Factura creada: {invoice.invoice_number}")

    invoice_detail = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_mensualidad,
        description='Mensualidad - Enero',
        quantity=1,
        unit_price=Decimal('500.00')
    )

    # PASO 4: Asociar factura al pago
    allocations = [
        {
            'invoice_detail_id': invoice_detail.id,
            'payment_concept_id': concept_mensualidad.id,
            'amount_applied': Decimal('500.00'),
            'status': 'PAID'
        }
    ]

    updated_payment = use_case.associate_invoice_to_payment(
        payment_id=payment.id,
        invoice_id=invoice.id,
        allocations=allocations
    )

    print(f"✓ Factura asociada al pago")
    print(f"  - Pago: {updated_payment.payment_number}")
    print(f"  - Factura: {updated_payment.invoice.invoice_number}")

    # Verificar resultados
    invoice.refresh_from_db()
    print(f"\n✓ Balance de factura: ${invoice.balance_due}")
    print(f"✓ Estado de factura: {invoice.get_status_display()}")

    return {
        'order': order,
        'invoice': invoice,
        'payment': updated_payment
    }


# ============================================================================
# EJEMPLO 3: PAGO PARCIAL CON MÚLTIPLES ALLOCATIONS
# ============================================================================

def ejemplo_3_pago_parcial_multiple_allocations():
    """
    Escenario: Estudiante paga parcialmente una factura con múltiples conceptos

    Flujo:
    1. Factura con 3 conceptos (Matrícula, Mensualidad, Material)
    2. Estudiante paga solo $800 de $1500 total
    3. Se asigna el pago a diferentes conceptos

    Resultado:
    - Pago parcial aplicado
    - Balance de factura actualizado
    - Allocations creados
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 3: PAGO PARCIAL CON MÚLTIPLES ALLOCATIONS")
    print("=" * 60)

    # Obtener datos
    student = Usuarios.objects.get(id=1)
    advisor = Usuarios.objects.get(id=2)

    concept_matricula = PaymentConcept.objects.get(name='Matrícula')
    concept_mensualidad = PaymentConcept.objects.get(name='Mensualidad')
    concept_material = PaymentConcept.objects.get(name='Material Didáctico')

    # 1. Crear orden y factura con múltiples conceptos
    order = PaymentOrder.objects.create(
        student=student,
        advisor=advisor,
        status='ACTIVE',
        allows_partial_payment=True,
        total_order=Decimal('1500.00')
    )

    invoice = Invoice.objects.create(
        user=student,
        advisor=advisor,
        payment_order=order,
        status='I',
        subtotal=Decimal('1500.00'),
        total=Decimal('1500.00'),
        balance_due=Decimal('1500.00'),
        currency='USD'
    )

    # Crear múltiples detalles
    detail_matricula = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_matricula,
        description='Matrícula',
        quantity=1,
        unit_price=Decimal('800.00')
    )

    detail_mensualidad = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_mensualidad,
        description='Mensualidad - Enero',
        quantity=1,
        unit_price=Decimal('500.00')
    )

    detail_material = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_material,
        description='Libros y material',
        quantity=1,
        unit_price=Decimal('200.00')
    )

    print(f"✓ Factura creada: {invoice.invoice_number}")
    print(f"  - Matrícula: $800")
    print(f"  - Mensualidad: $500")
    print(f"  - Material: $200")
    print(f"  - TOTAL: ${invoice.total}")

    # 2. Estudiante paga parcialmente $800
    print(f"\n--- Estudiante paga $800 de ${invoice.total} ---")

    allocations = [
        {
            'invoice_detail_id': detail_matricula.id,
            'payment_concept_id': concept_matricula.id,
            'amount_applied': Decimal('500.00'),  # Pago parcial de matrícula
            'status': 'PAID'
        },
        {
            'invoice_detail_id': detail_mensualidad.id,
            'payment_concept_id': concept_mensualidad.id,
            'amount_applied': Decimal('300.00'),  # Pago parcial de mensualidad
            'status': 'PAID'
        }
    ]

    use_case = setup_use_case()

    payment = use_case.execute(
        payment_data={
            'invoice': invoice,
            'user': student,
            'advisor': advisor,
            'amount': Decimal('800.00'),
            'payment_method': 'ST',  # Stripe
            'payment_reference_number': 'ch_stripe_123456',
            'currency': 'USD',
            'status': 'D'
        },
        allocations=allocations
    )

    print(f"✓ Pago parcial registrado: {payment.payment_number}")
    print(f"  - Monto pagado: ${payment.amount}")

    # Verificar allocations
    print(f"\n✓ Asignaciones creadas:")
    for alloc in payment.allocations.all():
        print(f"  - {alloc.payment_concept.name}: ${alloc.amount_applied}")

    # Verificar balance
    invoice.refresh_from_db()
    print(f"\n✓ Balance de factura: ${invoice.balance_due}")
    print(f"  (Restante: ${invoice.total - payment.amount})")
    print(f"✓ Estado: {invoice.get_status_display()}")

    return {
        'order': order,
        'invoice': invoice,
        'payment': payment
    }


# ============================================================================
# EJEMPLO 4: PAGO POR TRANSFERENCIA BANCARIA (PENDIENTE VERIFICACIÓN)
# ============================================================================

def ejemplo_4_transferencia_bancaria_pendiente():
    """
    Escenario: Estudiante paga por transferencia bancaria

    Flujo:
    1. Estudiante realiza transferencia
    2. Sistema registra pago como pendiente ('P')
    3. Tesorería verifica el pago
    4. Estado cambia a verificado ('V')

    Resultado:
    - Pago: status='P' → status='V'
    - Factura actualizada después de verificación
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 4: TRANSFERENCIA BANCARIA (PENDIENTE → VERIFICADO)")
    print("=" * 60)

    # Obtener datos
    student = Usuarios.objects.get(id=1)
    advisor = Usuarios.objects.get(id=2)
    concept_matricula = PaymentConcept.objects.get(name='Matrícula')

    # 1. Crear orden y factura
    order = PaymentOrder.objects.create(
        student=student,
        advisor=advisor,
        status='PENDING',
        total_order=Decimal('1000.00')
    )

    invoice = Invoice.objects.create(
        user=student,
        advisor=advisor,
        payment_order=order,
        status='I',
        subtotal=Decimal('1000.00'),
        total=Decimal('1000.00'),
        balance_due=Decimal('1000.00'),
        currency='USD'
    )

    invoice_detail = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_matricula,
        description='Matrícula',
        quantity=1,
        unit_price=Decimal('1000.00')
    )

    print(f"✓ Factura creada: {invoice.invoice_number}")

    # 2. Registrar pago pendiente
    print(f"\n--- Estudiante envía comprobante de transferencia ---")

    use_case = setup_use_case()
    repository = PaymentRepository()

    payment = use_case.execute(
        payment_data={
            'invoice': invoice,
            'user': student,
            'advisor': advisor,
            'amount': Decimal('1000.00'),
            'payment_method': 'BT',  # Bank Transfer
            'payment_reference_number': 'TRANSFER-2026-001',
            'currency': 'USD',
            'status': 'P'  # Pendiente verificación
        },
        allocations=[
            {
                'invoice_detail_id': invoice_detail.id,
                'payment_concept_id': concept_matricula.id,
                'amount_applied': Decimal('1000.00'),
                'status': 'PENDING'
            }
        ]
    )

    print(f"✓ Pago registrado como pendiente: {payment.payment_number}")
    print(f"  - Estado: {payment.get_status_display()}")
    print(f"  - Referencia: {payment.payment_reference_number}")

    # 3. Tesorería verifica el pago
    print(f"\n--- Tesorería verifica la transferencia ---")

    verified_payment = repository.verify(
        payment_id=payment.id,
        verification_date=timezone.now().date()
    )

    print(f"✓ Pago verificado: {verified_payment.payment_number}")
    print(f"  - Estado: {verified_payment.get_status_display()}")
    print(f"  - Fecha verificación: {verified_payment.verification_date}")

    # Verificar actualización de factura
    invoice.refresh_from_db()
    print(f"\n✓ Balance de factura: ${invoice.balance_due}")
    print(f"✓ Estado de factura: {invoice.get_status_display()}")

    return {
        'order': order,
        'invoice': invoice,
        'payment': verified_payment
    }


# ============================================================================
# EJEMPLO 5: PAGO ANTICIPADO CON STRIPE Y WEBHOOK
# ============================================================================

def ejemplo_5_stripe_webhook_flow():
    """
    Escenario: Pago procesado por Stripe con webhook

    Flujo:
    1. Stripe procesa el pago (webhook)
    2. Sistema registra pago sin factura
    3. Factura se genera en proceso batch nocturno
    4. Sistema asocia automáticamente

    Resultado:
    - Integración completa con gateway de pago
    - Pago anticipado → Factura asociada
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 5: STRIPE WEBHOOK FLOW")
    print("=" * 60)

    # Obtener datos
    student = Usuarios.objects.get(id=1)
    advisor = Usuarios.objects.get(id=2)
    concept_mensualidad = PaymentConcept.objects.get(name='Mensualidad')

    # PASO 1: Simular webhook de Stripe
    stripe_event = {
        'id': 'evt_stripe_123',
        'type': 'charge.succeeded',
        'data': {
            'object': {
                'id': 'ch_stripe_456',
                'amount': 75000,  # Centavos (= $750.00)
                'currency': 'usd',
                'status': 'succeeded',
                'customer': 'cus_stripe_789',
                'metadata': {
                    'student_id': str(student.id),
                    'advisor_id': str(advisor.id)
                }
            }
        }
    }

    print(f"✓ Webhook recibido de Stripe")
    print(f"  - Event ID: {stripe_event['id']}")
    print(f"  - Charge ID: {stripe_event['data']['object']['id']}")
    print(f"  - Amount: ${stripe_event['data']['object']['amount'] / 100}")

    # PASO 2: Registrar pago anticipado
    use_case = setup_use_case()

    amount = Decimal(str(stripe_event['data']['object']['amount'] / 100))

    payment = use_case.create_advance_payment(
        user=student,
        advisor=advisor,
        amount=amount,
        payment_method='ST',
        payment_reference_number=stripe_event['data']['object']['id'],
        currency='USD',
        status='D'  # Disponible (Stripe ya confirmó)
    )

    print(f"\n✓ Pago anticipado registrado: {payment.payment_number}")
    print(f"  - Factura: {payment.invoice}")  # None
    print(f"  - Monto: ${payment.amount}")

    # PASO 3: Simular generación de factura en batch nocturno
    print(f"\n--- Proceso batch nocturno generando facturas ---")

    order = PaymentOrder.objects.create(
        student=student,
        advisor=advisor,
        status='ACTIVE',
        total_order=amount
    )

    invoice = Invoice.objects.create(
        user=student,
        advisor=advisor,
        payment_order=order,
        status='I',
        subtotal=amount,
        total=amount,
        balance_due=amount,
        currency='USD'
    )

    invoice_detail = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_concept=concept_mensualidad,
        description='Mensualidad - Febrero',
        quantity=1,
        unit_price=amount
    )

    print(f"✓ Factura generada: {invoice.invoice_number}")

    # PASO 4: Asociar automáticamente
    allocations = [
        {
            'invoice_detail_id': invoice_detail.id,
            'payment_concept_id': concept_mensualidad.id,
            'amount_applied': amount,
            'status': 'PAID'
        }
    ]

    updated_payment = use_case.associate_invoice_to_payment(
        payment_id=payment.id,
        invoice_id=invoice.id,
        allocations=allocations
    )

    print(f"✓ Pago asociado automáticamente a factura")
    print(f"  - Pago: {updated_payment.payment_number}")
    print(f"  - Factura: {updated_payment.invoice.invoice_number}")

    # Verificar
    invoice.refresh_from_db()
    print(f"\n✓ Balance: ${invoice.balance_due}")
    print(f"✓ Estado: {invoice.get_status_display()}")

    return {
        'order': order,
        'invoice': invoice,
        'payment': updated_payment
    }


# ============================================================================
# EJECUTAR TODOS LOS EJEMPLOS
# ============================================================================

def run_all_examples():
    """Ejecuta todos los ejemplos en secuencia."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "EJEMPLOS DE USO: CreatePaymentUseCase" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Ejemplo 1
        result1 = ejemplo_1_pago_exonerado_completo()

        # Ejemplo 2
        result2 = ejemplo_2_pago_anticipado_paypal()

        # Ejemplo 3
        result3 = ejemplo_3_pago_parcial_multiple_allocations()

        # Ejemplo 4
        result4 = ejemplo_4_transferencia_bancaria_pendiente()

        # Ejemplo 5
        result5 = ejemplo_5_stripe_webhook_flow()

        print("\n" + "=" * 60)
        print("✓ TODOS LOS EJEMPLOS EJECUTADOS EXITOSAMENTE")
        print("=" * 60)

        return {
            'ejemplo_1': result1,
            'ejemplo_2': result2,
            'ejemplo_3': result3,
            'ejemplo_4': result4,
            'ejemplo_5': result5
        }

    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == '__main__':
    """
    Para ejecutar estos ejemplos:
    
    1. Desde Django shell:
       python manage.py shell
       >>> from apps.pagos.docs.EJEMPLOS_USO_ENDPOINTS import *
       >>> run_all_examples()
    
    2. Ejecutar ejemplo específico:
       >>> ejemplo_1_pago_exonerado_completo()
       >>> ejemplo_2_pago_anticipado_paypal()
       >>> etc.
    """
    print(__doc__)
    print("\nPara ejecutar los ejemplos, importa este módulo en Django shell.")
