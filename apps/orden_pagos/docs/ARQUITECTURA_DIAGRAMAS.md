# Arquitectura - Casos de Uso de Envío de Pago y PDF

## Diagrama de Flujo de la Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE PRESENTACIÓN                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   ViewSet    │  │   API View   │  │  Management  │  │   Scripts   │ │
│  │     DRF      │  │              │  │   Command    │  │             │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                 │         │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                    CAPA DE TAREAS ASÍNCRONAS (Celery)                    │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   │                                      │
│                  ┌────────────────▼────────────────┐                     │
│                  │  enviar_enlace_pago_orden()    │                     │
│                  │  (Tarea Celery Refactorizada)  │                     │
│                  └────────────────┬────────────────┘                     │
│                                   │                                      │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                      CAPA DE APLICACIÓN (Use Cases)                      │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   │                                      │
│                  ┌────────────────▼────────────────┐                     │
│                  │  SendPaymentLinkUseCase         │                     │
│                  │  • Valida estado PENDING        │                     │
│                  │  • Genera enlace de pago        │                     │
│                  │  • Prepara datos de correo      │                     │
│                  │  • Envía correos                │                     │
│                  │  • Actualiza fecha de envío     │                     │
│                  └────────┬──────────────┬─────────┘                     │
│                           │              │                               │
│                           │      ┌───────▼──────────┐                    │
│                           │      │ GeneratePDF      │                    │
│                           │      │ UseCase          │                    │
│                           │      │ • Obtiene datos  │                    │
│                           │      │ • Renderiza HTML │                    │
│                           │      │ • Aplica CSS     │                    │
│                           │      │ • Genera PDF     │                    │
│                           │      └──────────────────┘                    │
│                           │                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────────────┐
│                    CAPA DE INFRAESTRUCTURA                                │
├───────────────────────────┼──────────────────────────────────────────────┤
│                           │                                               │
│                  ┌────────▼───────────┐                                  │
│                  │   Repository       │                                  │
│                  │  • get_by_id()     │                                  │
│                  │  • update()        │                                  │
│                  └────────┬───────────┘                                  │
│                           │                                               │
└───────────────────────────┼───────────────────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────────────────┐
│                       CAPA DE DOMINIO                                     │
├───────────────────────────┼───────────────────────────────────────────────┤
│                           │                                               │
│                  ┌────────▼───────────┐                                  │
│                  │   PaymentOrder     │                                  │
│                  │   (Modelo Django)  │                                  │
│                  │  • Propiedades     │                                  │
│                  │  • Métodos         │                                  │
│                  │  • Validaciones    │                                  │
│                  └────────────────────┘                                  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Flujo de Ejecución: Envío de Enlace de Pago

```
┌────────┐
│ START  │
└───┬────┘
    │
    ▼
┌─────────────────────────────────┐
│ Usuario solicita envío          │
│ (API, Command, Script)          │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Tarea Celery (asíncrono)        │
│ o Llamada directa (síncrono)    │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│ SendPaymentLinkUseCase.execute(order_id)            │
├─────────────────────────────────────────────��───────┤
│                                                     │
│  1. Obtener orden con relaciones                   │
│     └─> Repository.get_by_id_with_relations()      │
│                                                     │
│  2. Validar estado PENDING                         │
│     └─> Si no es PENDING: ValidationError          │
│                                                     │
│  3. Generar enlace de pago                         │
│     └─> _generate_payment_link()                   │
│                                                     │
│  4. Preparar datos del correo                      │
│     └─> _prepare_email_data()                      │
│                                                     │
│  5. Generar PDF                                    │
│     └─> GeneratePaymentOrderPDFUseCase.execute()   │
│         ├─> Obtener estructura de orden            │
│         ├─> Renderizar HTML                        │
│         ├─> Aplicar CSS                            │
│         └─> Generar PDF con WeasyPrint             │
│                                                     │
│  6. Enviar correo al estudiante                    │
│     └─> _send_student_email()                      │
│         ├─> Crear EmailMultiAlternatives           │
│         ├─> Adjuntar PDF                           │
│         └─> Enviar                                 │
│                                                     │
│  7. Enviar correo al asesor                        │
│     └─> _send_advisor_email()                      │
│         ├─> Crear EmailMultiAlternatives           │
│         ├─> Adjuntar PDF                           │
│         └─> Enviar                                 │
│                                                     │
│  8. Actualizar fecha de envío                      │
│     └─> payment_order.save()                       │
│                                                     │
│  9. Construir respuesta                            │
│     └─> _build_response()                          │
│                                                     │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Retornar resultado              │
│ {                               │
│   'success': True/False,        │
│   'message': '...',             │
│   'emails_sent': [...],         │
│   'order_number': '...',        │
│   'errors': [...]               │
│ }                               │
└─────────────┬───────────────────┘
              │
              ▼
          ┌───────┐
          │  END  │
          └───────┘
```

## Flujo de Ejecución: Generación de PDF

```
┌────────┐
│ START  │
└───┬────┘
    │
    ▼
┌────────────────────────────────────────┐
│ GeneratePaymentOrderPDFUseCase         │
│ .execute(payment_order, base_url)      │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ 1. Obtener estructura de la orden      │
│    payment_order.get_order_structure() │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ 2. Renderizar plantilla HTML           │
│    render_to_string(template, data)    │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ 3. Configurar base_url                 │
│    (si no se proporciona)              │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ 4. Generar PDF                         │
│    _generate_pdf()                     │
│    ├─> Buscar archivo CSS              │
│    ├─> Crear HTML object               │
│    └─> write_pdf(stylesheets)          │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ 5. Retornar bytes del PDF              │
└────────────┬───────────────────────────┘
             │
             ▼
         ┌───────┐
         │  END  │
         └───────┘
```

## Responsabilidades por Capa

### 📱 Presentación

- Recibir peticiones del usuario
- Validar entrada básica
- Llamar casos de uso
- Formatear respuestas

### ⚙️ Aplicación (Use Cases)

- **SendPaymentLinkUseCase:**
    - Orquestar el proceso de envío
    - Validar reglas de negocio
    - Coordinar entre repositorio y generador PDF
    - Manejar errores

- **GeneratePaymentOrderPDFUseCase:**
    - Generar PDFs con parámetros flexibles
    - Aplicar plantillas y estilos
    - Manejar errores de generación

### 🗄️ Infraestructura

- Acceso a base de datos
- Implementación de repositorios
- Servicios externos (email, WeasyPrint)

### 🎯 Dominio

- Modelos de datos
- Lógica de negocio core
- Validaciones de entidades

## Dependencias entre Casos de Uso

```
SendPaymentLinkUseCase
│
├─> PaymentOrderRepository (Inyectado)
│   └─> get_by_id_with_relations()
│   └─> save()
│
└─> GeneratePaymentOrderPDFUseCase (Inyectado)
    └─> execute(payment_order)
```

## Puntos de Extensión

### 🔌 Fácil de extender:

1. **Nuevos tipos de notificaciones**
    - Crear nuevo caso de uso: `SendPaymentSMSUseCase`
    - Inyectar en `SendPaymentLinkUseCase`

2. **Diferentes formatos de PDF**
    - Agregar parámetro `template_name`
    - Crear nuevas plantillas

3. **Múltiples canales de envío**
    - Implementar patrón Strategy
    - Crear `NotificationChannel` interface

4. **Logging y métricas**
    - Agregar decoradores
    - Implementar observers

## Ventajas de esta Arquitectura

### ✅ Ventajas

| Aspecto            | Beneficio                                   |
|--------------------|---------------------------------------------|
| **Testabilidad**   | Casos de uso aislados, fácil mocking        |
| **Mantenibilidad** | Cambios localizados, bajo acoplamiento      |
| **Reutilización**  | Casos de uso usables desde múltiples puntos |
| **Legibilidad**    | Código limpio y autodocumentado             |
| **Escalabilidad**  | Fácil agregar nuevas funcionalidades        |
| **Separación**     | Cada clase tiene una responsabilidad        |

### 🎯 Principios SOLID Aplicados

- **S** - Single Responsibility: Cada caso de uso hace una cosa
- **O** - Open/Closed: Abierto a extensión, cerrado a modificación
- **L** - Liskov Substitution: Interfaces bien definidas
- **I** - Interface Segregation: Interfaces específicas
- **D** - Dependency Inversion: Dependencia de abstracciones

---

**Fecha:** 2025-01-28  
**Versión:** 1.0  
**Arquitectura:** Clean Architecture + SOLID

