# 📋 Checklist de Migración - PaymentHistoryService

## Pre-requisitos

Antes de empezar la migración, asegúrate de:

- [ ] Tener backup del código actual
- [ ] Tener tests de integración funcionando (si existen)
- [ ] Ambiente de desarrollo configurado
- [ ] Git branch creada para la migración

---

## Fase 1: Validación (15 min)

### ✅ 1.1 Verificar archivos nuevos creados

```bash
# Verificar que todos los archivos existen
ls -la apps/pagos/domain/interface/services/file_storage_service_interface.py
ls -la apps/pagos/domain/interface/services/pdf_generator_service_interface.py
ls -la apps/pagos/application/services/payment_pdf_service.py
ls -la apps/pagos/infrastructure/services/local_file_storage_service.py
ls -la apps/pagos/infrastructure/services/celery_pdf_generator_service.py
ls -la apps/pagos/application/dependencies.py
```

- [ ] Todos los archivos de dominio existen
- [ ] Todos los archivos de infraestructura existen
- [ ] Archivo de dependencies existe
- [ ] DTO actualizado a inmutable

### ✅ 1.2 Verificar imports

```bash
# Ejecutar para verificar imports
python manage.py check
```

- [ ] No hay errores de import
- [ ] No hay errores de sintaxis

---

## Fase 2: Testing (30 min)

### ✅ 2.1 Ejecutar tests unitarios nuevos

```bash
# Ejecutar tests del nuevo servicio
python manage.py test apps.pagos.tests.test_payment_history_service
```

- [ ] Todos los tests pasan
- [ ] No hay warnings críticos

### ✅ 2.2 Crear tests de integración básicos

```python
# tests/integration/test_payment_history_integration.py
from apps.pagos.application.dependencies import get_payment_history_service

def test_service_can_be_instantiated():
    service = get_payment_history_service()
    assert service is not None
    assert service.payment_repository is not None
    assert service.payment_pdf_service is not None
```

- [ ] Test de integración básico funciona

---

## Fase 3: Migración de Vistas (1-2 horas)

### ✅ 3.1 Identificar todos los lugares donde se usa el servicio antiguo

```bash
# Buscar usos del servicio
grep -r "PaymentHistoryService" apps/ --include="*.py" | grep -v __pycache__
```

- [ ] Lista de archivos que usan el servicio creada
- [ ] Cantidad de lugares a migrar identificada: _____

### ✅ 3.2 Migrar cada vista/endpoint

Para cada archivo identificado:

#### Ejemplo de migración:

**ANTES:**
```python
from apps.pagos.application.services.payment_history_service import PaymentHistoryService
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.infrastructure.repository.legacy_payment_repository import LegacyPaymentRepository

def get_payment_history(request, student_id):
    payment_repo = PaymentRepository()
    legacy_repo = LegacyPaymentRepository()
    service = PaymentHistoryService(payment_repo, legacy_repo)
    
    payments = service.get_student_payments(student_id, request=request)
    return Response(...)
```

**DESPUÉS:**
```python
from apps.pagos.application.dependencies import get_payment_history_service

def get_payment_history(request, student_id):
    service = get_payment_history_service()
    base_url = request.build_absolute_uri('/')
    
    payments = service.get_student_payments(
        student_id=student_id,
        base_url=base_url,
        ensure_pdfs=True
    )
    return Response(...)
```

#### Checklist por archivo:

- [ ] Archivo 1: _________________________ migrado
- [ ] Archivo 2: _________________________ migrado
- [ ] Archivo 3: _________________________ migrado
- [ ] Archivo 4: _________________________ migrado
- [ ] Archivo 5: _________________________ migrado

### ✅ 3.3 Verificar cada vista migrada

Para cada vista:
- [ ] Cambios realizados
- [ ] Imports actualizados
- [ ] Signature actualizada (`request` → `base_url`)
- [ ] Manejo de errores revisado
- [ ] Funciona en desarrollo local

---

## Fase 4: Testing de Integración (30 min)

### ✅ 4.1 Ejecutar suite completa de tests

```bash
# Ejecutar todos los tests relacionados con pagos
python manage.py test apps.pagos
```

- [ ] Tests unitarios pasan
- [ ] Tests de integración pasan
- [ ] No hay regresiones

### ✅ 4.2 Pruebas manuales

#### Escenario 1: Obtener historial de pagos
```bash
# Usando curl o Postman
curl -X GET http://localhost:8000/api/students/123/payments/
```

- [ ] Retorna pagos correctamente
- [ ] Pagos ordenados por fecha
- [ ] PDFs existen o se regeneran
- [ ] No hay errores en logs

#### Escenario 2: Filtros
```bash
curl -X GET "http://localhost:8000/api/students/123/payments/?date_from=2024-01-01"
```

- [ ] Filtros funcionan correctamente
- [ ] Resultados son los esperados

#### Escenario 3: Sin verificación de PDFs
```bash
curl -X GET "http://localhost:8000/api/students/123/payments/?ensure_pdfs=false"
```

- [ ] Respuesta más rápida
- [ ] No intenta regenerar PDFs
- [ ] Datos correctos

---

## Fase 5: Limpieza (15 min)

### ✅ 5.1 Eliminar código antiguo (OPCIONAL - hacer después de validación en producción)

⚠️ **NO ELIMINAR HASTA VALIDAR EN PRODUCCIÓN**

Después de validación exitosa en producción:

```bash
# Crear backup del código antiguo
git tag backup-before-cleanup
git push origin backup-before-cleanup

# Comentar imports no utilizados (no eliminar aún)
# Mantener por al menos 1 sprint
```

- [ ] Backup creado
- [ ] Tag en git creado
- [ ] Código antiguo comentado (no eliminado)

---

## Fase 6: Documentación (15 min)

### ✅ 6.1 Actualizar documentación del proyecto

- [ ] README.md actualizado con nueva arquitectura
- [ ] Changelog actualizado
- [ ] Comentarios en código revisados

### ✅ 6.2 Comunicar cambios al equipo

- [ ] Email/Slack al equipo con cambios
- [ ] Demo en daily standup (opcional)
- [ ] Link a REFACTORING_GUIDE.md compartido

---

## Fase 7: Deployment (variable)

### ✅ 7.1 Preparación

- [ ] Branch mergeada a develop
- [ ] CI/CD pasa todos los tests
- [ ] Code review aprobado
- [ ] QA notificado

### ✅ 7.2 Deploy a Staging

```bash
# Deploy a staging
git push origin develop
# Esperar CI/CD
```

- [ ] Deploy exitoso a staging
- [ ] Tests de humo pasan
- [ ] Logs sin errores

### ✅ 7.3 Validación en Staging

- [ ] Endpoint de pagos funciona
- [ ] PDFs se generan correctamente
- [ ] Performance aceptable
- [ ] No hay memory leaks

### ✅ 7.4 Deploy a Producción

- [ ] Aprobación de QA recibida
- [ ] Ventana de deployment coordinada
- [ ] Rollback plan preparado

```bash
# Deploy a producción
git checkout main
git merge develop
git push origin main
```

- [ ] Deploy exitoso
- [ ] Monitoring sin alertas
- [ ] Logs limpios

---

## Fase 8: Post-Deployment (24 horas)

### ✅ 8.1 Monitoring (primeras 24 horas)

#### Métricas a monitorear:

- [ ] Response time de endpoints de pagos
  - Esperado: Similar o mejor que antes
  - Actual: _______

- [ ] Error rate
  - Esperado: <0.1%
  - Actual: _______

- [ ] Throughput
  - Esperado: Similar a antes
  - Actual: _______

- [ ] Regeneración de PDFs
  - ¿Cuántos PDFs se regeneraron?: _______
  - ¿Hubo errores?: _______

#### Logs a revisar:

```bash
# Ver logs de errores
tail -f logs/errors.log | grep PaymentHistoryService

# Ver logs de regeneración de PDFs
tail -f logs/app.log | grep "PDF regenerado"
```

- [ ] No hay errores críticos
- [ ] Logs informativos correctos
- [ ] Warnings esperados documentados

### ✅ 8.2 Feedback del equipo

- [ ] Desarrolladores reportan funcionamiento correcto
- [ ] QA no reporta bugs relacionados
- [ ] Usuarios no reportan problemas

---

## Rollback Plan

Si algo sale mal, seguir estos pasos:

### 🚨 Paso 1: Identificar el problema
- [ ] Logs revisados
- [ ] Impacto evaluado
- [ ] Decision de rollback tomada

### 🚨 Paso 2: Ejecutar rollback

```bash
# Rollback en git
git checkout main
git revert <commit-hash>
git push origin main

# O deploy del commit anterior
# (según proceso de deployment)
```

- [ ] Rollback ejecutado
- [ ] Versión anterior funcionando
- [ ] Usuarios notificados

### 🚨 Paso 3: Post-mortem

- [ ] Causa raíz identificada
- [ ] Plan de corrección creado
- [ ] Documento de post-mortem escrito

---

## 📊 Métricas de Éxito

Al final de la migración, deberías tener:

### Código
- [x] 0 dependencias de infraestructura en capa de aplicación
- [x] 100% de servicios con responsabilidad única
- [x] 100% de interfaces implementadas correctamente

### Tests
- [ ] Cobertura de tests: _____ % (objetivo: >80%)
- [ ] Tests unitarios rápidos (<1s)
- [ ] Tests de integración funcionando

### Performance
- [ ] Response time: ≤ versión anterior
- [ ] Error rate: ≤ 0.1%
- [ ] CPU/Memory: similar o menor

### Documentación
- [x] Guía de migración completa
- [x] Arquitectura documentada
- [x] Ejemplos de uso creados
- [x] Tests de ejemplo creados

---

## ✅ Sign-off Final

- [ ] Todas las fases completadas
- [ ] No hay issues abiertos críticos
- [ ] Equipo de desarrollo confirma
- [ ] QA confirma
- [ ] Product Owner aprueba

**Fecha de inicio:** _______________  
**Fecha de completación:** _______________  
**Responsable:** _______________  
**Revisor:** _______________

---

## 📞 Contactos de Emergencia

Si tienes problemas durante la migración:

1. **Desarrollador principal:** _______________
2. **Tech Lead:** _______________
3. **DevOps:** _______________

---

## 📚 Referencias

- `REFACTORING_GUIDE.md` - Guía completa de migración
- `ARCHITECTURE.md` - Arquitectura del sistema
- `usage_examples.py` - Ejemplos de uso
- `test_payment_history_service.py` - Tests de referencia

---

**¡Buena suerte con la migración! 🚀**

