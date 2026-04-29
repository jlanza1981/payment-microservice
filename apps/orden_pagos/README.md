# 📦 Sistema de Órdenes de Pago

Sistema completo para gestión de órdenes de pago, registro de estudiantes y envío de enlaces de pago.

---

## 🗂️ Estructura de Documentación

### 📚 [context/](./context/)
Documentación de contexto completo para desarrollo y trabajo con IA:
- **REFERENCIA_RAPIDA.md** - ⭐ Inicio rápido (2 páginas)
- **CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md** - Arquitectura completa
- **CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md** - Sistema de envío de enlaces
- **README.md** - Guía de uso de archivos de contexto

### 📖 [docs/](./docs/)
Guías de implementación y uso:
- **PAYMENT_ORDERS_API_DOCUMENTATION.md** - Documentación API completa
- **GUIA_FRONTEND_ENVIO_ENLACE.md** - Guía para frontend
- **EJEMPLO_USO_ENVIO_ENLACE_PAGO.md** - Ejemplos prácticos
- **EJEMPLOS_FRONTEND_PAGINACION.md** - Paginación frontend
- **CAMBIOS_SIN_CONTRASENAS_TEMPORALES.md** - Cambios recientes
- **IMPLEMENTACION_COMPLETADA_ENLACE_PAGO.md** - Estado de implementación
- **RESUMEN_ENVIO_ENLACE_PAGO.md** - Resumen funcionalidad
- **RESUMEN_OPCIONES_ENVIO_ENLACE.md** - Opciones disponibles

---

## 🚀 Inicio Rápido

### Para Desarrolladores
1. Lee primero: [`context/REFERENCIA_RAPIDA.md`](./context/REFERENCIA_RAPIDA.md)
2. Consulta: [`docs/PAYMENT_ORDERS_API_DOCUMENTATION.md`](./docs/PAYMENT_ORDERS_API_DOCUMENTATION.md)

### Para Trabajo con IA
1. Carga: [`context/CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md`](./context/CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md)
2. Complementa con: [`context/CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md`](./context/CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md)

### Para Implementar Frontend
1. Revisa: [`docs/GUIA_FRONTEND_ENVIO_ENLACE.md`](./docs/GUIA_FRONTEND_ENVIO_ENLACE.md)
2. Ve ejemplos en: [`docs/EJEMPLO_USO_ENVIO_ENLACE_PAGO.md`](./docs/EJEMPLO_USO_ENVIO_ENLACE_PAGO.md)

---

## 🏗️ Arquitectura

El sistema sigue **Clean Architecture + Domain-Driven Design (DDD)**:

```
orden_pagos/
├── domain/           # Lógica de negocio
│   ├── entities/     # Modelos de dominio
│   ├── repositories/ # Interfaces de repositorio
│   └── services/     # Servicios de dominio
├── application/      # Casos de uso
│   ├── dtos/         # Data Transfer Objects
│   └── use_cases/    # Lógica de aplicación
├── infrastructure/   # Implementaciones
│   ├── repositories/ # Repositorios concretos
│   └── services/     # Servicios externos
└── presentation/     # Interfaz de usuario
    ├── serializers/  # Serializers DRF
    └── views/        # ViewSets y vistas
```

---

## 📋 Características Principales

✅ **Gestión de Órdenes de Pago**
- CRUD completo con paginación
- Múltiples conceptos de pago
- Cálculo automático de totales
- Estados y seguimiento

✅ **Registro de Estudiantes**
- Creación automática de usuarios
- Sin contraseñas temporales (recuperación por web)
- Validaciones completas
- Manejo de duplicados

✅ **Envío de Enlaces de Pago**
- Creación/actualización automática de orden
- Generación de PDF con detalle
- Envío de correos (estudiante + asesor)
- Plantillas personalizables
- Gestión asíncrona con Celery

✅ **API RESTful**
- Django REST Framework
- Autenticación y permisos
- Filtros y búsqueda
- Ordenamiento
- Paginación personalizada

---

## 🔑 Endpoints Principales

```
POST   /api/V1/orden-pagos/payment-orders/              # Crear orden
GET    /api/V1/orden-pagos/payment-orders/              # Listar órdenes
GET    /api/V1/orden-pagos/payment-orders/{id}/         # Detalle orden
PUT    /api/V1/orden-pagos/payment-orders/{id}/         # Actualizar orden
DELETE /api/V1/orden-pagos/payment-orders/{id}/         # Eliminar orden
POST   /api/V1/orden-pagos/payment-orders/send-payment-link/  # Enviar enlace
```

---

## 📧 Contacto y Soporte

Para dudas o soporte, consulta la documentación en las carpetas `context/` y `docs/`.

---

**Última actualización:** 2025-01-28

