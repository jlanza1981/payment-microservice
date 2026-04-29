# Refactorización del Servicio de Historial de Pagos

## 📁 Estructura de Archivos

### Nuevos archivos creados:

```
apps/pagos/
├── domain/
│   └── interface/
│       └── services/
│           ├── file_storage_service_interface.py       # ✅ NUEVO
│           └── pdf_generator_service_interface.py      # ✅ NUEVO
│
├── application/
│   ├── dto/
│   │   └── student_payment_dto.py                      # ✏️ MODIFICADO (inmutable)
│   ├── services/
│   │   ├── payment_history_service.py                  # ✏️ REFACTORIZADO
│   │   └── payment_pdf_service.py                      # ✅ NUEVO
│   └── dependencies.py                                 # ✅ NUEVO
│
└── infrastructure/
    └── services/
        ├── local_file_storage_service.py               # ✅ NUEVO
        └── celery_pdf_generator_service.py             # ✅ NUEVO
```

---

## 🎯 Cambios Principales

### 1. **Separación de Responsabilidades**

**ANTES:**
```python
# Un solo servicio hacía todo
class PaymentHistoryService:
    def get_student_payments(..., request=None):
        # Obtener pagos
        # Verificar archivos
        # Generar PDFs
        # Mutar DTOs
```

**DESPUÉS:**
```python
# Servicio enfocado en historial
class PaymentHistoryService:
    def get_student_payments(..., base_url: str):
        # Solo obtiene y combina pagos
        # Delega PDFs a otro servicio

# Servicio especializado en PDFs
class PaymentPDFService:
    def ensure_payment_pdfs_exist(...):
        # Solo gestiona PDFs
```

---

### 2. **DTOs Inmutables**

**ANTES:**
```python
@dataclass
class StudentPaymentDTO:
    # ... campos
    
# Mutación directa ❌
payment.file = new_path
```

**DESPUÉS:**
```python
@dataclass(frozen=True)  # ✅ Inmutable
class StudentPaymentDTO:
    # ... campos

# Crear nuevo DTO ✅
updated_payment = replace(payment, file=new_path)
```

---

### 3. **Inversión de Dependencias (DIP)**

**ANTES:**
```python
from api import settings  # ❌ Dependencia directa
from pathlib import Path
from apps.billing.tasks import save_pdf_payment_task  # ❌ Celery

file_path = Path(settings.MEDIA_ROOT) / str(payment.file)
```

**DESPUÉS:**
```python
# Inyección de dependencias ✅
def __init__(
    self,
    file_storage_service: FileStorageServiceInterface,
    pdf_generator_service: PDFGeneratorServiceInterface
):
    # Depende de abstracciones, no de implementaciones
```

---

### 4. **Eliminación de Acoplamiento HTTP**

**ANTES:**
```python
def get_student_payments(..., request=None):  # ❌ Objeto HTTP
    base_url = request.build_absolute_uri()
```

**DESPUÉS:**
```python
def get_student_payments(..., base_url: str):  # ✅ String simple
    # Agnóstico del protocolo de transporte
```

---

## 🔄 Migración del Código Existente

### En las vistas/controladores:

**ANTES:**
```python
# views.py
from apps.pagos.application.services.payment_history_service import PaymentHistoryService
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.infrastructure.repository.legacy_payment_repository import LegacyPaymentRepository

def get_payment_history(request, student_id):
    payment_repo = PaymentRepository()
    legacy_repo = LegacyPaymentRepository()
    
    service = PaymentHistoryService(payment_repo, legacy_repo)
    
    # ❌ Pasando request
    payments = service.get_student_payments(student_id, request=request)
    
    return payments
```

**DESPUÉS:**
```python
# views.py
from apps.pagos.application.dependencies import get_payment_history_service

def get_payment_history(request, student_id):
    # ✅ Inyección de dependencias centralizada
    service = get_payment_history_service()
    
    # ✅ Solo pasamos la URL base
    base_url = request.build_absolute_uri('/')
    
    payments = service.get_student_payments(
        student_id=student_id,
        base_url=base_url,
        ensure_pdfs=True  # ✅ Explícito
    )
    
    return payments
```

---

## 🌐 ¿Cómo obtener base_url?

### ¿Qué es base_url?

`base_url` es la **URL HTTP completa** del dominio, necesaria para que WeasyPrint pueda resolver recursos estáticos (CSS, imágenes) al generar PDFs.

**Ejemplos válidos:**
- ✅ `https://example.com`
- ✅ `http://localhost:8000`
- ✅ `https://api.tudominio.com`

**NO válidos:**
- ❌ `/home/user/project` (es un path, no una URL)
- ❌ `example.com` (falta protocolo http:// o https://)

### En Vistas DRF (con request HTTP)

```python
from rest_framework.decorators import api_view

@api_view(['GET'])
def my_view(request):
    # Construir desde el request actual
    base_url = request.build_absolute_uri('/')[:-1]
    # Resultado: https://example.com (sin trailing slash)
    
    service = get_payment_history_service()
    payments = service.get_student_payments(
        student_id=123,
        base_url=base_url
    )
```

### En Celery Tasks (sin request HTTP)

```python
from celery import shared_task
from django.conf import settings

@shared_task
def my_task():
    # Usar configuración de settings
    base_url = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)
    
    service = get_payment_history_service()
    payments = service.get_student_payments(
        student_id=123,
        base_url=base_url
    )
```

### En Management Commands (sin request HTTP)

```python
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Usar configuración de settings
        base_url = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)
        
        service = get_payment_history_service()
        payments = service.get_student_payments(
            student_id=123,
            base_url=base_url
        )
```

### Configuración en settings.py

Ya está configurado en `api/settings.py`:

```python
# URL base para generación de PDFs
BASE_URL = config('BASE_URL', default=DOMAIN_NAME)
```

### Configuración en .env

```bash
# Desarrollo
BASE_URL=http://localhost:8000

# Producción
BASE_URL=https://tudominio.com
```

Si no defines `BASE_URL`, se usará `DOMAIN_NAME` como fallback.

---

## 📝 Uso del Nuevo Servicio

### Ejemplo 1: Obtener historial con PDFs

```python
from apps.pagos.application.dependencies import get_payment_history_service

service = get_payment_history_service()

payments = service.get_student_payments(
    student_id=123,
    base_url="https://example.com",
    ensure_pdfs=True  # Verifica/regenera PDFs
)
```

### Ejemplo 2: Obtener historial sin verificar PDFs

```python
payments = service.get_student_payments(
    student_id=123,
    ensure_pdfs=False  # Más rápido, no toca archivos
)
```

### Ejemplo 3: Con filtros

```python
payments = service.get_student_payments(
    student_id=123,
    filters={
        'date_from': '2024-01-01',
        'date_to': '2024-12-31',
        'status': 'verified'
    },
    base_url="https://example.com",
    ensure_pdfs=True
)
```

---

## 🧪 Testing

### Ventajas de la nueva arquitectura para testing:

**ANTES:** Testing difícil, requiere Django/Celery
```python
# ❌ Difícil de testear
def test_payment_history():
    # Necesita settings de Django
    # Necesita Celery corriendo
    # Necesita filesystem real
```

**DESPUÉS:** Testing fácil con mocks
```python
# ✅ Fácil de testear
def test_payment_history():
    # Mock de repositorios
    mock_payment_repo = MagicMock(spec=PaymentRepositoryInterface)
    mock_legacy_repo = MagicMock(spec=PaymentRepositoryInterface)
    mock_pdf_service = MagicMock(spec=PaymentPDFService)
    
    # Servicio con dependencias mockeadas
    service = PaymentHistoryService(
        payment_repository=mock_payment_repo,
        legacy_payment_repository=mock_legacy_repo,
        payment_pdf_service=mock_pdf_service
    )
    
    # Test sin dependencias externas
    payments = service.get_student_payments(
        student_id=123,
        base_url="http://test.com",
        ensure_pdfs=False
    )
```

---

## ✅ Beneficios de la Refactorización

### 1. **Cumple con DDD**
- ✅ Capas bien separadas (domain, application, infrastructure)
- ✅ Dependencias apuntan hacia adentro (DIP)
- ✅ Sin dependencias de infraestructura en aplicación

### 2. **Cumple con SOLID**
- ✅ **SRP**: Cada servicio tiene una responsabilidad única
- ✅ **OCP**: Abierto a extensión (nuevas implementaciones de interfaces)
- ✅ **LSP**: Las interfaces pueden ser sustituidas
- ✅ **ISP**: Interfaces específicas y cohesivas
- ✅ **DIP**: Dependencia de abstracciones, no de implementaciones

### 3. **Clean Code**
- ✅ Nombres descriptivos
- ✅ Métodos pequeños y enfocados
- ✅ Sin flags booleanos
- ✅ Manejo de errores con logging
- ✅ Documentación clara (docstrings)
- ✅ Tipado completo

### 4. **Testeable**
- ✅ Fácil crear mocks de interfaces
- ✅ No requiere Django/Celery/Filesystem
- ✅ Tests unitarios rápidos

### 5. **Mantenible**
- ✅ Fácil entender responsabilidades
- ✅ Fácil cambiar implementaciones
- ✅ Fácil agregar nuevas funcionalidades

---

## 🔧 Configuración Adicional

### Para usar en otros contextos (CLI, Jobs, etc.):

```python
# management/commands/regenerate_pdfs.py
from django.core.management.base import BaseCommand
from apps.pagos.application.dependencies import get_payment_pdf_service

class Command(BaseCommand):
    def handle(self, *args, **options):
        pdf_service = get_payment_pdf_service()
        
        # Uso sin request HTTP ✅
        payments = [...]  # Obtener de algún lado
        
        updated_payments = pdf_service.ensure_payment_pdfs_exist(
            payments=payments,
            base_url="https://production.com"
        )
```

---

## 🚀 Próximos Pasos (Opcionales)

1. **Implementar alternativas de almacenamiento**
   - `S3FileStorageService` para AWS S3
   - `AzureBlobStorageService` para Azure

2. **Implementar alternativas de generación de PDF**
   - `SyncPDFGeneratorService` (sin Celery)
   - `WeasyPrintPDFGeneratorService` (motor alternativo)

3. **Agregar caché**
   - Cache de DTOs de pagos
   - Cache de PDFs generados

4. **Agregar eventos de dominio**
   - `PaymentPDFRegenerated`
   - `PaymentHistoryRequested`

---

## 📞 Soporte

Si tienes dudas sobre la migración o el uso de los nuevos servicios, revisa:
1. Los docstrings de cada clase/método
2. Los tests unitarios (próximamente)
3. Este documento

---

**Fecha de refactorización:** Marzo 2026  
**Versión:** 2.0  
**Arquitectura:** Hexagonal / DDD  
**Principios:** SOLID, Clean Code

