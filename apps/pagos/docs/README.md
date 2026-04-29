# Documentación del Módulo de Pagos

Sistema de gestión de pagos para LC Mundo con soporte para múltiples flujos de pago.

## 📋 Índice

1. [Guía de Uso: CreatePaymentUseCase](./USO_CREATE_PAYMENT.md)
2. [Guía del Servicio de Dominio de Pagos](./GUIA_SERVICIO_DOMINIO_PAGOS.md) ⭐ **NUEVO**
3. [Diagramas de Flujos de Pago](./DIAGRAMAS_FLUJOS_PAGO.md)
4. [Ejemplos de Uso con Endpoints](./EJEMPLOS_USO_ENDPOINTS.py)
5. [Resumen Ejecutivo de Refactorización](./RESUMEN_REFACTORIZACION.md)

## 🎯 Descripción General

El módulo de pagos maneja dos flujos principales:

### Flujo 1: Pago Exonerado (con Factura)

```
Orden de Pago → Factura → Pago Automático
```

- Usado cuando el estudiante es exonerado
- La factura se genera inmediatamente
- El pago se marca como verificado automáticamente

### Flujo 2: Pago Anticipado (sin Factura)

```
Orden de Pago → Pago del Estudiante → Factura
```

- El estudiante paga primero
- El pago se registra sin factura
- La factura se genera después y se asocia al pago

## 🏗️ Arquitectura

```
presentation/          # API endpoints (Django Ninja)
├── api/
│   └── schemas/      # Pydantic schemas

application/          # Casos de uso (lógica de negocio)
├── use_cases/
│   └── create_payment.py   # ← REFACTORIZADO
└── commands.py       # Comandos (DTOs)

domain/               # Interfaces y contratos
└── interface/
    └── repository/

infrastructure/       # Implementaciones
└── repository/
    └── payment_repository.py
```

## 🚀 Inicio Rápido

### Crear Pago Exonerado

```python
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePaymentUseCase
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

# Inicializar caso de uso
repository = PaymentRepository()
use_case = CreatePaymentUseCase(repository)

# Crear pago exonerado
payment = use_case.create_exonerated_payment(
    invoice=invoice_instance,
    user=student,
    advisor=advisor,
    amount=Decimal('1500.00'),
    currency='USD'
)
```

### Crear Pago Anticipado

```python
# Crear pago sin factura
payment = use_case.create_advance_payment(
    user=student,
    advisor=advisor,
    amount=Decimal('500.00'),
    payment_method='PP',
    payment_reference_number='PAYPAL-12345',
    status='D'
)

# Después generar y asociar factura
payment = use_case.associate_invoice_to_payment(
    payment_id=payment.id,
    invoice_id=invoice.id,
    allocations=[...]
)
```

## 📊 Modelos Principales

### Payment

- `payment_number`: Número único de pago (auto-generado)
- `invoice`: Factura asociada (opcional, puede ser None)
- `user`: Usuario que realiza el pago
- `advisor`: Asesor asignado
- `amount`: Monto del pago
- `payment_method`: Método de pago (PP, ST, TC, BT, EF, EX, etc.)
- `status`: Estado (P, D, V, R, X)
- `currency`: Moneda (USD, EUR, etc.)

### PaymentAllocation

- `payment`: Pago asociado
- `invoice_detail`: Detalle de factura
- `payment_concept`: Concepto de pago
- `amount_applied`: Monto aplicado
- `status`: Estado de la asignación

## 🔗 Enlaces Relacionados

- [Modelos de Billing](../../billing/models.py)
- [Modelos de Orden de Pagos](../../orden_pagos/models.py)
- [Sistema de Abonos](../../../docs/GUIA_RAPIDA_SISTEMA_ABONOS.md)

## 📝 Notas Importantes

1. **Transacciones Atómicas**: Todos los métodos principales usan `@transaction.atomic()`
2. **Logging**: Se registran todas las operaciones importantes
3. **Validaciones**: Se validan datos antes de crear/actualizar
4. **Type Hints**: Todo el código usa type hints para mejor IDE support

## 🧪 Testing

Ver archivo de tests completo: [test_create_payment_flows.py](../tests/test_create_payment_flows.py)

```bash
# Ejecutar tests
python manage.py test apps.pagos.tests.test_create_payment_flows
```

## 📞 Contacto y Soporte

Para dudas o problemas, contactar al equipo de desarrollo.
