# ⚠️ ACLARACIÓN: Django Ninja + DRF Híbrido

## Pregunta del Usuario

**¿No se necesita `rest_framework`? ¿Solo se usa para las rutas?**

## Respuesta

**SÍ se necesita `rest_framework`**, pero **NO para las rutas**. El proyecto usa un enfoque **híbrido**:

---

## 🔀 Arquitectura Híbrida

### Django Ninja (Principal)
**Uso:** Endpoints de la API pública

```python
# apps/orden_pagos/presentation/api/routers/router.py
from ninja import Router

router = Router()

@router.get("/")  # ← Endpoint de Django Ninja
def list_payment_orders(request):
    # ...
```

### Django REST Framework (Legacy/Utilities)
**Uso:** Utilidades y código legacy en `infrastructure/`

```python
# 1. ValidationError
from rest_framework.exceptions import ValidationError

def validate_payment(data):
    if not data:
        raise ValidationError("Invalid data")  # ← Usa DRF

# 2. Serializers Legacy (en infrastructure/)
from rest_framework import serializers

class PaymentOrderSerializer(serializers.ModelSerializer):  # ← Legacy
    class Meta:
        model = PaymentOrder
        fields = '__all__'
```

---

## 📊 Dónde se Usa Cada Uno

### Django Ninja → `presentation/api/`
```
apps/orden_pagos/presentation/api/
├── routers/           ✅ Endpoints con Django Ninja
│   └── router.py
└── schemas/           ✅ Pydantic schemas
    └── input_schemas.py
```

**Ejemplos:**
- ✅ Rutas/endpoints públicos
- ✅ Documentación OpenAPI/Swagger
- ✅ Validación con Pydantic
- ✅ Type hints nativos

### Django REST Framework → `infrastructure/`
```
apps/orden_pagos/infrastructure/
└── serializers/       ⚠️ Serializers legacy de DRF
    ├── payment_order_serializer.py
    ├── payment_structure.py
    └── payment_structure_field.py
```

**Ejemplos:**
- ⚠️ `ValidationError` en toda la app
- ⚠️ Serializers en `infrastructure/serializers/`
- ⚠️ Algunos decoradores legacy

---

## 🎯 ¿Por Qué Esta Mezcla?

### Razón 1: Migración Gradual
El proyecto original migró de DRF a Django Ninja, pero quedó código legacy:

```python
# VIEJO (DRF) - todavía existe en infrastructure/
class PaymentOrderSerializer(serializers.ModelSerializer):
    # ...

# NUEVO (Django Ninja) - en presentation/api/
class PaymentOrderSchema(Schema):
    # ...
```

### Razón 2: ValidationError
`ValidationError` de DRF se usa mucho en el código:

```python
# apps/orden_pagos/tasks.py
from rest_framework.exceptions import ValidationError  # ← Muy usado

def validate_token(token):
    if not token:
        raise ValidationError("Token required")
```

**Alternativa Django Ninja:**
```python
from ninja.errors import HttpError

def validate_token(token):
    if not token:
        raise HttpError(400, "Token required")  # ← Mejor
```

### Razón 3: Serializers en Infrastructure
Algunos serializers se usan internamente:

```python
# infrastructure/serializers/payment_order_serializer.py
from rest_framework import serializers

class PaymentOrderSerializer(serializers.ModelSerializer):
    # Usado internamente para conversiones
    # NO para endpoints
```

---

## ✅ Recomendaciones

### 1. Mantener Ambos (Por Ahora)

```python
# requirements.txt
django-ninja==1.1.0          # Para endpoints
djangorestframework==3.14.0  # Para ValidationError y serializers legacy
```

**Razón:** El código copiado los usa ambos.

### 2. Usar Django Ninja para Nuevos Endpoints

```python
# ✅ HACER: Nuevos endpoints
from ninja import Router

@router.post("/")
def create_order(request, data: CreateOrderSchema):
    # ...

# ❌ EVITAR: Nuevos ViewSets de DRF
class OrderViewSet(viewsets.ModelViewSet):  # No hacer esto
    # ...
```

### 3. Reemplazar ValidationError Gradualmente

```python
# 🔄 MIGRAR DE:
from rest_framework.exceptions import ValidationError
raise ValidationError("Error")

# 🔄 MIGRAR A:
from ninja.errors import HttpError
raise HttpError(400, "Error")
```

### 4. Los Serializers en Infrastructure Están OK

Los serializers en `infrastructure/serializers/` son parte de la capa de infraestructura y están OK:

```
infrastructure/
└── serializers/        ← OK aquí (conversión ORM ↔ DTO)
    └── *.py
```

Pero **NO crear nuevos ViewSets** en `presentation/`.

---

## 🗂️ Estructura Correcta

```
apps/orden_pagos/
│
├── presentation/               # Capa de presentación
│   └── api/                   # API REST
│       ├── routers/           ✅ Django Ninja routers
│       └── schemas/           ✅ Pydantic schemas
│
├── application/               # Casos de uso
│   └── use_cases/            ✅ Usan ValidationError de DRF
│
├── infrastructure/            # Infraestructura
│   ├── repositories/         ✅ Pure Python
│   └── serializers/          ⚠️ DRF serializers (legacy pero OK)
│
└── domain/                    # Dominio
    └── entities/             ✅ Pure Python
```

---

## 💡 Respuesta Directa

### ¿Se necesita `rest_framework`?
**SÍ**, porque:
1. ✅ `ValidationError` se usa en 20+ archivos
2. ✅ Serializers en `infrastructure/serializers/`
3. ✅ Algunas utilidades internas

### ¿Solo se usa para rutas?
**NO**, las rutas usan **Django Ninja**.

`rest_framework` se usa para:
- Excepciones (`ValidationError`)
- Serializers legacy en infrastructure
- Utilidades internas

---

## 🔧 Configuración Final

### requirements.txt
```txt
django-ninja==1.1.0              # ← Para API endpoints
djangorestframework==3.14.0      # ← Para ValidationError + serializers
```

### settings.py
```python
INSTALLED_APPS = [
    'ninja',            # ← Para routers en presentation/
    'rest_framework',   # ← Para ValidationError + serializers
    # ...
]
```

### urls.py
```python
from ninja import NinjaAPI

api = NinjaAPI()  # ← Solo Django Ninja para rutas

# rest_framework NO se usa para routing
```

---

## 📝 Conclusión

El proyecto usa **arquitectura híbrida**:

- **Django Ninja**: Endpoints modernos (routers + schemas)
- **DRF**: Utilidades internas (ValidationError + serializers legacy)

**NO es redundancia**, es una **migración gradual** de DRF → Django Ninja donde:
- ✅ Frontend nuevo usa Django Ninja
- ⚠️ Backend interno todavía usa algunas utilidades de DRF
- 🎯 Ambos son necesarios (por ahora)

---

## 🚀 Plan de Limpieza Futura (Opcional)

Si quieres eliminar DRF completamente:

1. **Reemplazar ValidationError**
   ```python
   # Buscar: from rest_framework.exceptions import ValidationError
   # Reemplazar: from ninja.errors import HttpError
   ```

2. **Migrar Serializers**
   ```python
   # Serializers DRF → Pydantic Schemas
   ```

3. **Eliminar DRF**
   ```bash
   pip uninstall djangorestframework
   ```

Pero por ahora, **déjalo así** porque el código lo necesita.

---

**TL;DR**: Sí se necesita `rest_framework`, pero NO para rutas. Se usa para `ValidationError` y serializers internos. Las rutas usan Django Ninja.

