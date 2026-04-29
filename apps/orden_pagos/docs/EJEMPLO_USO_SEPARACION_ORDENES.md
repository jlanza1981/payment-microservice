# Ejemplo de Uso: Separación Automática de Órdenes

## Caso 1: Crear orden solo con Costo Administrativo

**Request:**

```json
POST /api/v1/payment-orders/

{
  "student_id": 123,
  "advisor_id": 456,
  "opportunity_id": 789,
  "payment_details": [
    {
      "payment_type_id": 1,
      "type_administrative_cost_id": 5,
      "amount": "100.00",
      "discount_type": null,
      "discount_amount": "0.00"
    }
  ],
  "program_data": {
    "program_type_id": 1,
    "institution_id": 10,
    "country_id": 1,
    "city_id": 1,
    "start_date": "2025-02-01",
    "duration": 4,
    "duration_type": "w",
    "price_week": "300.00",
    "material_cost": "50.00"
  }
}
```

**Response (UNA sola orden):**

```json
{
  "id": 100,
  "order_number": "PO-0000100",
  "student": {
    ...
  },
  "advisor": {
    ...
  },
  "status": "PENDING",
  "total_order": "100.00",
  "payment_order_details": [
    {
      "payment_type": {
        "code": "C",
        "description": "Costo Administrativo"
      },
      "amount": "100.00",
      "sub_total": "100.00"
    }
  ],
  ...
}
```

---

## Caso 2: Crear orden con Costo Administrativo + Matrícula

**Request:**

```json
POST /api/v1/payment-orders/

{
  "student_id": 123,
  "advisor_id": 456,
  "opportunity_id": 789,
  "payment_details": [
    {
      "payment_type_id": 1,
      "type_administrative_cost_id": 5,
      "amount": "100.00",
      "discount_type": null,
      "discount_amount": "0.00"
    },
    {
      "payment_type_id": 3,
      "amount": "1200.00",
      "discount_type": null,
      "discount_amount": "0.00"
    }
  ],
  "program_data": {
    "program_type_id": 1,
    "institution_id": 10,
    "country_id": 1,
    "city_id": 1,
    "start_date": "2025-02-01",
    "duration": 4,
    "duration_type": "w",
    "price_week": "300.00",
    "material_cost": "50.00"
  }
}
```

**Response (DOS órdenes separadas):**

```json
{
  "orders": [
    {
      "id": 100,
      "order_number": "PO-0000100",
      "student": {
        ...
      },
      "advisor": {
        ...
      },
      "status": "PENDING",
      "total_order": "100.00",
      "payment_order_details": [
        {
          "payment_type": {
            "code": "C",
            "description": "Costo Administrativo"
          },
          "amount": "100.00",
          "sub_total": "100.00"
        }
      ],
      "payment_order_program": {
        "program_type": "Idiomas",
        "institution": "EF Education",
        "country": "Canadá",
        "city": "Toronto",
        "duration": 0,
        "price_week": "0.00",
        "total_enrollment": "0.00"
      },
      ...
    },
    {
      "id": 101,
      "order_number": "PO-0000101",
      "student": {
        ...
      },
      "advisor": {
        ...
      },
      "status": "PENDING",
      "total_order": "1250.00",
      "payment_order_details": [
        {
          "payment_type": {
            "code": "M",
            "description": "Matricula"
          },
          "amount": "1200.00",
          "sub_total": "1200.00"
        }
      ],
      "payment_order_program": {
        "program_type": "Idiomas",
        "institution": "EF Education",
        "country": "Canadá",
        "city": "Toronto",
        "duration": 4,
        "duration_type": "w",
        "price_week": "300.00",
        "material_cost": "50.00",
        "total_enrollment": "1250.00"
      },
      ...
    }
  ],
  "split": true,
  "message": "Se crearon dos órdenes separadas: una para pagos independientes y otra para pagos dependientes del programa"
}
```

---

## Caso 3: Enviar enlace de pago automáticamente

**Request con query parameter:**

```
POST /api/v1/payment-orders/?send_payment_link=true

{...datos de la orden...}
```

**Comportamiento:**

- Si se crea **1 orden**: Envía 1 correo
- Si se crean **2 órdenes**: Envía 2 correos (uno por cada orden)

**Response incluirá información del envío:**

```json
{
  "orders": [
    ...
  ],
  "split": true,
  "message": "...",
  "email_sent": {
    "order_1": {
      "success": true,
      "emails": [
        "student@example.com",
        "advisor@example.com"
      ]
    },
    "order_2": {
      "success": true,
      "emails": [
        "student@example.com",
        "advisor@example.com"
      ]
    }
  }
}
```

---

## Códigos de Tipo de Pago

### Independientes (no requieren programa):

| Código | Descripción           |
|--------|-----------------------|
| C      | Costo Administrativo  |
| F      | Booking Fee           |
| I      | Inscripción           |
| D      | Airport Drop-off      |
| H      | HomeStay              |
| AH     | Abono de Alojamiento  |
| CL     | Custodian Letter      |
| ST     | Student Services Fee  |
| CF     | Courier Fees          |
| HS     | Homestay Special Diet |

### Dependientes (requieren programa):

| Código | Descripción                          |
|--------|--------------------------------------|
| M      | Matricula                            |
| B      | Inscripción y Matricula              |
| T      | Pago Total                           |
| E      | Extension de Matricula               |
| A      | Abono de Matricula                   |
| IA     | Inscripción y Abono                  |
| BF     | Inscripción, Matricula y Booking Fee |
| IF     | Inscripción y Booking Fee            |
| MF     | Matricula y Booking Fee              |
| HF     | HomeStay y Booking Fee               |
| AF     | Abono y Booking Fee                  |
| R      | Airport Pick-up                      |
| S      | Seguro Médico                        |
| U      | Adicionales completos                |

---

## Manejo en el Frontend

```javascript
// Crear orden
const response = await createPaymentOrder(orderData);

if (response.split) {
    // Se crearon dos órdenes
    console.log('Se crearon dos órdenes separadas');
    console.log('Orden 1 (independientes):', response.orders[0]);
    console.log('Orden 2 (dependientes):', response.orders[1]);

    // Mostrar ambas órdenes al usuario
    displayOrders(response.orders);
} else {
    // Se creó una sola orden
    console.log('Orden única:', response);
    displayOrder(response);
}
```

---

## Notas Importantes

1. **Las órdenes son independientes**: Cada una tiene su propio estado, token, PDF y correo
2. **Se pueden pagar por separado**: No hay dependencia entre ellas
3. **Moneda**: Cada orden usa la moneda de su institución
4. **Números correlativos**: Cada orden tiene su propio número (PO-XXXXXXX)
5. **Programa mínimo**: La orden de tipos independientes mantiene contexto pero sin cálculos de precio

