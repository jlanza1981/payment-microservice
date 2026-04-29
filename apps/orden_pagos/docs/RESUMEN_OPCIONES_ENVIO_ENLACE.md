# 🎯 RESUMEN: Tres Formas de Enviar Enlace de Pago

## Problema Original

El asesor presiona "Enviar Enlace de Pago" y el sistema debe crear/actualizar la orden y enviar el enlace, pero no
queremos hacer dos llamadas HTTP desde el frontend.

## ✅ SOLUCIONES IMPLEMENTADAS

---

### **Opción 1: Endpoint Combinado `create-and-send` ⭐ RECOMENDADO**

**Ideal para**: Cuando el asesor presiona el botón "Enviar Enlace"

#### Endpoint:

```
POST /api/v1/payment-orders/create-and-send/
```

#### Ventajas:

- ✅ **Una sola llamada HTTP**
- ✅ **Detección automática** (crear vs actualizar)
- ✅ **Más intuitivo** para el frontend
- ✅ **Código más limpio**

#### Request:

```json
{
  "order_id": null,
  // null = crear, ID = actualizar
  "send_password": false,
  "new_password": null,
  "order_data": {
    "student_id": 123,
    "advisor_id": 5,
    "payment_details": [
      ...
    ]
  }
}
```

#### Response:

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "message": "Orden creada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com"
}
```

#### Código Frontend (React):

```javascript
const handleEnviarEnlace = async () => {
    const response = await fetch('/api/v1/payment-orders/create-and-send/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: currentOrderId || null,  // null si es nueva
            send_password: true,
            new_password: 'Temp2025',
            order_data: orderFormData
        })
    });

    const result = await response.json();
    toast.success(`Orden ${result.order_number} y enlace enviado!`);
};
```

---

### **Opción 2: Query Parameters en CREATE/UPDATE**

**Ideal para**: Cuando ya tienes endpoints separados y solo quieres agregar el envío

#### Crear orden con envío automático:

```
POST /api/v1/payment-orders/?send_payment_link=true&send_password=false
```

#### Actualizar orden con envío automático:

```
PUT /api/v1/payment-orders/123/?send_payment_link=true&new_password=Temp123
```

#### Ventajas:

- ✅ **Usa endpoints existentes**
- ✅ **Flexible** - Puedes enviar o no el enlace
- ✅ **Fácil de implementar** en frontend existente

#### Código Frontend (React):

```javascript
// Crear orden nueva con envío
const response = await fetch(
    '/api/v1/payment-orders/?send_payment_link=true',
    {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    }
);

// Actualizar orden con envío
const response = await fetch(
    `/api/v1/payment-orders/${orderId}/?send_payment_link=true&send_password=true&new_password=Temp123`,
    {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    }
);
```

#### Response:

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "student": {
    ...
  },
  "payment_link_sent": true,
  "payment_link_task_id": "abc123"
}
```

---

### **Opción 3: Endpoint Separado `send-payment-link`**

**Ideal para**: Reenviar enlace de una orden ya creada

#### Endpoint:

```
POST /api/v1/payment-orders/{id}/send-payment-link/
```

#### Ventajas:

- ✅ **Especializado** en solo enviar el enlace
- ✅ **Útil para reenvíos**
- ✅ **Validación estricta** (solo PENDING)

#### Request:

```json
{
  "send_password": true,
  "new_password": "Temporal2025!"
}
```

#### Código Frontend (React):

```javascript
// Solo enviar enlace de orden existente
const response = await fetch(
    `/api/v1/payment-orders/${orderId}/send-payment-link/`,
    {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            send_password: true,
            new_password: 'Temp2025'
        })
    }
);
```

---

## 📊 Comparación Rápida

| Característica   | create-and-send | Query Params | send-payment-link  |
|------------------|-----------------|--------------|--------------------|
| Llamadas HTTP    | **1**           | **1**        | 2 (crear + enviar) |
| Crear orden      | ✅               | ✅            | ❌                  |
| Actualizar orden | ✅               | ✅            | ❌                  |
| Solo enviar      | ❌               | ❌            | ✅                  |
| Detección auto   | ✅               | ❌            | ❌                  |
| Reenviar enlace  | ❌               | ❌            | ✅                  |
| Frontend limpio  | ⭐⭐⭐             | ⭐⭐           | ⭐                  |

---

## 🎯 Recomendación por Caso de Uso

### **Caso 1: Botón "Enviar Enlace" en formulario nuevo/existente**

```
✅ Usa: create-and-send
```

**Por qué**: Una sola llamada, detección automática, más simple.

### **Caso 2: Ya tienes formularios separados de crear/editar**

```
✅ Usa: Query Parameters
```

**Por qué**: Mínimo cambio en frontend existente.

### **Caso 3: Botón "Reenviar Enlace" en lista de órdenes**

```
✅ Usa: send-payment-link
```

**Por qué**: Solo necesitas enviar, la orden ya existe.

---

## 💻 Ejemplo Completo: Componente React

```javascript
import React, {useState} from 'react';
import {toast} from 'react-toastify';

function OrdenPagoForm({existingOrderId = null, studentId, advisorId}) {
    const [loading, setLoading] = useState(false);
    const [orderData, setOrderData] = useState({
        student_id: studentId,
        advisor_id: advisorId,
        payment_details: []
    });
    const [sendPassword, setSendPassword] = useState(false);
    const [password, setPassword] = useState('');

    // OPCIÓN 1: Usar create-and-send (RECOMENDADO)
    const handleEnviarEnlaceOpcion1 = async () => {
        setLoading(true);

        try {
            const response = await fetch('/api/v1/payment-orders/create-and-send/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: existingOrderId,  // null si es nueva, ID si actualiza
                    send_password: sendPassword,
                    new_password: sendPassword ? password : null,
                    order_data: orderData
                })
            });

            if (!response.ok) throw new Error('Error');

            const result = await response.json();

            toast.success(
                `✅ ${result.message}\n` +
                `📧 Enlace enviado a ${result.student_email}`
            );

        } catch (error) {
            toast.error('❌ Error al procesar solicitud');
        } finally {
            setLoading(false);
        }
    };

    // OPCIÓN 2: Usar query parameters
    const handleEnviarEnlaceOpcion2 = async () => {
        setLoading(true);

        try {
            const url = existingOrderId
                ? `/api/v1/payment-orders/${existingOrderId}/?send_payment_link=true`
                : `/api/v1/payment-orders/?send_payment_link=true`;

            const method = existingOrderId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) throw new Error('Error');

            const result = await response.json();

            toast.success(
                result.payment_link_sent
                    ? `✅ Orden ${result.order_number} y enlace enviado`
                    : `⚠️ Orden creada pero no se pudo enviar enlace`
            );

        } catch (error) {
            toast.error('❌ Error al procesar solicitud');
        } finally {
            setLoading(false);
        }
    };

    // OPCIÓN 3: Solo reenviar (orden ya existe)
    const handleReenviarEnlace = async () => {
        if (!existingOrderId) {
            toast.error('No hay orden para reenviar');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(
                `/api/v1/payment-orders/${existingOrderId}/send-payment-link/`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        send_password: sendPassword,
                        new_password: sendPassword ? password : null
                    })
                }
            );

            if (!response.ok) throw new Error('Error');

            const result = await response.json();

            toast.success(`✅ ${result.message}`);

        } catch (error) {
            toast.error('❌ Error al reenviar enlace');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="orden-pago-form">
            {/* Formulario aquí */}

            <div className="form-actions">
                <button
                    onClick={handleEnviarEnlaceOpcion1}
                    disabled={loading}
                    className="btn btn-primary"
                >
                    {loading ? 'Procesando...' : 'Crear/Actualizar y Enviar'}
                </button>

                {existingOrderId && (
                    <button
                        onClick={handleReenviarEnlace}
                        disabled={loading}
                        className="btn btn-secondary"
                    >
                        Reenviar Enlace
                    </button>
                )}
            </div>
        </div>
    );
}

export default OrdenPagoForm;
```

---

## 🚀 Migración del Código Existente

### Si actualmente haces esto:

```javascript
// ❌ DOS LLAMADAS
const order = await createOrder(orderData);
await sendPaymentLink(order.id);
```

### Cámbialo por esto:

```javascript
// ✅ UNA LLAMADA
const result = await fetch('/api/v1/payment-orders/create-and-send/', {
    method: 'POST',
    body: JSON.stringify({
        order_id: null,
        order_data: orderData
    })
});
```

---

## 📋 Checklist de Implementación Frontend

- [ ] Decidir qué opción usar según tu caso de uso
- [ ] Actualizar el endpoint en tu servicio/API client
- [ ] Modificar el componente del formulario
- [ ] Agregar manejo de loading state
- [ ] Implementar manejo de errores
- [ ] Mostrar mensajes de éxito/error al usuario
- [ ] Probar con orden nueva
- [ ] Probar con orden existente
- [ ] Probar envío con/sin contraseña
- [ ] Probar manejo de errores

---

**Fecha**: 28 de Noviembre de 2025  
**Estado**: ✅ Tres opciones implementadas y documentadas  
**Recomendación**: Usa `create-and-send` para el botón principal del asesor

