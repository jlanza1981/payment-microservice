# 🏗️ Arquitectura del Payment Microservice

## Visión General

Este microservicio sigue los principios de **Clean Architecture**, **Domain-Driven Design (DDD)** y **Arquitectura Hexagonal (Ports & Adapters)**.

## Capas de la Arquitectura

### 1. Presentation Layer (Capa de Presentación)

**Responsabilidad:** Manejar las peticiones HTTP y respuestas de la API REST.

**Componentes:**
- ViewSets (Django REST Framework)
- Serializers
- Routers
- Validators

**Ubicación:** `apps/*/presentation/`

**Ejemplo:**
```python
# apps/orden_pagos/presentation/views.py
class PaymentOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payment orders via API
    """
    serializer_class = PaymentOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        # Calls application layer use case
        use_case = CreatePaymentOrderUseCase()
        result = use_case.execute(request.data)
        return Response(result)
```

---

### 2. Application Layer (Capa de Aplicación)

**Responsabilidad:** Orquestar los casos de uso del negocio.

**Componentes:**
- Use Cases (Casos de Uso)
- DTOs (Data Transfer Objects)
- Application Services
- Command/Query handlers

**Ubicación:** `apps/*/application/`

**Características:**
- No contiene lógica de negocio (esa está en Domain)
- Coordina entre Domain y Infrastructure
- Transforma datos entre capas
- Maneja transacciones

**Ejemplo:**
```python
# apps/orden_pagos/application/use_cases/create_payment_order.py
class CreatePaymentOrderUseCase:
    """
    Create a new payment order with details and program
    """
    
    def __init__(self):
        self.repository = PaymentOrderRepository()
        self.notification_service = EmailNotificationService()
    
    def execute(self, data: dict) -> PaymentOrder:
        # 1. Validate input
        validated_data = self._validate(data)
        
        # 2. Create domain entity
        payment_order = PaymentOrder.create(validated_data)
        
        # 3. Save using repository
        saved_order = self.repository.save(payment_order)
        
        # 4. Send notification
        self.notification_service.send_payment_link(saved_order)
        
        return saved_order
```

---

### 3. Domain Layer (Capa de Dominio)

**Responsabilidad:** Contener toda la lógica de negocio.

**Componentes:**
- Entities (Entidades)
- Value Objects
- Domain Services
- Business Rules
- Domain Events
- Repository Interfaces

**Ubicación:** `apps/*/domain/`

**Características:**
- **Independiente** de frameworks y librerías externas
- Contiene las **reglas de negocio**
- Define **interfaces** (contracts) para infraestructura

**Ejemplo:**
```python
# apps/orden_pagos/domain/entities/payment_order.py
class PaymentOrder:
    """
    Payment Order entity with business logic
    """
    
    def __init__(self, order_number, student, total_order, status):
        self.order_number = order_number
        self.student = student
        self.total_order = total_order
        self.status = status
    
    def calculate_total(self):
        """Business rule: Calculate total from details"""
        return sum(detail.sub_total for detail in self.details)
    
    def can_be_paid(self) -> bool:
        """Business rule: Check if order can receive payments"""
        return self.status in ['ACTIVE', 'PENDING']
    
    def mark_as_paid(self):
        """Business rule: Mark order as paid when balance is zero"""
        if self.get_balance_due() <= 0:
            self.status = 'PAID'
            return True
        return False
```

**Repository Interface (Domain):**
```python
# apps/orden_pagos/domain/repositories/payment_order_repository_interface.py
from abc import ABC, abstractmethod

class PaymentOrderRepositoryInterface(ABC):
    """
    Contract for payment order persistence
    """
    
    @abstractmethod
    def save(self, payment_order: PaymentOrder) -> PaymentOrder:
        pass
    
    @abstractmethod
    def find_by_id(self, order_id: int) -> PaymentOrder:
        pass
    
    @abstractmethod
    def find_by_token(self, token: str) -> PaymentOrder:
        pass
```

---

### 4. Infrastructure Layer (Capa de Infraestructura)

**Responsabilidad:** Implementar detalles técnicos y comunicación con sistemas externos.

**Componentes:**
- Repository Implementations
- ORM Models (Django Models)
- External API Clients (PayPal, Stripe)
- File Storage
- Email Services
- Database Configurations

**Ubicación:** `apps/*/infrastructure/` y `db_models/`

**Ejemplo:**
```python
# apps/orden_pagos/infrastructure/repositories/payment_order_repository.py
from apps.orden_pagos.domain.repositories import PaymentOrderRepositoryInterface
from db_models.payment_orders.models import PaymentOrder as PaymentOrderModel

class PaymentOrderRepository(PaymentOrderRepositoryInterface):
    """
    Django ORM implementation of PaymentOrderRepository
    """
    
    def save(self, payment_order) -> PaymentOrder:
        # Convert domain entity to ORM model
        model = PaymentOrderModel.objects.create(
            order_number=payment_order.order_number,
            student_id=payment_order.student.id,
            total_order=payment_order.total_order,
            status=payment_order.status
        )
        return self._to_domain(model)
    
    def find_by_id(self, order_id: int):
        model = PaymentOrderModel.objects.get(id=order_id)
        return self._to_domain(model)
    
    def _to_domain(self, model):
        # Convert ORM model to domain entity
        return PaymentOrder(
            order_number=model.order_number,
            student=model.student,
            total_order=model.total_order,
            status=model.status
        )
```

---

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│  1. CLIENT REQUEST                                           │
│     POST /api/v1/payment-orders/                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. PRESENTATION LAYER                                       │
│     PaymentOrderViewSet.create()                            │
│     - Validates request data                                │
│     - Calls application layer                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. APPLICATION LAYER                                        │
│     CreatePaymentOrderUseCase.execute()                     │
│     - Orchestrates the operation                            │
│     - Calls domain services                                 │
│     - Manages transactions                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. DOMAIN LAYER                                             │
│     PaymentOrder.create() + Business Rules                  │
│     - Validates business rules                              │
│     - Applies domain logic                                  │
│     - Returns domain entity                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  5. INFRASTRUCTURE LAYER                                     │
│     PaymentOrderRepository.save()                           │
│     - Persists to database (Django ORM)                     │
│     - Sends emails (EmailService)                           │
│     - Stores files (FileStorage)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  6. CLIENT RESPONSE                                          │
│     200 OK + PaymentOrder data                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Ventajas de esta Arquitectura

### 1. **Testabilidad**
- Cada capa puede testearse independientemente
- Fácil crear mocks de dependencias externas

### 2. **Mantenibilidad**
- Cambios en una capa no afectan otras capas
- Código organizado y fácil de entender

### 3. **Flexibilidad**
- Fácil cambiar de framework o database
- Fácil agregar nuevas features

### 4. **Reusabilidad**
- Domain layer puede usarse en diferentes proyectos
- Use cases pueden reutilizarse en diferentes interfaces (API, CLI, etc.)

### 5. **Independencia**
- Domain no depende de Django
- Business logic puede ejecutarse sin framework

---

## Ejemplo Completo: Crear Orden de Pago

### 1. Request (Cliente)
```http
POST /api/v1/payment-orders/
Content-Type: application/json
Authorization: Token abc123

{
  "student_id": 100,
  "advisor_id": 50,
  "concepts": [
    {
      "concept_code": "I",
      "amount": 1000.00,
      "discount_type": "percentage",
      "discount_amount": 10.00
    }
  ]
}
```

### 2. Presentation Layer
```python
# apps/orden_pagos/presentation/views.py
class PaymentOrderViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = CreatePaymentOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = CreatePaymentOrderUseCase()
        order = use_case.execute(serializer.validated_data)
        
        response_serializer = PaymentOrderSerializer(order)
        return Response(response_serializer.data, status=201)
```

### 3. Application Layer
```python
# apps/orden_pagos/application/use_cases/create_payment_order.py
class CreatePaymentOrderUseCase:
    def execute(self, data):
        # 1. Get student and advisor
        student = self.user_repository.find_by_id(data['student_id'])
        advisor = self.user_repository.find_by_id(data['advisor_id'])
        
        # 2. Create domain entity
        payment_order = PaymentOrder.create(
            student=student,
            advisor=advisor,
            concepts=data['concepts']
        )
        
        # 3. Apply business rules
        payment_order.calculate_totals()
        payment_order.generate_token()
        
        # 4. Save
        saved_order = self.repository.save(payment_order)
        
        # 5. Send notification
        self.notification_service.send_payment_link(saved_order)
        
        return saved_order
```

### 4. Domain Layer
```python
# apps/orden_pagos/domain/entities/payment_order.py
class PaymentOrder:
    @classmethod
    def create(cls, student, advisor, concepts):
        order = cls()
        order.student = student
        order.advisor = advisor
        order.order_number = cls._generate_order_number()
        order.status = 'PENDING'
        order.concepts = concepts
        return order
    
    def calculate_totals(self):
        self.total_order = sum(
            concept.calculate_amount()
            for concept in self.concepts
        )
    
    def generate_token(self):
        self.token = secrets.token_urlsafe(64)
        self.link_expires_at = timezone.now() + timedelta(days=30)
```

### 5. Infrastructure Layer
```python
# apps/orden_pagos/infrastructure/repositories/payment_order_repository.py
class PaymentOrderRepository:
    def save(self, payment_order):
        with transaction.atomic():
            # Save order
            model = PaymentOrderModel.objects.create(
                order_number=payment_order.order_number,
                student_id=payment_order.student.id,
                advisor_id=payment_order.advisor.id,
                total_order=payment_order.total_order,
                status=payment_order.status,
                token=payment_order.token
            )
            
            # Save details
            for concept in payment_order.concepts:
                PaymentOrderDetailsModel.objects.create(
                    payment_order=model,
                    concept_code=concept.code,
                    amount=concept.amount
                )
            
            return self._to_domain(model)
```

### 6. Response
```json
{
  "id": 123,
  "order_number": "PO-2026-00123",
  "student": {
    "id": 100,
    "name": "Juan Pérez"
  },
  "advisor": {
    "id": 50,
    "name": "María González"
  },
  "total_order": 900.00,
  "status": "PENDING",
  "token": "xyz789abc...",
  "payment_link": "https://payments.example.com/pay/xyz789abc...",
  "created_at": "2026-03-30T10:30:00Z"
}
```

---

## Principios SOLID Aplicados

### Single Responsibility Principle (SRP)
Cada clase tiene una única responsabilidad:
- `PaymentOrderViewSet`: Manejar HTTP
- `CreatePaymentOrderUseCase`: Orquestar creación
- `PaymentOrder`: Lógica de negocio
- `PaymentOrderRepository`: Persistencia

### Open/Closed Principle (OCP)
Abierto para extensión, cerrado para modificación:
- Nuevas pasarelas de pago sin modificar código existente
- Nuevos tipos de notificaciones sin cambiar use cases

### Liskov Substitution Principle (LSP)
Interfaces implementables sin romper funcionalidad:
- `PaymentGatewayInterface`: PayPal, Stripe intercambiables

### Interface Segregation Principle (ISP)
Interfaces específicas, no genéricas:
- `PaymentRepositoryInterface`
- `NotificationServiceInterface`
- Separate interfaces for different concerns

### Dependency Inversion Principle (DIP)
Depender de abstracciones, no de implementaciones:
- Use cases dependen de interfaces
- Infrastructure implementa interfaces
- Dependency injection en use cases

---

## Testing Strategy

### Unit Tests
```python
# Test domain logic (no dependencies)
def test_payment_order_calculate_total():
    order = PaymentOrder()
    order.add_concept(Concept(amount=1000))
    order.add_concept(Concept(amount=500))
    
    total = order.calculate_total()
    
    assert total == 1500
```

### Integration Tests
```python
# Test use cases with real repositories
def test_create_payment_order_use_case():
    use_case = CreatePaymentOrderUseCase()
    
    order = use_case.execute({
        'student_id': 1,
        'concepts': [...]
    })
    
    assert order.order_number is not None
    assert order.status == 'PENDING'
```

### API Tests
```python
# Test complete flow
def test_create_payment_order_api(client):
    response = client.post('/api/v1/payment-orders/', {
        'student_id': 1,
        'concepts': [...]
    })
    
    assert response.status_code == 201
    assert 'order_number' in response.json()
```

---

## Conclusión

Esta arquitectura proporciona:
- ✅ Separación clara de responsabilidades
- ✅ Código testeable y mantenible
- ✅ Flexibilidad para cambios futuros
- ✅ Independencia de frameworks
- ✅ Cumplimiento de principios SOLID
- ✅ Facilita el trabajo en equipo

El sistema puede evolucionar sin afectar el core business logic.

