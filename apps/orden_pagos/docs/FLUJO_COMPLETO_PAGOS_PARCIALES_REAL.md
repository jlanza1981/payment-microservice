# 🎯 Flujo COMPLETO: Pagos Parciales - Arquitectura Real

## 📋 **Flujo Correcto según tu Código**

```
1. Crear PaymentOrder (PENDING)
   ↓
2. Enviar PDF de orden al estudiante por email
   ↓
3. Estudiante paga en PayPal → ✅ PAGO EXITOSO
   ↓
4. Webhook de PayPal notifica al backend
   ↓
5. Backend activa orden (PENDING → ACTIVE)
   ↓
6. Backend crea Invoice + InvoiceDetail
   ↓
7. Backend crea InvoiceCreditDetail (registra el pago)
   ↓
8. Backend crea PaymentReceipt
   ↓
9. Backend genera PDF del recibo
   ↓
10. Backend envía recibo por email al estudiante
```

---

## 🔄 **Paso a Paso Detallado**

### **PASO 1: Crear PaymentOrder (PENDING)**

```python
# apps/orden_pagos/use_cases/create_payment_order.py
from decimal import Decimal

order = PaymentOrder.objects.create(
    order_number='PO-2026-000025',  # Auto-generado
    student_id=123,
    advisor_id=456,
    opportunity_id=789,
    currency='CAD',
    total_order=Decimal('2608.00'),
    allows_partial_payment=True,  # ⬅️ Habilita pagos parciales
    minimum_payment_amount=Decimal('50.00'),  # ⬅️ Mínimo por abono
    initial_payment_amount=Decimal('1000.00'),  # ⬅️ Sugerido para PDF
    status='PENDING'  # ⬅️ Esperando pago
)

# Crear detalles
PaymentOrderDetails.objects.create(
    payment_order=order,
    payment_concept_id=1,  # Inscripción
    amount=Decimal('150.00'),
    quantity=1
)

PaymentOrderDetails.objects.create(
    payment_order=order,
    payment_concept_id=2,  # Matrícula
    amount=Decimal('120.00'),
    quantity=4  # 4 semanas
)
```

**Estado BD**:
```sql
payment_order:
  order_number='PO-2026-000025'
  status='PENDING'
  total_order=2608.00
  allows_partial_payment=true
  minimum_payment_amount=50.00
  initial_payment_amount=1000.00
```

---

### **PASO 2: Enviar PDF de Orden al Estudiante**

```python
# apps/orden_pagos/use_cases/send_payment_notification.py

# Generar token para el link
order.generate_token_and_expiration_date(days_valid=7)

# Generar PDF de la orden
pdf_content, pdf_path = generate_payment_order_pdf(order)

# Enviar email con PDF adjunto
send_email(
    to=order.student.email,
    subject=f"Orden de Pago {order.order_number}",
    template='email_payment_order.html',
    context={'order': order},
    attachments=[
        ('orden_pago.pdf', pdf_content, 'application/pdf')
    ]
)
```

**Email enviado**:
```
Subject: Orden de Pago PO-2026-000025

Hola Johanna,

Tu orden de pago está lista.

Total: CAD 2,608.00
Monto a pagar (primer abono sugerido): CAD 1,000.00

Link de pago: https://app.lcmundo.com/payment/token123abc

Adjunto: orden_pago.pdf
```

**PDF muestra**:
```
╔════════════════════════════════╗
║  ORDEN N° PO-2026-000025      ║
║                                ║
║  Total: CAD 2,608.00          ║
║  Monto a Pagar: CAD 1,000.00  ║ ⬅️ initial_payment_amount
╚════════════════════════════════╝
```

---

### **PASO 3: Estudiante Paga en PayPal**

```javascript
// Frontend - Botón de PayPal
paypal.Buttons({
    createOrder: function(data, actions) {
        return actions.order.create({
            purchase_units: [{
                amount: {
                    value: '1000.00',  // Primer abono
                    currency_code: 'CAD'
                },
                reference_id: 'PO-2026-000025'
            }]
        });
    },
    onApprove: function(data, actions) {
        return actions.order.capture().then(function(details) {
            // PayPal captura el pago ✅
            console.log('Pago exitoso', details);
            
            // Redirigir al webhook o confirmar
            window.location.href = '/payment/success';
        });
    }
}).render('#paypal-button-container');
```

**PayPal captura**: $1,000 CAD ✅

---

### **PASO 4: Webhook de PayPal Notifica al Backend**

```python
# apps/pagos/views/paypal_webhook.py

@csrf_exempt
def paypal_webhook(request):
    """Webhook que recibe notificaciones de PayPal"""
    
    payload = json.loads(request.body)
    event_type = payload.get('event_type')
    
    if event_type == 'PAYMENT.CAPTURE.COMPLETED':
        # Extraer datos del pago
        order_id = payload['resource']['purchase_units'][0]['reference_id']
        amount = Decimal(payload['resource']['amount']['value'])
        transaction_id = payload['resource']['id']
        
        # Procesar el pago
        process_payment_from_webhook.delay(
            order_number=order_id,
            amount=amount,
            transaction_id=transaction_id,
            payment_method='PP',  # PayPal
            metadata=payload
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'ignored'})
```

---

### **PASO 5: Backend Activa la Orden**

```python
# apps/pagos/tasks.py

@shared_task
def process_payment_from_webhook(order_number, amount, transaction_id, payment_method, metadata):
    """
    Procesa un pago confirmado por el webhook de PayPal
    """
    from apps.orden_pagos.models import PaymentOrder
    from apps.billing.models import Invoice, InvoiceDetail, InvoiceCreditDetail, PaymentReceipt
    from apps.pagos.models import Payment
    
    try:
        # 1. Obtener la orden
        order = PaymentOrder.objects.get(order_number=order_number)
        
        # 2. Validar que puede recibir pagos
        if order.status not in ['PENDING', 'ACTIVE']:
            raise ValueError(f"Orden en estado {order.status} no puede recibir pagos")
        
        # 3. Validar monto mínimo
        if order.minimum_payment_amount and amount < order.minimum_payment_amount:
            raise ValueError(f"Monto {amount} menor al mínimo {order.minimum_payment_amount}")
        
        # 4. ACTIVAR orden si está en PENDING
        if order.status == 'PENDING':
            order.activate_for_payments()  # PENDING → ACTIVE ✅
        
        # Continúa en el siguiente paso...
        
    except Exception as e:
        logger.error(f"Error procesando pago: {str(e)}")
        raise
```

**Estado BD después de activar**:
```sql
payment_order:
  status='ACTIVE'  ⬅️ Cambió de PENDING a ACTIVE
```

---

### **PASO 6: Backend Crea Invoice (si no existe)**

```python
# Continuación del task...

with transaction.atomic():
    # 5. Verificar si ya existe Invoice para esta orden
    invoice = order.invoices_payment_order.first()
    
    if not invoice:
        # ⚠️ PRIMERA VEZ: Crear Invoice
        invoice = Invoice.objects.create(
            payment_order=order,
            user=order.student,
            advisor=order.advisor,
            subtotal=order.total_order,
            total=order.total_order,
            balance_due=order.total_order,  # Inicia con deuda completa
            currency=order.currency,
            status='B'  # Borrador
        )
        
        # Crear InvoiceDetail desde PaymentOrderDetails
        for order_detail in order.payment_order_details.all():
            InvoiceDetail.objects.create(
                invoice=invoice,
                payment_concept=order_detail.payment_concept,
                description=order_detail.payment_concept.description,
                quantity=order_detail.quantity,
                unit_price=order_detail.amount,
                discount=order_detail.discount_amount or Decimal('0.00'),
                discount_type=order_detail.discount_type,
                subtotal=order_detail.sub_total
            )
        
        logger.info(f"Invoice {invoice.invoice_number} creada para orden {order.order_number}")
```

**Estado BD**:
```sql
invoices:
  invoice_number='FAC-2026-000123'  ⬅️ Auto-generado
  payment_order_id=1
  user_id=123
  total=2608.00
  balance_due=2608.00
  status='B'  (Borrador)

invoice_details (2 registros):
  - description='Inscripción', unit_price=150.00, quantity=1, subtotal=150.00
  - description='Matrícula', unit_price=120.00, quantity=4, subtotal=480.00
```

---

### **PASO 7: Backend Registra el Pago en InvoiceCreditDetail**

```python
# Continuación del task...

    # 6. Crear registro del pago en Payment
    payment = Payment.objects.create(
        user=order.student,
        amount=amount,
        payment_method=payment_method,  # 'PP' para PayPal
        reference_number=transaction_id,
        payment_date=timezone.now(),
        currency=order.currency,
        status='D',  # Disponible/Verificado
        metadata=metadata  # Guardar datos completos de PayPal
    )
    
    # 7. Guardar balance anterior
    previous_balance = invoice.balance_due  # $2,608.00
    
    # 8. CREAR InvoiceCreditDetail (registra el abono)
    credit_detail = InvoiceCreditDetail.objects.create(
        invoice=invoice,
        amount=amount,  # $1,000.00
        credit_status='E',  # Emitido
        credit_balance=None  # NULL porque es pago directo, NO un crédito a favor
    )
    
    logger.info(f"Pago de {amount} registrado en InvoiceCreditDetail para factura {invoice.invoice_number}")
```

**Estado BD**:
```sql
payments:
  id=1, amount=1000.00, payment_method='PP', status='D'

invoice_credit_detail:
  id=1
  invoice_id=1
  amount=1000.00
  credit_status='E'  (Emitido)
  credit_balance=NULL  ⬅️ Pago directo, NO crédito a favor
```

---

### **PASO 8: Backend Crea PaymentReceipt**

```python
# Continuación del task...

    # 9. CREAR PaymentReceipt (recibo del abono)
    receipt = PaymentReceipt.objects.create(
        payment=payment,
        invoice=invoice,
        student=order.student,
        amount_paid=amount,  # $1,000.00
        previous_balance=previous_balance,  # $2,608.00
        new_balance=previous_balance - amount,  # $1,608.00
        payment_method=payment_method,
        payment_date=timezone.now(),
        currency=order.currency,
        notes=f"Pago recibido vía {payment_method} - Transaction ID: {transaction_id}"
    )
    
    # 10. Vincular recibo con el credit detail
    credit_detail.payment_receipt = receipt
    credit_detail.save()
    
    logger.info(f"Recibo {receipt.receipt_number} creado")
```

**Estado BD**:
```sql
payment_receipts:
  receipt_number='REC-2026-000001'  ⬅️ Auto-generado
  payment_id=1
  invoice_id=1
  student_id=123
  amount_paid=1000.00
  previous_balance=2608.00
  new_balance=1608.00  ⬅️ Calculado
  payment_method='PP'
```

---

### **PASO 9: Backend Actualiza Balance de Invoice**

```python
# Continuación del task...

    # 11. Actualizar balance de la factura
    invoice.update_balance()
    
    # Este método:
    # - Suma todos los InvoiceCreditDetail con credit_status='E'
    # - Calcula balance_due = total - total_pagado
    # - Actualiza status: 'PP' (Parcialmente Pagada) si 0 < balance < total
    # - Actualiza status: 'P' (Pagada) si balance = 0
    # - Marca orden como PAID si balance = 0
```

**Estado BD después de `update_balance()`**:
```sql
invoices:
  total=2608.00
  balance_due=1608.00  ⬅️ Actualizado (2608 - 1000)
  status='PP'  ⬅️ Parcialmente Pagada

payment_order:
  status='ACTIVE'  ⬅️ Sigue ACTIVE (aún hay saldo)
```

---

### **PASO 10: Backend Genera PDF del Recibo**

```python
# Continuación del task...

    # 12. Generar PDF del recibo de forma asíncrona
    receipt.generate_pdf()  # Llama a Celery task
```

**Task de Celery**:
```python
# apps/pagos/tasks.py

@shared_task
def generate_receipt_pdf_task(receipt_id):
    """Genera el PDF del recibo"""
    from apps.billing.models import PaymentReceipt
    from apps.orden_pagos.application.use_cases import GenerateReceiptPDFUseCase
    
    receipt = PaymentReceipt.objects.get(id=receipt_id)
    
    # Generar PDF
    pdf_content, pdf_path = GenerateReceiptPDFUseCase().execute(
        receipt=receipt,
        template_name='pdf_payment_receipt.html',
        css_filename='pdf_receipt.css'
    )
    
    # Guardar PDF en el modelo
    receipt.receipt_file.save(
        f'receipt_{receipt.receipt_number}.pdf',
        ContentFile(pdf_content),
        save=True
    )
    
    logger.info(f"PDF generado para recibo {receipt.receipt_number}")
```

**PDF del recibo**:
```
╔════════════════════════════════════════╗
║       RECIBO DE PAGO                  ║
║       REC-2026-000001                 ║
╠════════════════════════════════════════╣
║  Estudiante: Johanna Lanza            ║
║  Factura: FAC-2026-000123             ║
║  Orden: PO-2026-000025                ║
║                                       ║
║  Saldo Anterior: CAD 2,608.00         ║
║  Monto Pagado:   CAD 1,000.00         ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║  Nuevo Saldo:    CAD 1,608.00         ║
║                                       ║
║  Método: PayPal                       ║
║  Fecha: 11/02/2026                    ║
║  Ref: PAYPAL-123ABC                   ║
╚════════════════════════════════════════╝
```

---

### **PASO 11: Backend Envía Recibo por Email**

```python
# Continuación del task...

    # 13. Enviar recibo por email
    receipt.send_to_student_email()  # Llama a otro Celery task
```

**Task de Celery**:
```python
@shared_task
def send_receipt_email_task(receipt_id):
    """Envía el recibo por email al estudiante"""
    from apps.billing.models import PaymentReceipt
    
    receipt = PaymentReceipt.objects.get(id=receipt_id)
    
    # Enviar email con PDF adjunto
    send_email(
        to=receipt.student.email,
        subject=f"Recibo de Pago {receipt.receipt_number}",
        template='email_payment_receipt.html',
        context={
            'receipt': receipt,
            'student': receipt.student,
            'invoice': receipt.invoice,
            'order': receipt.invoice.payment_order
        },
        attachments=[
            (f'recibo_{receipt.receipt_number}.pdf', receipt.receipt_file.read(), 'application/pdf')
        ]
    )
    
    # Marcar como enviado
    receipt.sent_to_student = True
    receipt.sent_at = timezone.now()
    receipt.save()
    
    logger.info(f"Recibo {receipt.receipt_number} enviado a {receipt.student.email}")
```

**Email enviado**:
```
Subject: Recibo de Pago REC-2026-000001

Hola Johanna,

Tu pago ha sido recibido exitosamente.

Detalles del pago:
- Monto pagado: CAD 1,000.00
- Saldo pendiente: CAD 1,608.00
- Método: PayPal
- Fecha: 11/02/2026

Adjunto: recibo_REC-2026-000001.pdf

Puedes realizar otro abono en: https://app.lcmundo.com/payment/token123abc
```

---

## 🔄 **Segundo Pago: $1,000**

### **Usuario vuelve al link y paga**

```
1. Estudiante abre link nuevamente (días después)
2. Frontend muestra: Saldo pendiente: $1,608
3. Estudiante ingresa: $1,000 (segundo abono)
4. PayPal captura el pago ✅
5. Webhook notifica al backend
```

### **Backend procesa segundo pago**

```python
@shared_task
def process_payment_from_webhook(order_number, amount, transaction_id, payment_method, metadata):
    # 1. Obtener orden (ya existe)
    order = PaymentOrder.objects.get(order_number=order_number)
    
    # 2. Obtener Invoice EXISTENTE (NO crear nuevo)
    invoice = order.invoices_payment_order.first()
    # ⚠️ Ya existe desde el primer pago
    
    # 3. Crear nuevo Payment
    payment_2 = Payment.objects.create(
        user=order.student,
        amount=Decimal('1000.00'),
        payment_method='PP',
        reference_number=transaction_id,
        status='D'
    )
    
    # 4. CREAR NUEVO InvoiceCreditDetail (NO actualizar el anterior)
    credit_detail_2 = InvoiceCreditDetail.objects.create(
        invoice=invoice,  # ⬅️ Mismo invoice
        amount=Decimal('1000.00'),
        credit_status='E',
        credit_balance=None
    )
    
    # 5. CREAR NUEVO PaymentReceipt
    receipt_2 = PaymentReceipt.objects.create(
        payment=payment_2,
        invoice=invoice,
        student=order.student,
        amount_paid=Decimal('1000.00'),
        previous_balance=Decimal('1608.00'),
        new_balance=Decimal('608.00'),  # 1608 - 1000
        payment_method='PP',
        payment_date=timezone.now(),
        currency='CAD'
    )
    
    # 6. Vincular
    credit_detail_2.payment_receipt = receipt_2
    credit_detail_2.save()
    
    # 7. Actualizar balance
    invoice.update_balance()
    # balance_due = 608.00
    # status = 'PP' (sigue parcialmente pagada)
    
    # 8. Generar y enviar segundo recibo
    receipt_2.generate_pdf()
    receipt_2.send_to_student_email()
```

**Estado BD después del segundo pago**:
```sql
payments (2 registros):
  id=1, amount=1000.00
  id=2, amount=1000.00  ⬅️ NUEVO

invoice_credit_detail (2 registros):
  id=1, amount=1000.00, credit_status='P'  ⬅️ Cambió a 'P' (Pago)
  id=2, amount=1000.00, credit_status='E'  ⬅️ NUEVO

payment_receipts (2 registros):
  id=1, receipt_number='REC-2026-000001', amount_paid=1000.00
  id=2, receipt_number='REC-2026-000002', amount_paid=1000.00  ⬅️ NUEVO

invoices:
  balance_due=608.00  ⬅️ Actualizado
  status='PP'  ⬅️ Sigue parcialmente pagada

payment_order:
  status='ACTIVE'  ⬅️ Sigue activa
```

---

## ✅ **Tercer y Último Pago: $608**

```python
# Mismo proceso...

# Crear tercer Payment, InvoiceCreditDetail y PaymentReceipt
payment_3 = Payment.objects.create(amount=Decimal('608.00'), ...)
credit_detail_3 = InvoiceCreditDetail.objects.create(amount=Decimal('608.00'), ...)
receipt_3 = PaymentReceipt.objects.create(amount_paid=Decimal('608.00'), new_balance=Decimal('0.00'), ...)

# Actualizar balance
invoice.update_balance()
# balance_due = 0.00
# status = 'P' (Pagada) ✅
# order.status = 'PAID' ✅
```

**Estado Final**:
```sql
payments (3 registros):
  id=1, amount=1000.00
  id=2, amount=1000.00
  id=3, amount=608.00

invoice_credit_detail (3 registros):
  id=1, amount=1000.00, credit_status='P'
  id=2, amount=1000.00, credit_status='P'
  id=3, amount=608.00, credit_status='P'

payment_receipts (3 recibos):
  REC-2026-000001, amount_paid=1000.00
  REC-2026-000002, amount_paid=1000.00
  REC-2026-000003, amount_paid=608.00

invoices:
  balance_due=0.00  ⬅️ PAGADA
  status='P'  ⬅️ Pagada

payment_order:
  status='PAID'  ⬅️ Completamente pagada
```

---

## 📊 **Tabla Resumen de Estados**

| Momento | Order Status | Invoice Status | Balance Due | Registros Creados |
|---------|-------------|----------------|-------------|-------------------|
| Orden creada | `PENDING` | No existe | N/A | PaymentOrder |
| Primer pago | `ACTIVE` | `PP` | $1,608 | Invoice, InvoiceDetail, InvoiceCreditDetail, Payment, PaymentReceipt |
| Segundo pago | `ACTIVE` | `PP` | $608 | InvoiceCreditDetail, Payment, PaymentReceipt |
| Tercer pago | `PAID` | `P` | $0 | InvoiceCreditDetail, Payment, PaymentReceipt |

---

## 🔑 **Puntos Clave**

1. ✅ **Invoice se crea DESPUÉS del primer pago** (no antes)
2. ✅ **Un InvoiceCreditDetail por cada pago**
3. ✅ **Un PaymentReceipt por cada pago**
4. ✅ **`initial_payment_amount` NUNCA se actualiza** (solo para PDF inicial)
5. ✅ **`InvoiceCreditDetail.credit_balance = NULL`** para pagos directos
6. ✅ **Webhook de PayPal dispara todo el proceso**

---

## 📝 **Resumen Ejecutivo**

| Pregunta | Respuesta |
|----------|-----------|
| ¿Cuándo se crea el Invoice? | **Después del primer pago exitoso** |
| ¿Se actualiza `initial_payment_amount`? | **NO, permanece fijo** |
| ¿Dónde se registran los pagos? | **InvoiceCreditDetail** (uno por cada pago) |
| ¿Se usa `StudentCreditBalance` para pagos normales? | **NO, solo para créditos a favor (reembolsos)** |
| ¿Cuántos PaymentReceipt se crean? | **Uno por cada pago** |
| ¿Qué dispara la creación del Invoice? | **El webhook de PayPal confirmando el pago** |

---

## ✅ **Conclusión**

Tu arquitectura está **correctamente diseñada** para manejar pagos parciales:

1. **PaymentOrder**: Define QUÉ se debe pagar
2. **Invoice**: Se crea DESPUÉS del primer pago (evita facturas huérfanas)
3. **InvoiceCreditDetail**: Registra CADA abono
4. **PaymentReceipt**: Comprobante de CADA pago
5. **Webhook de PayPal**: Dispara todo el flujo automáticamente

**El flujo evita facturas sin pagar porque el Invoice solo se crea cuando hay un pago confirmado.** 🎯

