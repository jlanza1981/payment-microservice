# 🚀 Guía de Instalación - Payment Microservice

## Instalación Rápida con Docker

Esta es la forma más rápida y recomendada de ejecutar el microservicio.

### Requisitos
- Docker Desktop o Docker Engine instalado
- Docker Compose instalado
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/payment-microservice.git
cd payment-microservice

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Editar .env (IMPORTANTE)
# Configurar al menos:
# - SECRET_KEY
# - PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET
# - EMAIL_HOST_USER y EMAIL_HOST_PASSWORD (si usas email)

# 4. Construir y levantar servicios
docker-compose up -d --build

# 5. Esperar a que los servicios estén listos
docker-compose logs -f web

# 6. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 7. Crear superusuario
docker-compose exec web python manage.py createsuperuser

# 8. Cargar datos iniciales (conceptos de pago)
docker-compose exec web python manage.py loaddata initial_data

# 9. Acceder a la aplicación
# API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin/
# Docs: http://localhost:8000/api/v1/api-docs/
```

---

## Instalación Local (Sin Docker)

Para desarrollo local o si no puedes usar Docker.

### Requisitos
- Python 3.10 o superior
- PostgreSQL 13+ (o SQLite para desarrollo)
- Redis (para Celery)
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/payment-microservice.git
cd payment-microservice

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu editor favorito

# 7. Crear base de datos PostgreSQL (opcional)
# Si usas PostgreSQL:
createdb payment_microservice_db

# 8. Ejecutar migraciones
python manage.py migrate

# 9. Crear superusuario
python manage.py createsuperuser

# 10. Cargar datos iniciales
python manage.py loaddata initial_data

# 11. Recolectar archivos estáticos
python manage.py collectstatic --noinput

# 12. Ejecutar servidor de desarrollo
python manage.py runserver
```

### Servicios Adicionales

#### Redis (para Celery)
```bash
# En Linux/Mac con Homebrew:
brew install redis
brew services start redis

# En Ubuntu/Debian:
sudo apt-get install redis-server
sudo service redis-server start

# En Windows:
# Descargar desde https://redis.io/download
# O usar Docker:
docker run -d -p 6379:6379 redis:alpine
```

#### Celery Worker (en otra terminal)
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar worker
celery -A config worker -l info
```

#### Celery Beat (tareas programadas)
```bash
# En otra terminal
source venv/bin/activate
celery -A config beat -l info
```

---

## Verificación de Instalación

### 1. Verificar que el servidor está corriendo
```bash
curl http://localhost:8000/api/v1/health

# Debería responder: {"status": "healthy"}
```

### 2. Acceder al admin
```
http://localhost:8000/admin/
```
Usar las credenciales del superusuario creado.

### 3. Ver documentación de la API
```
http://localhost:8000/api/v1/api-docs/
```

### 4. Listar endpoints disponibles
```bash
python manage.py show_urls
```

---

## Configuración Básica

### 1. Configurar PayPal

En tu archivo `.env`:

```bash
PAYPAL_CLIENT_ID=tu-client-id-aqui
PAYPAL_CLIENT_SECRET=tu-secret-aqui
PAYPAL_MODE=sandbox  # Usar 'live' en producción
```

Para obtener credenciales de PayPal:
1. Ir a https://developer.paypal.com/
2. Crear una aplicación
3. Obtener Client ID y Secret

### 2. Configurar Email

Para Gmail:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

**Nota:** Usa una "App Password" en Gmail, no tu contraseña normal.

### 3. Configurar Base de Datos (Producción)

PostgreSQL:

```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=payment_microservice_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Cargar Datos de Prueba

```bash
# Cargar conceptos de pago básicos
python manage.py loaddata payment_concepts

# Cargar datos de ejemplo (opcional)
python manage.py loaddata sample_data

# Crear datos de prueba personalizados
python manage.py create_test_data
```

---

## Solución de Problemas

### Error: "No module named 'apps'"

```bash
# Asegúrate de estar en el directorio correcto
cd payment-microservice

# Verifica que PYTHONPATH esté configurado
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Error: "relation does not exist"

```bash
# Ejecutar migraciones
python manage.py migrate
```

### Error: "Connection refused" (PostgreSQL)

```bash
# Verificar que PostgreSQL está corriendo
sudo service postgresql status

# Iniciar PostgreSQL
sudo service postgresql start
```

### Error: "Connection refused" (Redis)

```bash
# Verificar que Redis está corriendo
redis-cli ping
# Debería responder: PONG

# Si no responde, iniciar Redis
redis-server
```

### Error de permisos en manage.py

```bash
# Dar permisos de ejecución
chmod +x manage.py
```

---

## Comandos Útiles

### Desarrollo

```bash
# Ejecutar servidor en modo desarrollo
python manage.py runserver

# Ejecutar servidor en puerto específico
python manage.py runserver 0.0.0.0:9000

# Ejecutar shell de Django
python manage.py shell

# Crear una nueva aplicación
python manage.py startapp nombre_app

# Verificar problemas
python manage.py check
```

### Base de Datos

```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Ver SQL de migraciones
python manage.py sqlmigrate app_name migration_name

# Listar migraciones
python manage.py showmigrations

# Revertir migración
python manage.py migrate app_name migration_name
```

### Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Tests con coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Tests específicos
python manage.py test apps.orden_pagos
```

### Datos

```bash
# Crear backup de la base de datos
python manage.py dumpdata > backup.json

# Restaurar backup
python manage.py loaddata backup.json

# Exportar datos específicos
python manage.py dumpdata payment_orders > payment_orders.json
```

---

## Próximos Pasos

1. **Explorar la API:** http://localhost:8000/api/docs/
2. **Leer la documentación de arquitectura:** `docs/ARCHITECTURE.md`
3. **Ver ejemplos de uso:** `docs/EXAMPLES.md`
4. **Configurar webhooks:** Para PayPal y Stripe

---

## Recursos Adicionales

- [Documentación Completa](docs/)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

**¡Listo para empezar a desarrollar!** 🚀

