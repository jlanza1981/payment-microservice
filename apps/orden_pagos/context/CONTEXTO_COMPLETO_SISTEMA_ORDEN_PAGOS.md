# 📋 CONTEXTO COMPLETO - Sistema de Órdenes de Pago

**Fecha:** 28 de Noviembre de 2025  
**Sistema:** LC Mundo - Órdenes de Pago  
**App:** `apps/orden_pagos`  
**Arquitectura:** Clean Architecture + DDD

---

## 🎯 RESUMEN EJECUTIVO

El sistema de **Órdenes de Pago** permite la gestión completa de órdenes de pago para estudiantes, incluyendo:

- ✅ **Creación y actualización** de órdenes de pago
- ✅ **Gestión de múltiples conceptos de pago** (matrícula, inscripción, cargos administrativos, etc.)
- ✅ **Cálculo automático de descuentos** (porcentuales y fijos)
- ✅ **Información de programas educativos** asociados a la orden
- ✅ **Envío automático de enlaces de pago** por correo electrónico con PDF adjunto
- ✅ **Estados de orden** (PENDING, PAID, VERIFIED, CANCELLED)
- ✅ **Generación automática de números de orden** (OP202400001, OP202400002, etc.)
- ✅ **API REST completa** con filtros, paginación y búsquedas

---

## 📁 ESTRUCTURA DE LA APP

```
apps/orden_pagos/
├── domain/                          # Capa de Dominio
│   └── interface/
│       ├── repository/
│       │   └── payment_order_repository_interface.py
│       └── services/
│           └── payment_order_domain_service.py
│
├── application/                     # Capa de Aplicación
│   ├── commands.py                  # DTOs para comandos
│   ├── queries.py                   # DTOs para consultas
│   └── use_cases/                   # Casos de uso
│       ├── create_payment_order.py
│       ├── update_payment_order.py
│       ├── get_payment_order_by_id.py
│       ├── get_payment_order_by_number.py
│       ├── list_payment_orders.py
│       ├── delete_payment_order_by_id.py
│       ├── mark_order_as_paid.py
│       ├── cancel_order.py
│       ├── verify_order.py
│       └── change_payment_order_status.py
│
├── infrastructure/                  # Capa de Infraestructura
│   ├── repository/
│   │   └── payment_order_repository.py
│   └── serializers/
│       ├── payment_order_serializer.py
│       ├── payment_order_input_serializer.py
│       ├── payment_structure.py
│       └── payment_structure_field.py
│
├── presentation/                    # Capa de Presentación
│   └── views/
│       └── payment_order_viewset.py
│
├── templates/                       # Plantillas HTML
│   ├── correo-enlace-pago-orden.html
│   └── pdf_orden_pago.html
│
├── context/                         # Documentación de contexto
│   ├── CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md
│   └── CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md (este archivo)
│
├── docs/                            # Documentación técnica
│   ├── PAYMENT_ORDERS_API_DOCUMENTATION.md
│   ├── IMPLEMENTACION_COMPLETADA_ENLACE_PAGO.md
│   ├── GUIA_FRONTEND_ENVIO_ENLACE.md
│   ├── EJEMPLO_USO_ENVIO_ENLACE_PAGO.md
│   ├── RESUMEN_ENVIO_ENLACE_PAGO.md
│   ├── RESUMEN_OPCIONES_ENVIO_ENLACE.md
│   ├── CAMBIOS_SIN_CONTRASENAS_TEMPORALES.md
│   └── EJEMPLOS_FRONTEND_PAGINACION.md
│
├── models.py                        # Modelos de Django
├── admin.py                         # Configuración del admin
├── tasks.py                         # Tareas de Celery
├── signals.py                       # Señales de Django
├── urls_V1.py                       # URLs de la API v1
├── apps.py                          # Configuración de la app
└── tests.py                         # Tests
```

---

## 🗄️ MODELOS DE BASE DE DATOS

### 1. **PaymentType** (Tipos de Pago)

Define los diferentes tipos de pago disponibles en el sistema.

**Tabla:** `payment_type`

```python
class PaymentType(Modelo):
    code = models.CharField(max_length=2, unique=True)          # Ej: 'I', 'M', 'B', 'C'
    description = models.CharField(max_length=100)              # Ej: 'Inscripción', 'Matrícula'
    combined_codes = models.CharField(max_length=10, ...)       # Códigos combinados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Códigos de Tipo de Pago:**

| Código | Descripción                                   | Requiere Programa |
|--------|-----------------------------------------------|-------------------|
| **I**  | Inscripción                                   | Sí                |
| **M**  | Matrícula                                     | Sí                |
| **B**  | Inscripción y Matrícula                       | Sí                |
| **T**  | Inscripción, Matrícula y Cargo Administrativo | Sí                |
| **C**  | Cargo Administrativo                          | No                |
| **E**  | Extensión                                     | Sí                |
| **P**  | Abono de Matrícula                            | Sí                |
| **F**  | Inscripción y Abono                           | Sí                |
| **A**  | Alojamiento                                   | No                |
| **S**  | Seguro                                        | No                |

---

### 2. **PaymentStructure** (Estructura de Pago)

Define la estructura de campos dinámicos para cada tipo de pago.

**Tabla:** `payment_structure`

```python
class PaymentStructure(models.Model):
    payment_type = models.ForeignKey('PaymentType', ...)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    has_discount = models.BooleanField(default=False)
    choices = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Método `to_json()`:**
Retorna un JSON estructurado con la información de la estructura y sus campos dinámicos.

---

### 3. **PaymentStructureFields** (Campos de Estructura)

Define los campos dinámicos que puede tener cada estructura de pago.

**Tabla:** `payment_structure_section`

```python
class PaymentStructureFields(models.Model):
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('hidden', 'Oculto'),
        ('div', 'Div'),
        ('number', 'Número'),
        ('select', 'Select'),
        ('readonly', 'Solo Lectura'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
    ]
    
    payment_structure = models.ForeignKey('PaymentStructure', ...)
    name = models.CharField(max_length=50)                  # Ej: "precio", "descuento_pct"
    label = models.CharField(max_length=100)                # Ej: "Precio", "Descuento (%)"
    field_type = models.CharField(max_length=20, ...)
    choices = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=True)
    readonly = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    default_value = models.CharField(max_length=100, ...)
    active = models.BooleanField(default=True)
```

---

### 4. **PaymentOrder** (Orden de Pago) ⭐ MODELO PRINCIPAL

Representa una orden de pago completa.

**Tabla:** `payment_order`

```python
class PaymentOrder(Modelo):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de pago'),
        ('PAID', 'Pagado'),
        ('VERIFIED', 'Verificado por Tesorería'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    order_number = models.CharField(max_length=10, unique=True)         # Ej: OP202400001
    student = models.ForeignKey('administrador.Usuarios', ...)          # Estudiante
    advisor = models.ForeignKey('administrador.Usuarios', ...)          # Asesor que creó
    opportunity = models.ForeignKey('crm.Oportunidades', ...)           # Oportunidad CRM
    quotation = models.ForeignKey('website.Cotizaciones', ...)          # Cotización
    status = models.CharField(max_length=20, default='PENDING')
    payment_link_date = models.DateField(...)                           # Fecha de envío del enlace
    payment_types = models.ManyToManyField('PaymentType', through='PaymentOrderDetails')
    total_order = models.DecimalField(max_digits=10, decimal_places=2)
    payment_order_file = models.FileField(...)                          # PDF generado
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Propiedades:**

```python
@property
def calculated_total(self):
    """Suma todos los sub_total de los detalles"""
    return self.payment_order_details.aggregate(
        sub_total=models.Sum('sub_total')
    )['sub_total'] or Decimal('0.00')
```

**Métodos de Estado:**

```python
def cancel(self) -> bool:
    """Cancela la orden (solo si está en PENDING)"""
    
def mark_as_paid(self) -> bool:
    """Marca como pagada (solo si está en PENDING)"""
    
def verify(self) -> bool:
    """Verifica la orden (solo si está en PAID)"""
    
def can_be_updated(self) -> bool:
    """Verifica si la orden puede ser actualizada (solo PENDING)"""
```

**Método Principal:**

```python
def get_order_structure(self, another_program=None):
    """
    Retorna un dict con la estructura completa de la orden:
    - Datos del estudiante
    - Datos del programa
    - Conceptos a facturar (tipos de pago con sus montos)
    """
```

---

### 5. **PaymentOrderDetails** (Detalles de la Orden)

Representa cada concepto de pago dentro de una orden.

**Tabla:** `payment_order_details`

```python
class PaymentOrderDetails(Modelo):
    DISCOUNT_TYPE = (
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto Fijo'),
    )
    
    payment_order = models.ForeignKey('PaymentOrder', ...)
    payment_type = models.ForeignKey('PaymentType', ...)
    type_administrative_cost = models.ForeignKey(TipoCosto, ...)        # Tipo de cargo administrativo
    discount_type = models.CharField(max_length=10, ...)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)       # Monto neto
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)    # Monto total después de descuento
```

**Métodos:**

```python
def calculate_amount(self):
    """Calcula el amount automáticamente si el tipo requiere datos del programa"""

def get_applied_discount(self):
    """Calcula el descuento aplicado según el tipo"""

@property
def calculate_total(self):
    """Calcula el total (amount - descuento)"""
```

**Cálculo de Descuentos:**

- **Porcentual:** `sub_total = amount - (amount * discount_amount / 100)`
- **Fijo:** `sub_total = amount - discount_amount`

---

### 6. **PaymentOrderProgram** (Programa de la Orden)

Información del programa educativo asociado a la orden de pago.

**Tabla:** `payment_order_program`

```python
class PaymentOrderProgram(Modelo):
    DURATION_TYPE = (
        ('A', 'Año(s)'), 
        ('S', 'Semestres'), 
        ('w', 'Semanas')
    )
    
    payment_order = models.OneToOneField(PaymentOrder, ...)
    program_type = models.ForeignKey(Categorias, ...)                   # Tipo de programa
    institution = models.ForeignKey(Institucion, ...)                   # Institución
    country = models.ForeignKey(Paises, ...)                            # País
    city = models.ForeignKey(Ciudades, ...)                             # Ciudad
    program = models.ForeignKey(Cursos, ...)                            # Curso/Programa
    intensity = models.ForeignKey(Intensidad, ...)                      # Intensidad
    another_program = models.CharField(max_length=255, ...)             # Otro programa (texto libre)
    start_date = models.DateField(...)                                  # Fecha de inicio
    end_date = models.DateField(...)                                    # Fecha de fin
    duration = models.IntegerField(default=0)                           # Duración
    duration_type = models.CharField(max_length=1, ...)
    price_week = models.DecimalField(max_digits=10, decimal_places=2)   # Precio por semana
    material_cost = models.DecimalField(max_digits=10, decimal_places=2)
    material_cost_type = models.ForeignKey('instituciones.TiposCostoMaterial', ...)
```

**Propiedades calculadas:**

```python
@property
def tuition_subtotal(self):
    """Calcula: price_week * duration"""
    return (Decimal(self.price_week) * Decimal(self.duration)).quantize(Decimal('0.01'))

@property
def total_material(self):
    """Retorna el costo de material"""
    return Decimal(self.material_cost).quantize(Decimal('0.01'))

@property
def total_enrollment(self):
    """Calcula: tuition_subtotal + total_material"""
    return (self.tuition_subtotal + self.total_material).quantize(Decimal('0.01'))
```

**Validaciones:**

- Programas de **idiomas** deben tener duración en **semanas**
- **Maestrías** deben tener duración en **semestres** o **años**

---

## 🔄 FLUJO COMPLETO DE UNA ORDEN DE PAGO

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREACIÓN DE LA ORDEN                                     │
│    • Frontend envía datos de la orden                       │
│    • Se genera número de orden automático (OP202400001)     │
│    • Se calculan totales con descuentos                     │
│    • Estado inicial: PENDING                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ENVÍO DE ENLACE DE PAGO (Opcional)                       │
│    • Se genera PDF con detalle de la orden                  │
│    • Se envía correo al estudiante con enlace               │
│    • Se envía copia al asesor                               │
│    • Se actualiza payment_link_date                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ESTUDIANTE PAGA                                          │
│    • Estudiante accede al enlace de pago                    │
│    • Recupera/crea contraseña desde la website              │
│    • Realiza el pago online                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CONFIRMACIÓN DE PAGO                                     │
│    • Sistema de pagos confirma transacción                  │
│    • Estado cambia a: PAID                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. VERIFICACIÓN POR TESORERÍA                               │
│    • Tesorería revisa el pago                               │
│    • Estado cambia a: VERIFIED                              │
└─────────────────────────────────────────────────────────────┘
```

**Estados posibles:**

```
PENDING → PAID → VERIFIED
   ↓
CANCELLED (solo desde PENDING)
```

---

## 🚀 ENDPOINTS DE LA API

**Base URL:** `/api/v1/payment-orders/`

### 1. Listar Órdenes de Pago

```http
GET /api/v1/payment-orders/
```

**Query Parameters:**

- `page` - Número de página (default: 1)
- `per_page` - Items por página (default: 10)
- `status` - Filtrar por estado
- `student_id` - Filtrar por estudiante
- `advisor_id` - Filtrar por asesor
- `opportunity_id` - Filtrar por oportunidad
- `quotation_id` - Filtrar por cotización
- `date_from` - Filtrar desde fecha (YYYY-MM-DD)
- `date_to` - Filtrar hasta fecha (YYYY-MM-DD)

**Respuesta:**

```json
{
  "count": 50,
  "next": "http://api/v1/payment-orders/?page=2",
  "previous": null,
  "results": [...]
}
```

---

### 2. Crear Orden de Pago

```http
POST /api/v1/payment-orders/
```

**Body:**

```json
{
  "student_id": 123,
  "advisor_id": 5,
  "opportunity_id": 50,
  "quotation_id": 20,
  "payment_details": [
    {
      "payment_type_id": 1,
      "type_administrative_cost_id": 3,
      "amount": 1000.00,
      "discount_type": "percentage",
      "discount_amount": 10.00
    }
  ],
  "payment_program": {
    "program_type_id": 1,
    "institution_id": 10,
    "country_id": 5,
    "city_id": 15,
    "program_id": 25,
    "intensity_id": 2,
    "start_date": "2025-01-15",
    "end_date": "2025-04-15",
    "duration": 12,
    "duration_type": "w",
    "price_week": 250.00,
    "material_cost": 100.00,
    "material_cost_type_id": 1
  }
}
```

**Respuesta:** `201 Created`

---

### 3. Crear y Enviar Enlace ⭐ RECOMENDADO

```http
POST /api/v1/payment-orders/create-and-send/
```

Crea o actualiza una orden y envía el enlace de pago en una sola llamada.

**Body:**

```json
{
  "order_id": null,          // null = crear, ID = actualizar
  "order_data": {
    "student_id": 123,
    "advisor_id": 5,
    "payment_details": [...],
    "payment_program": {...}
  }
}
```

**Respuesta:** `201 Created` o `200 OK`

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "message": "Orden creada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123-def456",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com",
  "status": "PENDING",
  "total_order": "3500.00"
}
```

---

### 4. Obtener Orden por ID

```http
GET /api/v1/payment-orders/{id}/
```

---

### 5. Obtener Orden por Número

```http
GET /api/v1/payment-orders/by-number/OP202400001/
```

---

### 6. Actualizar Orden

```http
PUT /api/v1/payment-orders/{id}/
```

**Query Parameter (opcional):**

- `send_payment_link=true` - Enviar enlace automáticamente

**Body:** (Igual que CREATE, pero todos los campos son opcionales)

---

### 7. Enviar Enlace de Pago

```http
POST /api/v1/payment-orders/{id}/send-payment-link/
```

**Body:** `{}` (vacío)

**Respuesta:**

```json
{
  "message": "El enlace de pago para la orden OP202400001 está siendo enviado.",
  "order_number": "OP202400001",
  "task_id": "abc123-def456",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com"
}
```

---

### 8. Cambiar Estado de Orden

```http
POST /api/v1/payment-orders/{id}/change-status/
```

**Body:**

```json
{
  "new_status": "PAID"
}
```

**Valores válidos:** `PAID`, `VERIFIED`, `CANCELLED`

---

### 9. Marcar como Pagada

```http
POST /api/v1/payment-orders/{id}/mark-as-paid/
```

---

### 10. Cancelar Orden

```http
POST /api/v1/payment-orders/{id}/cancel/
```

---

### 11. Verificar Orden

```http
POST /api/v1/payment-orders/{id}/verify/
```

---

### 12. Obtener Estructura de Orden

```http
GET /api/v1/payment-orders/{id}/structure/
```

Retorna un JSON detallado con toda la estructura de la orden.

---

### 13. Eliminar Orden (Soft Delete)

```http
DELETE /api/v1/payment-orders/{id}/
```

Nota: No elimina físicamente, cambia el estado a CANCELLED.

---

## 📧 SISTEMA DE ENVÍO DE ENLACES DE PAGO

### Tarea Celery: `enviar_enlace_pago_orden`

**Archivo:** `apps/orden_pagos/tasks.py`

```python
@shared_task
def enviar_enlace_pago_orden(order_id, base_url=None):
    """
    Envía el enlace de pago al estudiante y asesor.
    Proceso asíncrono que:
    1. Genera PDF de la orden
    2. Envía correo al estudiante
    3. Envía correo al asesor
    4. Actualiza payment_link_date
    """
```

**Características:**

- ✅ Proceso asíncrono (no bloquea)
- ✅ Validación de estado PENDING
- ✅ Generación automática de PDF
- ✅ Envío de correos con PDF adjunto
- ✅ Actualización automática de `payment_link_date`
- ✅ Manejo robusto de errores con logging
- ✅ Retorna task_id para seguimiento

---

### Plantillas HTML

#### 1. Correo Electrónico

**Archivo:** `apps/orden_pagos/templates/correo-enlace-pago-orden.html`

Contiene:

- Saludo personalizado
- Número de orden
- Monto total
- Botón de pago
- Nota sobre recuperación de contraseña

#### 2. PDF de Orden

**Archivo:** `apps/orden_pagos/templates/pdf_orden_pago.html`

Contiene:

- Logo de LC Mundo
- Información del estudiante
- Información del programa
- Tabla de conceptos de pago
- Descuentos aplicados
- Total a pagar

---

## 💻 EJEMPLOS DE USO DESDE FRONTEND

### React/Next.js

```javascript
async function crearYEnviarOrden(orderData) {
  const response = await fetch('/api/v1/payment-orders/create-and-send/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      order_id: null,  // null = crear nueva
      order_data: orderData
    })
  });
  
  const result = await response.json();
  console.log('Orden creada:', result.order_number);
  console.log('Enlace enviado a:', result.student_email);
}
```

### Vue.js

```javascript
async crearYEnviarOrden(orderData) {
  try {
    const response = await this.$http.post(
      '/api/v1/payment-orders/create-and-send/',
      {
        order_id: null,
        order_data: orderData
      }
    );
    
    this.$toast.success(`Orden ${response.data.order_number} creada y enviada`);
  } catch (error) {
    this.$toast.error('Error al procesar la orden');
  }
}
```

---

## 🔐 SEGURIDAD

### Sin Contraseñas Temporales

El sistema **NO envía contraseñas temporales** por correo. En su lugar:

1. El estudiante recibe el **enlace de pago**
2. Al hacer clic, es redirigido a la **website**
3. Si es primera vez, puede **crear su contraseña**
4. Si ya tiene cuenta, hace **login normal**
5. Si olvidó su contraseña, puede **recuperarla** desde la website

**Ventajas:**

- ✅ Mayor seguridad
- ✅ Menos fricción para el usuario
- ✅ Cumplimiento de buenas prácticas de seguridad

---

## ⚙️ CONFIGURACIÓN REQUERIDA

### 1. Settings de Django

```python
# settings.py

# Celery (para tareas asíncronas)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@example.com'
EMAIL_HOST_PASSWORD = 'tu_password'

# WeasyPrint (para generar PDFs)
# Asegúrate de tener instalado WeasyPrint y sus dependencias
```

### 2. Requirements

```txt
celery==5.3.4
redis==5.0.1
weasyprint==60.1
django-rest-framework==3.14.0
```

### 3. Celery Worker

Para que el envío de correos funcione, debe estar corriendo el worker de Celery:

```bash
celery -A api worker -l info
```

---

## 📊 REGLAS DE NEGOCIO

### Tipos de Pago y Programas

| Código | Tipo de Pago                | Requiere Programa | Requiere Cargo Admin |
|--------|-----------------------------|-------------------|----------------------|
| I      | Inscripción                 | ✅                 | ❌                    |
| M      | Matrícula                   | ✅                 | ❌                    |
| B      | Inscripción + Matrícula     | ✅                 | ❌                    |
| T      | Insc. + Matr. + Cargo Admin | ✅                 | ✅                    |
| C      | Cargo Administrativo        | ❌                 | ✅                    |
| E      | Extensión                   | ✅                 | ❌                    |
| P      | Abono de Matrícula          | ✅                 | ❌                    |
| F      | Inscripción + Abono         | ✅                 | ❌                    |

### Transiciones de Estado

```
PENDING:
  ├─→ PAID (mark_as_paid)
  └─→ CANCELLED (cancel)

PAID:
  └─→ VERIFIED (verify)

VERIFIED:
  └─→ [FINAL STATE]

CANCELLED:
  └─→ [FINAL STATE]
```

### Cálculos Automáticos

#### Detalles de Orden (PaymentOrderDetails)

```python
# Para tipos que dependen del programa (I, M, B, T, E, etc.)
amount = program.total_enrollment  # tuition_subtotal + total_material

# Para otros tipos (C, A, S, etc.)
amount = valor_ingresado_manualmente
```

#### Descuentos

```python
# Descuento porcentual
descuento = amount * (discount_amount / 100)
sub_total = amount - descuento

# Descuento fijo
sub_total = amount - discount_amount
```

#### Total de la Orden

```python
total_order = sum(detail.sub_total for detail in payment_order_details)
```

### Validaciones

1. ✅ Solo se pueden actualizar órdenes en estado **PENDING**
2. ✅ Solo se pueden cancelar órdenes en estado **PENDING**
3. ✅ Solo se pueden marcar como pagadas órdenes en estado **PENDING**
4. ✅ Solo se pueden verificar órdenes en estado **PAID**
5. ✅ Solo se pueden enviar enlaces a órdenes en estado **PENDING**
6. ✅ Programas de idiomas deben tener duración en **semanas**
7. ✅ Maestrías deben tener duración en **semestres** o **años**
8. ✅ El número de orden se genera automáticamente y es **único**

---

## 🧪 TESTING

### Casos de Prueba Importantes

1. **Creación de Orden**
    - ✅ Con programa
    - ✅ Sin programa (solo cargo administrativo)
    - ✅ Con múltiples conceptos de pago
    - ✅ Con descuentos porcentuales
    - ✅ Con descuentos fijos

2. **Cambios de Estado**
    - ✅ PENDING → PAID
    - ✅ PAID → VERIFIED
    - ✅ PENDING → CANCELLED
    - ❌ PAID → CANCELLED (debe fallar)
    - ❌ VERIFIED → cualquier otro (debe fallar)

3. **Actualización de Orden**
    - ✅ Actualizar detalles en PENDING
    - ❌ Actualizar detalles en PAID (debe fallar)
    - ✅ Recálculo automático de totales

4. **Envío de Enlaces**
    - ✅ Envío en creación
    - ✅ Envío en actualización
    - ✅ Reenvío de enlace
    - ❌ Envío con estado != PENDING (debe fallar)

---

## 📚 DOCUMENTACIÓN ADICIONAL

Consulta estos archivos para más información:

1. **API Completa:** `docs/PAYMENT_ORDERS_API_DOCUMENTATION.md`
2. **Envío de Enlaces:** `docs/IMPLEMENTACION_COMPLETADA_ENLACE_PAGO.md`
3. **Guía Frontend:** `docs/GUIA_FRONTEND_ENVIO_ENLACE.md`
4. **Ejemplos de Uso:** `docs/EJEMPLO_USO_ENVIO_ENLACE_PAGO.md`
5. **Contexto Envío:** `context/CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md`

---

## 🎯 PRÓXIMOS PASOS / TODOs

- [ ] Implementar webhook para notificación de pagos completados
- [ ] Agregar soporte para pagos parciales
- [ ] Implementar recordatorios automáticos de pago
- [ ] Agregar dashboard de estadísticas de órdenes
- [ ] Implementar exportación de reportes en Excel
- [ ] Agregar notificaciones push al cambiar estados
- [ ] Implementar sistema de plantillas de correo personalizables
- [ ] Agregar multi-moneda para pagos internacionales

---

## 👥 RESPONSABLES

**Backend:** Equipo de Desarrollo API  
**Frontend:** Equipo de Desarrollo Web  
**QA:** Equipo de Testing  
**DevOps:** Equipo de Infraestructura

---

## 📝 NOTAS FINALES

Este documento proporciona una visión completa del sistema de órdenes de pago. Para implementar nuevas funcionalidades:

1. **Lee primero** toda la documentación en `docs/` y `context/`
2. **Respeta** la arquitectura Clean Architecture + DDD
3. **Mantén** la separación de capas (Domain, Application, Infrastructure, Presentation)
4. **Documenta** cualquier cambio importante
5. **Escribe tests** para nuevas funcionalidades

---

**Última actualización:** 28 de Noviembre de 2025  
**Versión:** 1.0.0  
**Estado:** Completado y Funcional ✅

