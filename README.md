# 🚀 Payment Microservice - Django REST API

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-green)](https://www.djangoproject.com/)
[![Django Ninja](https://img.shields.io/badge/Django%20Ninja-1.1%2B-red)](https://django-ninja.rest-framework.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2B%20Hexagonal-brightgreen)](docs/ARCHITECTURE.md)

Sistema completo de gestión de pagos como microservicio independiente. Desarrollado con Clean Architecture + DDD + Arquitectura Hexagonal usando **Django Ninja** para las APIs.

---

## ✨ Características Principales

### 🎯 Sistema de Órdenes de Pago
- ✅ Gestión completa de órdenes de pago
- ✅ Múltiples conceptos (Matrícula, Inscripción, Alojamiento, etc.)
- ✅ Pagos parciales y abonos
- ✅ Enlaces de pago con tokens seguros
- ✅ Cálculo automático de totales

### 💳 Sistema de Pagos
- ✅ Integración PayPal y Stripe
- ✅ Webhooks automáticos
- ✅ Historial completo de transacciones
- ✅ Asignación automática a conceptos

### 📄 Sistema de Facturación
- ✅ Generación automática de facturas
- ✅ Gestión de saldo pendiente
- ✅ Aplicación de créditos
- ✅ Generación de recibos

### 🛠️ Servicios Adicionales
- ✅ Generación de PDFs
- ✅ Envío de correos
- ✅ Procesamiento asíncrono (Celery)
- ✅ API REST con Django Ninja
- ✅ Documentación OpenAPI/Swagger automática

---

## 🚀 Inicio Rápido

### Con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/payment-microservice.git
cd payment-microservice

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Levantar servicios
docker-compose up -d

# 4. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 5. Cargar datos iniciales
docker-compose exec web python manage.py loaddata initial_data

# 6. Crear superusuario
docker-compose exec web python manage.py createsuperuser

# 7. Acceder a la API
# http://localhost:8000/api/v1/
# http://localhost:8000/api/v1/api-docs/ (Documentación)
```

### Sin Docker

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env
cp .env.example .env

# 4. Migrar base de datos
python manage.py migrate

# 5. Cargar datos iniciales
python manage.py loaddata initial_data

# 6. Ejecutar servidor
python manage.py runserver
```

---

## 📚 Documentación

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Endpoints completos
- **[Architecture](docs/ARCHITECTURE.md)** - Arquitectura del sistema
- **[Development Guide](docs/DEVELOPMENT.md)** - Guía para desarrolladores
- **[Deployment](docs/DEPLOYMENT.md)** - Despliegue en producción

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│        PRESENTATION LAYER               │
│     (API REST - ViewSets)               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       APPLICATION LAYER                 │
│       (Use Cases - Services)            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         DOMAIN LAYER                    │
│    (Entities - Business Logic)          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      INFRASTRUCTURE LAYER               │
│   (DB, External APIs, Storage)          │
└─────────────────────────────────────────┘
```

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**José Lanza**
- GitHub: [@jlanza](https://github.com/jlanza)

---

⚡ **Sistema de pagos enterprise-grade listo para producción** ⚡

