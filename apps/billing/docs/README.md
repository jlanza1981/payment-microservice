# Documentación de Billing App

Bienvenido a la documentación del módulo de facturación de LC Mundo.

## 📚 Índice de Documentación

### Guías Principales

1. **[README.md](../README.md)** - Guía principal de la app
    - Descripción general del módulo
    - Modelos principales
    - Instrucciones de uso básico
    - Estados de factura y flujo

2. **[REPOSITORIO_Y_CASOS_DE_USO.md](REPOSITORIO_Y_CASOS_DE_USO.md)** - Arquitectura detallada
    - Estructura de capas (Domain, Infrastructure, Application)
    - Documentación de cada componente
    - Ejemplos de uso del repositorio y casos de uso
    - Próximos desarrollos

3. **[DIAGRAMA_ARQUITECTURA.md](DIAGRAMA_ARQUITECTURA.md)** - Diagramas visuales
    - Estructura de capas visualizada
    - Flujo de creación de facturas
    - Dependencias entre componentes
    - Patrones utilizados

4. **[RESUMEN_IMPLEMENTACION.md](RESUMEN_IMPLEMENTACION.md)** - Checklist y resumen
    - Archivos creados
    - Características principales
    - Ejemplos de uso
    - Validaciones implementadas

## 🎯 Inicio Rápido

### Crear una Factura

```python
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository

# Configurar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()
use_case = CreateInvoiceUseCase(domain_service, repository)

# Datos de la factura
data = {
    "student": 123,
    "advisor": 456,
    "payment_order": 789,
    "invoice_details": [
        {
            "payment_concept": 1,
            "description": "Matrícula",
            "quantity": 1,
            "unit_price": 500.00
        }
    ]
}

# Ejecutar
invoice = use_case.execute(data)
```

## 📖 Documentos por Tema

### Arquitectura

- [Diagrama de Arquitectura](DIAGRAMA_ARQUITECTURA.md) - Diagramas y flujos
- [Repositorio y Casos de Uso](REPOSITORIO_Y_CASOS_DE_USO.md) - Detalles técnicos

### Implementación

- [Resumen de Implementación](RESUMEN_IMPLEMENTACION.md) - Qué se implementó
- [README Principal](../README.md) - Guía de uso

### Testing

- Ver archivo: `../tests/test_invoice_use_case.py`

## 🔍 Búsqueda Rápida

### ¿Qué necesitas hacer?

- **Crear una factura** → [REPOSITORIO_Y_CASOS_DE_USO.md](REPOSITORIO_Y_CASOS_DE_USO.md#uso-del-caso-de-uso)
- **Entender la arquitectura** → [DIAGRAMA_ARQUITECTURA.md](DIAGRAMA_ARQUITECTURA.md)
- **Ver ejemplos de código** → [REPOSITORIO_Y_CASOS_DE_USO.md](REPOSITORIO_Y_CASOS_DE_USO.md#ejemplo-básico)
- **Saber qué se implementó** → [RESUMEN_IMPLEMENTACION.md](RESUMEN_IMPLEMENTACION.md)
- **Conocer los modelos** → [README.md](../README.md#modelos-principales)
- **Escribir tests** → Ver `../tests/test_invoice_use_case.py`

## 🏗️ Componentes Principales

### Domain Layer (Dominio)

- `InvoiceRepositoryInterface` - Contrato del repositorio
- `InvoiceDomainService` - Lógica de negocio

### Infrastructure Layer (Infraestructura)

- `InvoiceRepository` - Implementación con Django ORM

### Application Layer (Aplicación)

- `CreateInvoiceUseCase` - Caso de uso para crear facturas

## 🎓 Conceptos Clave

### Clean Architecture

Esta aplicación sigue los principios de Clean Architecture (Arquitectura Hexagonal):

- **Domain** - Reglas de negocio puras
- **Application** - Casos de uso (orquestación)
- **Infrastructure** - Detalles de implementación (BD, APIs)

### Repository Pattern

Abstracción del acceso a datos que permite:

- Cambiar la implementación sin afectar la lógica de negocio
- Facilitar los tests con mocks
- Centralizar las consultas

### Use Case Pattern

Cada operación de negocio tiene su propio caso de uso:

- Un caso de uso = una funcionalidad completa
- Orquesta la interacción entre servicios y repositorios
- Mantiene la lógica de negocio aislada

## 🚀 Roadmap

### Implementado ✅

- [x] CreateInvoiceUseCase
- [x] InvoiceRepository completo
- [x] InvoiceDomainService con validaciones
- [x] Tests unitarios básicos
- [x] Documentación completa

### Por Implementar 🔜

- [ ] UpdateInvoiceUseCase
- [ ] CancelInvoiceUseCase
- [ ] ListInvoicesUseCase
- [ ] GenerateInvoicePDFUseCase
- [ ] ApplyCreditToInvoiceUseCase
- [ ] SendInvoiceEmailUseCase

## 📞 Soporte

Para preguntas o dudas sobre la implementación:

1. Revisa primero esta documentación
2. Consulta el código de referencia en `apps/orden_pagos`
3. Revisa los tests para ver ejemplos prácticos

## 🔗 Enlaces Relacionados

### Documentación del Proyecto

- [Documentación General](../../../docs/README.md)
- [Sistema de Abonos](../../../docs/GUIA_RAPIDA_SISTEMA_ABONOS.md)
- [Orden de Pagos](../../orden_pagos/README.md)

### Recursos Externos

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)

---

**Última actualización**: 2026-01-12
**Versión**: 1.0.0
**Mantenedor**: Equipo LC Mundo

