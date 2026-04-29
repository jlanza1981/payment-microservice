# Arquitectura del Sistema de Pagos - DDD y Clean Code

## 📐 Diagrama de Arquitectura Hexagonal

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PRESENTACIÓN                         │
│                  (Views, APIs, Controllers)                      │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  DRF Views  │  │   Celery    │  │  Commands   │             │
│  │             │  │    Tasks    │  │             │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
└─────────┼────────────────┼────────────────┼──────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                            │
│              (Application Services, Use Cases)                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │         PaymentHistoryService                         │       │
│  │  + get_student_payments()                            │       │
│  │  - _get_new_payments()                               │       │
│  │  - _get_legacy_payments()                            │       │
│  │  - _combine_and_sort_payments()                      │       │
│  └───────────────────┬──────────────────────────────────┘       │
│                      │                                           │
│                      │ usa                                       │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            PaymentPDFService                          │       │
│  │  + ensure_payment_pdfs_exist()                       │       │
│  │  - _ensure_single_payment_pdf()                      │       │
│  │  - _regenerate_payment_pdf()                         │       │
│  └──────────┬────────────────────────┬───────────────────┘       │
│             │                        │                           │
└─────────────┼────────────────────────┼───────────────────────────┘
              │                        │
              │ depende de             │ depende de
              │ (interfaces)           │ (interfaces)
              ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CAPA DE DOMINIO                            │
│                  (Interfaces, Entities, VOs)                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    PaymentRepositoryInterface (ABC)                │         │
│  │  + get_by_student()                                │         │
│  │  + get_by_id()                                     │         │
│  │  + create()                                        │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    FileStorageServiceInterface (ABC)               │         │
│  │  + exists()                                        │         │
│  │  + get_absolute_path()                             │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    PDFGeneratorServiceInterface (ABC)              │         │
│  │  + generate_payment_pdf()                          │         │
│  │  + generate_legacy_payment_pdf()                   │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    StudentPaymentDTO (immutable)                   │         │
│  │  - id, student_id, amount, date, source...         │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
└─────────────────────────┬────────────────┬──────────────────────┘
                          │                │
                          │ implementado   │ implementado
                          │ por            │ por
                          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CAPA DE INFRAESTRUCTURA                        │
│          (Implementaciones concretas, Adaptadores)               │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    PaymentRepository                               │         │
│  │  + get_by_student() → consulta DB nueva           │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    LegacyPaymentRepository                         │         │
│  │  + get_by_student() → consulta DB legacy          │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    LocalFileStorageService                         │         │
│  │  + exists() → verifica en filesystem              │         │
│  │  + get_absolute_path() → path completo            │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │    CeleryPDFGeneratorService                       │         │
│  │  + generate_payment_pdf() → Celery task           │         │
│  │  + generate_legacy_payment_pdf() → Celery task    │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Principios Aplicados

### 1. **Dependency Inversion Principle (DIP)**

```python
# ✅ CORRECTO: Depender de abstracciones
class PaymentPDFService:
    def __init__(
        self,
        file_storage: FileStorageServiceInterface,  # Interfaz
        pdf_generator: PDFGeneratorServiceInterface  # Interfaz
    ):
        self.file_storage = file_storage
        self.pdf_generator = pdf_generator

# ❌ INCORRECTO: Depender de implementaciones concretas
class PaymentPDFService:
    def __init__(self):
        from pathlib import Path  # Dependencia directa
        from api import settings  # Dependencia directa
```

### 2. **Single Responsibility Principle (SRP)**

Cada clase tiene una única razón para cambiar:

- **PaymentHistoryService**: Obtener y combinar pagos
- **PaymentPDFService**: Gestionar PDFs
- **LocalFileStorageService**: Operaciones de almacenamiento
- **CeleryPDFGeneratorService**: Generación de PDFs

### 3. **Open/Closed Principle (OCP)**

Abierto a extensión, cerrado a modificación:

```python
# Puedes crear nuevas implementaciones sin modificar código existente

class S3FileStorageService(FileStorageServiceInterface):
    """Nueva implementación para S3"""
    def exists(self, file_path: str) -> bool:
        # Implementación usando boto3
        pass

class WeasyPrintPDFGenerator(PDFGeneratorServiceInterface):
    """Nueva implementación con WeasyPrint"""
    def generate_payment_pdf(...):
        # Implementación con WeasyPrint
        pass
```

### 4. **Liskov Substitution Principle (LSP)**

Las implementaciones son intercambiables:

```python
# Puedes intercambiar implementaciones sin romper el código
service = PaymentPDFService(
    file_storage=S3FileStorageService(),  # O LocalFileStorageService()
    pdf_generator=WeasyPrintPDFGenerator()  # O CeleryPDFGeneratorService()
)
```

### 5. **Interface Segregation Principle (ISP)**

Interfaces específicas y cohesivas:

```python
# Interfaces pequeñas y específicas
class FileStorageServiceInterface(ABC):
    def exists(self, file_path: str) -> bool: pass
    def get_absolute_path(self, file_path: str) -> str: pass

# En lugar de una interfaz monolítica con 20 métodos
```

---

## 📦 Flujo de Datos

### Escenario: Obtener historial de pagos

```
1. [View/API]
   └─> request.build_absolute_uri() → base_url
   └─> get_payment_history_service() → service
   └─> service.get_student_payments(student_id, base_url)

2. [PaymentHistoryService]
   └─> payment_repository.get_by_student(student_id) → [Payment, ...]
   └─> legacy_repository.get_by_student(student_id) → [Payment, ...]
   └─> Combinar y ordenar pagos
   └─> payment_pdf_service.ensure_payment_pdfs_exist(payments)

3. [PaymentPDFService]
   └─> Para cada pago:
       ├─> file_storage.exists(payment.file) → bool
       │   └─> Si False:
       │       ├─> Preparar datos de factura
       │       └─> pdf_generator.generate_*_pdf() → new_path
       │       └─> replace(payment, file=new_path)
       └─> Retornar lista actualizada

4. [View/API]
   └─> Serializar pagos
   └─> Retornar Response
```

---

## 🔄 Flujo de Dependencias

```
Presentación → Aplicación → Dominio ← Infraestructura
    │              │            ▲            │
    │              │            │            │
    │              └────────────┴────────────┘
    │                   implementa
    │
    └─────────────────────────────────────────────────
            usa pero no depende directamente
```

**Regla de oro**: Las dependencias siempre apuntan hacia el dominio (centro).

---

## 🧪 Testabilidad

### Antes (difícil de testear):

```python
class PaymentHistoryService:
    def get_student_payments(self, student_id, request):
        # ❌ Depende de Django request
        # ❌ Depende de settings
        # ❌ Depende de Celery
        # ❌ Depende de filesystem
        file_path = Path(settings.MEDIA_ROOT) / str(payment.file)
        pdf_path = save_pdf_task.delay(...)
```

### Después (fácil de testear):

```python
# ✅ Mock de interfaces
mock_repo = MagicMock(spec=PaymentRepositoryInterface)
mock_pdf_service = MagicMock(spec=PaymentPDFService)

service = PaymentHistoryService(
    payment_repository=mock_repo,
    payment_pdf_service=mock_pdf_service
)

# Test sin dependencias externas
payments = service.get_student_payments(
    student_id=123,
    base_url="http://test.com"
)
```

---

## 📂 Estructura de Directorios

```
apps/pagos/
│
├── domain/                          # Capa de Dominio (núcleo)
│   ├── entities/                    # Entidades de negocio
│   ├── value_objects/               # Objetos de valor
│   └── interface/                   # Contratos (interfaces)
│       ├── repository/
│       │   └── payment_repository_interface.py
│       └── services/
│           ├── file_storage_service_interface.py
│           └── pdf_generator_service_interface.py
│
├── application/                     # Capa de Aplicación (casos de uso)
│   ├── dto/                         # Data Transfer Objects
│   │   └── student_payment_dto.py
│   ├── services/                    # Servicios de aplicación
│   │   ├── payment_history_service.py
│   │   └── payment_pdf_service.py
│   ├── commands/                    # Comandos (CQRS)
│   ├── queries/                     # Consultas (CQRS)
│   └── dependencies.py              # Inyección de dependencias
│
├── infrastructure/                  # Capa de Infraestructura (detalles)
│   ├── repository/                  # Implementaciones de repositorios
│   │   ├── payment_repository.py
│   │   └── legacy_payment_repository.py
│   └── services/                    # Implementaciones de servicios
│       ├── local_file_storage_service.py
│       └── celery_pdf_generator_service.py
│
└── presentation/                    # Capa de Presentación (opcional)
    ├── views/                       # Vistas Django
    ├── serializers/                 # Serializadores DRF
    └── urls.py                      # Rutas
```

---

## 🔑 Ventajas de esta Arquitectura

### 1. **Mantenibilidad**
- Código organizado por responsabilidades
- Fácil encontrar dónde hacer cambios
- Cambios aislados no afectan otras capas

### 2. **Testabilidad**
- Fácil crear mocks de interfaces
- Tests unitarios rápidos sin dependencias externas
- Mayor cobertura de código

### 3. **Flexibilidad**
- Fácil cambiar implementaciones (DB, filesystem, generador PDF)
- Puedes usar diferentes implementaciones en diferentes entornos
- Extensible sin modificar código existente

### 4. **Escalabilidad**
- Servicios desacoplados
- Fácil agregar nuevas funcionalidades
- Fácil optimizar partes específicas

### 5. **Claridad**
- Arquitectura autodocumentada
- Flujo de datos claro
- Separación de conceptos

---

## 🚀 Próximos Pasos

1. **Implementar más casos de uso**
   - Crear pagos
   - Verificar pagos
   - Cancelar pagos

2. **Agregar eventos de dominio**
   - `PaymentCreated`
   - `PaymentVerified`
   - `PDFRegenerated`

3. **Implementar CQRS**
   - Separar comandos de consultas
   - Optimizar queries de lectura

4. **Agregar más implementaciones**
   - S3 storage
   - Redis cache
   - Diferentes generadores de PDF

---

**Fecha:** Marzo 2026  
**Arquitectura:** Hexagonal / DDD  
**Principios:** SOLID, Clean Code, Separation of Concerns

