# Guía Frontend - Envío de Enlace de Pago desde el Asesor

## 🎯 Problema Resuelto

Evitar hacer **dos llamadas al backend** cuando el asesor presiona el botón "Enviar Enlace de Pago".
Ahora todo se hace en **una sola llamada** que crea/actualiza la orden y envía el enlace automáticamente.

---

## 🚀 Soluciones Disponibles

### **Opción 1: Endpoint Combinado `create-and-send` (RECOMENDADO)**

Este es el endpoint más optimizado para tu caso de uso.

#### Características:

- ✅ Una sola llamada HTTP
- ✅ Detecta automáticamente si debe crear o actualizar
- ✅ Envía el enlace de pago inmediatamente
- ✅ Retorna toda la información en una respuesta

#### Endpoint:

```
POST /api/v1/payment-orders/create-and-send/
```

---

## 📝 Ejemplos de Uso desde el Frontend

### **Caso 1: Crear Nueva Orden y Enviar Enlace**

```javascript
// React/Vue/Angular Example
async function crearOrdenYEnviarEnlace(orderData, sendPassword = false, password = null) {
    const response = await fetch('/api/v1/payment-orders/create-and-send/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: null,  // null = crear nueva orden
            send_password: sendPassword,
            new_password: password,
            order_data: orderData
        })
    });

    if (!response.ok) {
        throw new Error('Error al crear orden');
    }

    return await response.json();
}

// Uso en el componente
const handleEnviarEnlace = async () => {
    try {
        setLoading(true);

        const orderData = {
            student_id: 123,
            advisor_id: 5,
            opportunity_id: 50,
            quotation_id: 25,
            payment_details: [
                {
                    payment_type_id: 1,
                    amount: 1000.00,
                    discount_type: "percentage",
                    discount_amount: 10.00
                }
            ],
            payment_program: {
                program_type_id: 1,
                institution_id: 10,
                country_id: 5,
                city_id: 15,
                program_id: 20,
                start_date: "2025-01-15",
                duration: 12,
                duration_type: "w",
                price_week: 250.00
            }
        };

        const result = await crearOrdenYEnviarEnlace(orderData, false);

        // Mostrar mensaje de éxito
        toast.success(`Orden ${result.order_number} creada y enlace enviado a ${result.student_email}`);

        // Opcional: rastrear el estado del envío
        console.log('Task ID:', result.payment_link_task_id);

    } catch (error) {
        toast.error('Error al crear orden y enviar enlace');
        console.error(error);
    } finally {
        setLoading(false);
    }
};
```

### **Caso 2: Actualizar Orden Existente y Enviar Enlace**

```javascript
async function actualizarOrdenYEnviarEnlace(orderId, orderData, sendPassword = false, password = null) {
    const response = await fetch('/api/v1/payment-orders/create-and-send/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: orderId,  // ID de la orden existente
            send_password: sendPassword,
            new_password: password,
            order_data: orderData
        })
    });

    if (!response.ok) {
        throw new Error('Error al actualizar orden');
    }

    return await response.json();
}

// Uso en el componente
const handleActualizarYEnviar = async () => {
    try {
        setLoading(true);

        const orderData = {
            payment_details: [
                {
                    payment_type_id: 1,
                    amount: 1200.00,  // Monto actualizado
                    discount_type: "fixed",
                    discount_amount: 100.00
                }
            ]
        };

        const result = await actualizarOrdenYEnviarEnlace(
            currentOrderId,
            orderData,
            true,  // Enviar contraseña
            'Temporal2025!'
        );

        toast.success(`Orden ${result.order_number} actualizada y enlace enviado`);

    } catch (error) {
        toast.error('Error al actualizar orden');
    } finally {
        setLoading(false);
    }
};
```

---

## 🎨 Ejemplo Completo de Componente React

```javascript
import React, {useState} from 'react';
import {toast} from 'react-toastify';

function CrearOrdenPagoForm({studentId, advisorId, opportunityId}) {
    const [loading, setLoading] = useState(false);
    const [orderData, setOrderData] = useState({
        student_id: studentId,
        advisor_id: advisorId,
        opportunity_id: opportunityId,
        payment_details: [],
        payment_program: null
    });
    const [sendPassword, setSendPassword] = useState(false);
    const [password, setPassword] = useState('');

    const handleSubmitAndSend = async (e) => {
        e.preventDefault();

        if (!orderData.payment_details.length) {
            toast.error('Debe agregar al menos un concepto de pago');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('/api/v1/payment-orders/create-and-send/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: null,  // Crear nueva
                    send_password: sendPassword,
                    new_password: sendPassword ? password : null,
                    order_data: orderData
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error desconocido');
            }

            const result = await response.json();

            // Éxito
            toast.success(
                `✅ Orden ${result.order_number} creada exitosamente\n` +
                `📧 Enlace enviado a ${result.student_email}`,
                {autoClose: 5000}
            );

            // Opcional: Redireccionar o actualizar estado
            // navigate(`/ordenes/${result.id}`);

        } catch (error) {
            toast.error(`❌ ${error.message}`);
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmitAndSend}>
            {/* Formulario de orden de pago */}

            <div className="form-group">
                <label>
                    <input
                        type="checkbox"
                        checked={sendPassword}
                        onChange={(e) => setSendPassword(e.target.checked)}
                    />
                    Enviar contraseña al estudiante
                </label>
            </div>

            {sendPassword && (
                <div className="form-group">
                    <input
                        type="text"
                        placeholder="Contraseña temporal"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
            )}

            <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
            >
                {loading ? (
                    <>
                        <span className="spinner"></span>
                        Procesando...
                    </>
                ) : (
                    'Crear Orden y Enviar Enlace'
                )}
            </button>
        </form>
    );
}

export default CrearOrdenPagoForm;
```

---

## 🔧 Ejemplo con Vue.js

```vue

<template>
  <div class="orden-pago-form">
    <form @submit.prevent="crearYEnviar">
      <!-- Formulario de orden -->

      <div class="form-check">
        <input
            type="checkbox"
            id="sendPassword"
            v-model="sendPassword"
        />
        <label for="sendPassword">
          Enviar contraseña al estudiante
        </label>
      </div>

      <input
          v-if="sendPassword"
          type="text"
          v-model="password"
          placeholder="Contraseña temporal"
          required
      />

      <button
          type="submit"
          :disabled="loading"
          class="btn btn-primary"
      >
        {{ loading ? 'Procesando...' : 'Crear Orden y Enviar Enlace' }}
      </button>
    </form>
  </div>
</template>

<script>
  export default {
    name: 'OrdenPagoForm',
    props: ['studentId', 'advisorId', 'opportunityId'],
    data() {
      return {
        loading: false,
        sendPassword: false,
        password: '',
        orderData: {
          student_id: this.studentId,
          advisor_id: this.advisorId,
          opportunity_id: this.opportunityId,
          payment_details: [],
          payment_program: null
        }
      };
    },
    methods: {
      async crearYEnviar() {
        this.loading = true;

        try {
          const response = await this.$http.post(
              '/api/v1/payment-orders/create-and-send/',
              {
                order_id: null,
                send_password: this.sendPassword,
                new_password: this.sendPassword ? this.password : null,
                order_data: this.orderData
              }
          );

          this.$toast.success(
              `Orden ${response.data.order_number} creada y enlace enviado a ${response.data.student_email}`
          );

          // Opcional: Emitir evento o redireccionar
          this.$emit('orden-creada', response.data);

        } catch (error) {
          this.$toast.error(error.response?.data?.error || 'Error al crear orden');
        } finally {
          this.loading = false;
        }
      }
    }
  };
</script>
```

---

## 📊 Respuesta del Endpoint

### Éxito (201 Created / 200 OK):

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "student": {
    "id": 123,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan.perez@example.com"
  },
  "advisor": {
    "id": 5,
    "nombre": "María",
    "apellido": "García",
    "email": "maria.garcia@lcmundo.com"
  },
  "status": "PENDING",
  "total_order": "3500.00",
  "payment_link_date": "2025-11-28",
  "message": "Orden creada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123-def456",
  "student_email": "juan.perez@example.com",
  "advisor_email": "maria.garcia@lcmundo.com"
}
```

### Error (400 Bad Request):

```json
{
  "error": "La orden está en estado PAID. Solo se puede enviar enlace en estado PENDING."
}
```

---

## 🎯 Alternativa: Usar Query Parameters

Si prefieres usar los endpoints normales de CREATE/UPDATE con parámetros:

### Crear orden con envío automático:

```javascript
const response = await fetch(
    '/api/v1/payment-orders/?send_payment_link=true&send_password=true&new_password=Temp123',
    {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    }
);
```

### Actualizar orden con envío automático:

```javascript
const response = await fetch(
    `/api/v1/payment-orders/${orderId}/?send_payment_link=true`,
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

---

## 🔄 Comparación de Enfoques

### ❌ Antiguo (2 llamadas):

```javascript
// 1. Crear orden
const order = await createOrder(orderData);

// 2. Enviar enlace (llamada adicional)
await sendPaymentLink(order.id);
```

**Problema:** 2 llamadas HTTP, más lento, más propenso a errores.

### ✅ Nuevo (1 llamada):

```javascript
// Todo en una sola llamada
const result = await createAndSendPaymentLink(orderData);
```

**Ventaja:** 1 llamada HTTP, más rápido, más confiable.

---

## 🎨 Flujo del Botón "Enviar Enlace"

```
┌────────────────────────────────┐
│  Asesor presiona botón        │
│  "Enviar Enlace de Pago"      │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│  Frontend valida formulario    │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│  UNA SOLA LLAMADA HTTP         │
│  POST /create-and-send/        │
│  {                             │
│    order_id: null/ID,          │
│    order_data: {...},          │
│    send_password: true/false   │
│  }                             │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│  Backend:                      │
│  1. Crea/actualiza orden       │
│  2. Genera PDF                 │
│  3. Envía correos (async)      │
│  4. Retorna respuesta          │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│  Frontend muestra mensaje      │
│  "Orden creada y enlace        │
│   enviado exitosamente"        │
└────────────────────────────────┘
```

---

## 💡 Recomendaciones

1. **Usa `create-and-send`** para el caso de uso principal del asesor
2. **Usa query parameters** si necesitas más flexibilidad en endpoints existentes
3. **Maneja errores apropiadamente** en el frontend
4. **Muestra feedback** al usuario mientras procesa
5. **Guarda el `task_id`** si necesitas rastrear el estado del envío

---

## 🚨 Manejo de Errores

```javascript
try {
    const result = await createAndSendPaymentLink(orderData);

    if (result.payment_link_sent) {
        toast.success('✅ Orden creada y enlace enviado');
    } else {
        toast.warning(`⚠️ Orden creada pero: ${result.payment_link_error}`);
    }

} catch (error) {
    if (error.response?.status === 400) {
        toast.error('❌ Error de validación: ' + error.response.data.error);
    } else if (error.response?.status === 500) {
        toast.error('❌ Error del servidor. Intente nuevamente.');
    } else {
        toast.error('❌ Error de conexión');
    }
}
```

---

**Fecha**: 28 de Noviembre de 2025  
**Optimización**: Una sola llamada HTTP para crear/actualizar y enviar enlace  
**Estado**: ✅ Listo para implementar en frontend

