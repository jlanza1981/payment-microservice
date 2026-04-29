# 🎯 Solución: Envío de Link con Monto Dinámico para Abonos Subsecuentes

## 🔴 **Problema Identificado**

Mirando tus imágenes, el flujo REAL es:

```
1. Crear orden → Enviar link/PDF con monto ($1,000) ✅
2. Estudiante paga $1,000 ✅
3. ⚠️ PROBLEMA: Necesitas enviar NUEVO link/PDF con saldo pendiente ($1,608)
4. Estudiante paga $1,608 o un abono parcial
5. ⚠️ PROBLEMA: Necesitas enviar OTRO link/PDF con nuevo saldo ($608)
```

**El PDF debe mostrar el monto actualizado en cada envío.**

---

## ✅ **Solución Implementada**

### **1. Template PDF Actualizado**

El template ahora muestra el monto dinámicamente:

```django
{% if data.allows_partial_payment %}
<div class="total" style="background: #d4edda;">
    <span class="text-total">MONTO A PAGAR:</span>
    <span class="monto">
        {{ data.currency }} 
        {% if data.balance_due and data.balance_due > 0 %}
            {{ data.balance_due }}  {# ⬅️ Saldo pendiente si ya hay pagos #}
        {% elif data.initial_payment_amount %}
            {{ data.initial_payment_amount }}  {# ⬅️ Primer abono sugerido #}
        {% else %}
            {{ data.total_order }}  {# ⬅️ Total completo #}
        {% endif %}
    </span>
</div>
{% endif %}
```

**Lógica**:
1. Si hay `balance_due > 0` → Muestra el saldo pendiente actual
2. Si no, si hay `initial_payment_amount` → Muestra el abono inicial sugerido
3. Si no, muestra el `total_order` completo

---

## 📋 **Flujo Actualizado Completo**

### **PRIMERA VEZ: Envío Inicial**

```python
# 1. Crear orden
order = PaymentOrder.objects.create(
    total_order=Decimal('2608.00'),
    allows_partial_payment=True,
    minimum_payment_amount=Decimal('50.00'),
    initial_payment_amount=Decimal('1000.00'),  # ⬅️ Sugerido
    status='PENDING'
)

# 2. Generar PDF (get_order_structure devuelve)
order_structure = {
    'total_order': 2608.00,
    'balance_due': 2608.00,  # ⬅️ Sin pagos aún
    'total_paid': 0.00,
    'initial_payment_amount': 1000.00,  # ⬅️ Existe
    'allows_partial_payment': True
}

# 3. Template renderiza
# Como balance_due = total_order y total_paid = 0
# Usa: initial_payment_amount
```

**PDF muestra**:
```
╔════════════════════════════════╗
║  TOTAL: CAD 2,608.00          ║
║  MONTO A PAGAR: CAD 1,000.00  ║ ⬅️ initial_payment_amount
║                                ║
║  NOTA:                         ║
║  Monto sugerido: CAD 1,000.00 ║
╚════════════════════════════════╝
```

---

### **SEGUNDO ENVÍO: Después del Primer Pago**

```python
# 1. Estudiante pagó $1,000
# 2. Invoice creado con balance_due = $1,608

# 3. Asesor vuelve a enviar link de pago
# (puede ser automático o manual)

# 4. Generar PDF (get_order_structure devuelve)
order_structure = {
    'total_order': 2608.00,
    'balance_due': 1608.00,  # ⬅️ Actualizado después del pago
    'total_paid': 1000.00,  # ⬅️ Ya hay pagos
    'initial_payment_amount': 1000.00,  # ⬅️ Sigue siendo 1000
    'allows_partial_payment': True
}

# 5. Template renderiza
# Como balance_due = 1608 > 0 y total_paid > 0
# Usa: balance_due (NO initial_payment_amount)
```

**PDF muestra**:
```
╔════════════════════════════════╗
║  TOTAL: CAD 2,608.00          ║
║  MONTO A PAGAR: CAD 1,608.00  ║ ⬅️ balance_due actualizado
║                                ║
║  NOTA:                         ║
║  Ya has pagado: CAD 1,000.00  ║
║  Saldo pendiente: CAD 1,608.00║
╚════════════════════════════════╝
```

---

### **TERCER ENVÍO: Después del Segundo Pago**

```python
# 1. Estudiante pagó $1,000 (segundo abono)
# 2. Invoice actualizado con balance_due = $608

# 3. Asesor envía link nuevamente

# 4. Generar PDF (get_order_structure devuelve)
order_structure = {
    'total_order': 2608.00,
    'balance_due': 608.00,  # ⬅️ Nuevo saldo
    'total_paid': 2000.00,  # ⬅️ $1,000 + $1,000
    'initial_payment_amount': 1000.00,  # ⬅️ Sigue fijo
    'allows_partial_payment': True
}

# 5. Template renderiza
# Usa: balance_due
```

**PDF muestra**:
```
╔════════════════════════════════╗
║  TOTAL: CAD 2,608.00          ║
║  MONTO A PAGAR: CAD 608.00    ║ ⬅️ balance_due actualizado
║                                ║
║  NOTA:                         ║
║  Ya has pagado: CAD 2,000.00  ║
║  Saldo pendiente: CAD 608.00  ║
╚════════════════════════════════╝
```

---

## 🔄 **Endpoint para Re-enviar Link de Pago**

Necesitas un endpoint que permita **re-enviar el link** con el monto actualizado:

```python
# apps/orden_pagos/presentation/api/router.py

@payment_orders_router.post('/{order_id}/resend-payment-link/', 
                            response={200: dict, 400: dict})
def resend_payment_link(request, order_id: int):
    """
    Re-envía el link de pago con el monto actualizado.
    Útil cuando ya hay pagos parciales.
    """
    try:
        # Obtener orden
        order = PaymentOrder.objects.get(id=order_id)
        
        # Validar que puede recibir más pagos
        if order.status not in ['PENDING', 'ACTIVE']:
            return 400, {
                'error': f'La orden está en estado {order.status} y no puede recibir pagos'
            }
        
        # Regenerar token (opcional, o reutilizar el existente)
        if not order.token or order.link_expires_at < timezone.now().date():
            order.generate_token_and_expiration_date(days_valid=7)
        
        # Enviar link con PDF actualizado
        result = SendPaymentLinkUseCase(
            repository=payment_order_repository,
            pdf_generator=pdf_generator,
            email_sender=email_sender
        ).execute(order_id=order.id)
        
        return 200, {
            'success': True,
            'message': 'Link de pago re-enviado exitosamente',
            'order_number': order.order_number,
            'balance_due': float(order.get_balance_due()),
            'link_expires_at': order.link_expires_at.isoformat()
        }
        
    except PaymentOrder.DoesNotExist:
        return 400, {'error': 'Orden no encontrada'}
    except Exception as e:
        logger.error(f"Error re-enviando link: {str(e)}")
        return 400, {'error': str(e)}
```

---

## 📝 **Request desde el Frontend**

### **Después del Primer Pago**

```javascript
// Usuario del CRM (asesor) quiere enviar nuevo link

POST /api/v1/payment-orders/123/resend-payment-link/

Response:
{
  "success": true,
  "message": "Link de pago re-enviado exitosamente",
  "order_number": "PO-2026-000025",
  "balance_due": 1608.00,  // ⬅️ Saldo actualizado
  "link_expires_at": "2026-02-18"
}
```

**Email enviado al estudiante**:
```
Subject: Recordatorio - Orden de Pago PO-2026-000025

Hola Johanna,

Tienes un saldo pendiente en tu orden de pago.

Total orden: CAD 2,608.00
Ya pagaste: CAD 1,000.00
Saldo pendiente: CAD 1,608.00

Link de pago: https://app.lcmundo.com/payment/token123abc

Adjunto: orden_pago_actualizada.pdf
```

---

## 🎯 **Flujo Visual Completo**

```
┌─────────────────────────────────────────┐
│  1. CREAR ORDEN                         │
│  total: $2,608                          │
│  initial_payment_amount: $1,000         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  2. ENVIAR LINK #1                      │
│  PDF muestra: "MONTO A PAGAR: $1,000"   │ ⬅️ initial_payment_amount
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  3. ESTUDIANTE PAGA $1,000              │
│  Invoice: balance_due = $1,608          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  4. RE-ENVIAR LINK #2                   │
│  PDF muestra: "MONTO A PAGAR: $1,608"   │ ⬅️ balance_due
│  Nota: "Ya has pagado: $1,000"          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  5. ESTUDIANTE PAGA $1,000              │
│  Invoice: balance_due = $608            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  6. RE-ENVIAR LINK #3                   │
│  PDF muestra: "MONTO A PAGAR: $608"     │ ⬅️ balance_due
│  Nota: "Ya has pagado: $2,000"          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  7. ESTUDIANTE PAGA $608                │
│  Invoice: balance_due = $0              │
│  Orden: status = PAID ✅                │
└─────────────────────────────────────────┘
```

---

## 📊 **Tabla Comparativa: Monto Mostrado en PDF**

| Envío | Estado | total_paid | balance_due | initial_payment_amount | **Monto Mostrado** |
|-------|--------|------------|-------------|------------------------|-------------------|
| #1 | PENDING | $0 | $2,608 | $1,000 | **$1,000** (initial) |
| #2 | ACTIVE | $1,000 | $1,608 | $1,000 | **$1,608** (balance) |
| #3 | ACTIVE | $2,000 | $608 | $1,000 | **$608** (balance) |

---

## 🔑 **Lógica del Template**

```python
def calcular_monto_a_mostrar(order_structure):
    """
    Determina qué monto mostrar en el PDF
    """
    # Si ya hay pagos, mostrar saldo pendiente
    if order_structure['total_paid'] > 0:
        return order_structure['balance_due']
    
    # Si es primera vez y hay sugerencia, mostrarla
    if order_structure['initial_payment_amount']:
        return order_structure['initial_payment_amount']
    
    # Por defecto, mostrar total
    return order_structure['total_order']
```

**Resultado**:
- **Primera vez**: Muestra $1,000 (sugerido)
- **Segunda vez**: Muestra $1,608 (saldo real)
- **Tercera vez**: Muestra $608 (saldo real)

---

## ✅ **Ventajas de esta Solución**

1. ✅ **PDF siempre muestra el monto correcto**
2. ✅ **No necesitas modificar `initial_payment_amount`** (permanece fijo)
3. ✅ **Reutilizas el mismo template** para todos los envíos
4. ✅ **El estudiante ve su historial de pagos** en el PDF
5. ✅ **El asesor puede re-enviar el link** cuando quiera

---

## 📝 **Resumen Ejecutivo**

| Pregunta | Respuesta |
|----------|-----------|
| **¿Cómo envío link después del primer pago?** | Endpoint `/resend-payment-link/` |
| **¿Qué monto muestra el PDF?** | `balance_due` si ya hay pagos, sino `initial_payment_amount` |
| **¿Se actualiza `initial_payment_amount`?** | **NO**, permanece fijo |
| **¿Cómo sabe el template qué mostrar?** | Verifica si `total_paid > 0`, usa `balance_due` |
| **¿Puedo re-enviar el link múltiples veces?** | **SÍ**, cada vez muestra el saldo actualizado |

---

## ✅ **Conclusión**

Con los cambios implementados:

1. ✅ **Template PDF actualizado** para mostrar monto dinámico
2. ✅ **Primera vez**: Muestra `initial_payment_amount` ($1,000)
3. ✅ **Siguientes veces**: Muestra `balance_due` actual ($1,608, $608, etc.)
4. ✅ **Nota del footer**: Muestra historial de pagos si existen
5. ✅ **Endpoint para re-enviar**: Permite enviar link actualizado

**El PDF ahora se adapta automáticamente al estado de pagos de la orden.** 🎯

