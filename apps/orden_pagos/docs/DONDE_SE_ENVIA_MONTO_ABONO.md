# 🎯 RESUMEN VISUAL: Dónde se Envía el Monto del Abono

## ❌ NO se envía aquí (al crear orden):

```
┌───────────────────────────────────────────────────┐
│  POST /api/v1/payment-orders/                    │
├───────────────────────────────────────────────────┤
│  {                                               │
│    "student": 123,                               │
│    "allows_partial_payment": true,               │
│    "minimum_payment_amount": 50.00, ⬅️ MÍNIMO    │
│    "payment_details": [                          │
│      {                                           │
│        "payment_concept": 1,                     │
│        "amount": 500.00  ⬅️ TOTAL (no el abono) │
│      }                                           │
│    ]                                             │
│  }                                               │
└───────────────────────────────────────────────────┘
```

**Resultado**: Orden creada, status=PENDING, sin pagos

---

## ✅ SÍ se envía aquí (al procesar pago):

```
┌───────────────────────────────────────────────────┐
│  POST /api/v1/payments/process-payment/          │
├───────────────────────────────────────────────────┤
│  {                                               │
│    "order_number": "PO-00001234",                │
│    "amount": 150.00,  ⬅️ MONTO DEL ABONO         │
│    "payment_method": "TRANSFER",                 │
│    "reference_number": "COMP-001"                │
│  }                                               │
└───────────────────────────────────────────────────┘
```

**Resultado**: InvoiceDetail creado con $150, balance_due actualizado

---

## 🔄 Flujo Completo Simplificado:

```
1️⃣ Crear Orden
   ┌─────────────────┐
   │ Frontend        │
   │ Envía:          │
   │ - minimum: $50  │  ⬅️ Solo el mínimo permitido
   │ - total: $500   │  ⬅️ Total a pagar
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Backend         │
   │ Crea:           │
   │ PaymentOrder    │
   │ status=PENDING  │
   │ NO Invoice      │
   └─────────────────┘


2️⃣ Enviar Link
   ┌─────────────────┐
   │ Backend         │
   │ Email con token │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Estudiante      │
   │ Recibe email    │
   │ (ignora 3 días) │
   └─────────────────┘


3️⃣ Estudiante Abre Link (días después)
   ┌─────────────────┐
   │ Frontend        │
   │ GET /by-token/  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Backend         │
   │ Responde:       │
   │ total: $500     │
   │ paid: $0        │
   │ balance: $500   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────────────────┐
   │ Pantalla del Estudiante        │
   │                                 │
   │ Total: $500                    │
   │ Pagado: $0                     │
   │ Saldo: $500                    │
   │                                 │
   │ Monto a pagar (min $50):       │
   │ $ [________] 💳                │  ⬅️ VACÍO
   │                                 │
   │ [PAGAR]                         │
   └─────────────────────────────────┘
   
   👤 Estudiante escribe: $150
                          ^^^^
                          Decide el monto


4️⃣ Procesar Primer Pago
   ┌─────────────────┐
   │ Frontend        │
   │ POST /process/  │
   │ amount: 150  ⬅️ │  AQUÍ va el monto del abono
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Backend         │
   │ Crea:           │
   │ - Invoice       │  ⬅️ Primera vez
   │ - InvoiceDetail │  ⬅️ Con $150
   │ - balance: $350 │
   └─────────────────┘


5️⃣ Estudiante Vuelve (días después)
   ┌─────────────────┐
   │ Frontend        │
   │ GET /by-token/  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Backend         │
   │ Responde:       │
   │ total: $500     │
   │ paid: $150      │  ⬅️ Muestra pago anterior
   │ balance: $350   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────────────────┐
   │ Pantalla del Estudiante        │
   │                                 │
   │ Total: $500                    │
   │ Pagado: $150 ✅                │
   │ Saldo: $350                    │
   │                                 │
   │ Historial:                      │
   │ • $150 - 15/05 - COMP-001      │
   │                                 │
   │ Monto a pagar (min $50):       │
   │ $ [________] 💳                │  ⬅️ VACÍO OTRA VEZ
   │                                 │
   │ [PAGAR]                         │
   └─────────────────────────────────┘
   
   👤 Estudiante escribe: $200
                          ^^^^
                          Decide el nuevo monto


6️⃣ Procesar Segundo Pago
   ┌─────────────────┐
   │ Frontend        │
   │ POST /process/  │
   │ amount: 200  ⬅️ │  AQUÍ va el segundo monto
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Backend         │
   │ Actualiza:      │
   │ - Invoice       │  ⬅️ Ya existe
   │ + InvoiceDetail │  ⬅️ Nuevo con $200
   │ - balance: $150 │
   └─────────────────┘


7️⃣ Repite hasta completar...
```

---

## 📊 Tabla Comparativa:

| Endpoint | Cuándo | Datos que Envía | Monto del Abono |
|----------|--------|-----------------|-----------------|
| **POST /payment-orders/** | Una sola vez (crear orden) | `minimum_payment_amount: 50`<br>`amount: 500` (total) | ❌ NO se envía |
| **POST /process-payment/** | Cada pago (múltiples veces) | `amount: 150` (primer abono)<br>`amount: 200` (segundo abono) | ✅ SÍ se envía |

---

## 💡 Analogía Simple:

Imagina una cuenta bancaria:

### Al abrir la cuenta (crear orden):
```
"Quiero una cuenta que permita depósitos parciales.
Depósito mínimo: $50.
Meta total: $500."
```

**NO depositas dinero todavía**, solo configuras la cuenta.

---

### Al hacer depósitos (procesar pagos):
```
Día 1: "Deposito $150"  ⬅️ Primer depósito
       Balance: $350

Día 5: "Deposito $200"  ⬅️ Segundo depósito
       Balance: $150

Día 10: "Deposito $150" ⬅️ Tercer depósito
        Balance: $0 ✅
```

Cada vez que depositas, **decides el monto en ese momento**.

---

## 🎯 Respuesta Final a tu Pregunta:

> **"¿El monto del abono el front lo debe mandar en los datos de entrada?"**

**NO** en los datos de entrada de la **creación de orden**.

**SÍ** en los datos de entrada del **procesamiento de pago**.

> **"¿Si la persona no hace el pago al instante, solo se busca la orden y se coloca el monto nuevamente?"**

**SÍ, exacto**. El flujo es:

1. Se crea la orden (sin monto de abono)
2. Se envía link
3. Estudiante abre link (puede ser días después)
4. **Frontend muestra input vacío**
5. **Estudiante ingresa el monto** que quiere pagar
6. Frontend envía ese monto a `/process-payment/`
7. Backend crea/actualiza Invoice con ese monto
8. Proceso se repite cada vez que el estudiante abra el link

**El input siempre está vacío**, el estudiante lo llena cada vez que va a pagar.

