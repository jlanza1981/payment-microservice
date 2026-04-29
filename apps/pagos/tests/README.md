# Tests de Pagos

Esta carpeta contiene tests para el módulo `apps.pagos` que gestiona:
- Modelo de pagos (Payment)
- Repositorio de pagos
- Casos de uso de pagos

---

## 📋 Tests Disponibles

### `test_payment_repository.py`
- **Descripción:** Test del repositorio de pagos
- **Verifica:** 
  - Interfaz del repositorio
  - Operaciones CRUD
  - Consultas específicas
- **Ejecutar:** `python manage.py shell < apps/pagos/tests/test_payment_repository.py`

---

## 🚀 Ejecutar Tests

```bash
cd /home/jlanza/projects/backend/django/api

# Opción 1: Con manage.py shell
python manage.py shell < apps/pagos/tests/test_payment_repository.py

# Opción 2: Directamente
python apps/pagos/tests/test_payment_repository.py
```

---

## 📚 Arquitectura

Este módulo sigue **arquitectura hexagonal**:

- **Domain:** Interfaces y entidades
- **Application:** Casos de uso
- **Infrastructure:** Repositorios (implementaciones)

---

## 🔗 Relacionado

- **Código:** `apps/pagos/domain/`, `apps/pagos/application/`, `apps/pagos/infrastructure/`
- **Modelos:** `apps/pagos/models.py`

