# 🔧 Solución: Configuración de base_url para PDFs

## 🎯 Problema Identificado

Hay confusión entre dos conceptos diferentes:

1. **`BASE_DIR`** (settings) = Directorio del proyecto en el filesystem
   - Ejemplo: `/home/user/project` o `C:\Users\project`
   - **NO es una URL HTTP**

2. **`base_url`** (para WeasyPrint) = URL HTTP base para recursos
   - Ejemplo: `https://example.com` o `http://localhost:8000`
   - Necesario para resolver CSS, imágenes en PDFs

## ❌ Código Actual (Incorrecto)

```python
# apps/billing/tasks.py línea 17
base_url = getattr(settings, 'BASE_DIR')  # ❌ Esto es un PATH, no una URL

# Luego se usa en línea 79
pdf_content, pdf_path = GeneratePDFUseCase(...).execute(
    base_url=str(base_url)  # ❌ Está pasando un path como URL
)
```

**Problema**: `BASE_DIR = '/home/user/project'` **NO** es una URL válida para WeasyPrint.

---

## ✅ Solución Correcta

### Opción 1: Agregar URL_BASE a settings.py (RECOMENDADO)

```python
# settings.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agregar esta configuración
BASE_URL = config('BASE_URL', default='http://localhost:8000')
# En producción: BASE_URL=https://tudominio.com
```

```python
# .env (desarrollo)
BASE_URL=http://localhost:8000

# .env (producción)
BASE_URL=https://tudominio.com
```

### Opción 2: Construir desde DOMAIN_NAME (Usar configuración existente)

```python
# settings.py ya tiene DOMAIN_NAME
DOMAIN_NAME = config('DOMAIN_NAME')  # Ya existe

# Usar esto como base_url
BASE_URL = DOMAIN_NAME  # Reutilizar configuración existente
```

---

## 📝 Implementación

### Paso 1: Agregar configuración a settings.py

```python
# api/settings.py - Agregar después de DOMAIN_NAME (línea ~165)

# URL base para generación de PDFs (recursos estáticos)
BASE_URL = config('BASE_URL', default=DOMAIN_NAME)
```

### Paso 2: Actualizar las vistas para obtener base_url

#### Opción A: Desde request (dinámico - ACTUAL)
```python
from rest_framework.decorators import api_view
from apps.pagos.application.dependencies import get_payment_history_service

@api_view(['GET'])
def get_payment_history(request, student_id):
    service = get_payment_history_service()
    
    # Construir URL base desde el request
    base_url = request.build_absolute_uri('/')[:-1]  # Remover el trailing slash
    # Resultado: https://example.com o http://localhost:8000
    
    payments = service.get_student_payments(
        student_id=student_id,
        base_url=base_url,
        ensure_pdfs=True
    )
    return Response({'payments': payments})
```

#### Opción B: Desde settings (estático - ALTERNATIVA)
```python
from django.conf import settings
from apps.pagos.application.dependencies import get_payment_history_service

@api_view(['GET'])
def get_payment_history(request, student_id):
    service = get_payment_history_service()
    
    # Usar URL configurada en settings
    base_url = settings.BASE_URL
    
    payments = service.get_student_payments(
        student_id=student_id,
        base_url=base_url,
        ensure_pdfs=True
    )
    return Response({'payments': payments})
```

#### Opción C: Híbrida (RECOMENDADA)
```python
from django.conf import settings
from apps.pagos.application.dependencies import get_payment_history_service

@api_view(['GET'])
def get_payment_history(request, student_id):
    service = get_payment_history_service()
    
    # Intentar desde request, fallback a settings
    try:
        base_url = request.build_absolute_uri('/')[:-1]
    except:
        base_url = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)
    
    payments = service.get_student_payments(
        student_id=student_id,
        base_url=base_url,
        ensure_pdfs=True
    )
    return Response({'payments': payments})
```

---

## 🔧 Corrección del Código Existente

### Arreglar billing/tasks.py

```python
# apps/billing/tasks.py

# ❌ ANTES (Incorrecto)
base_url = getattr(settings, 'BASE_DIR')

# ✅ DESPUÉS (Correcto)
base_url = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)
```

---

## 🎯 Casos de Uso

### 1. En Vistas DRF (HTTP Request disponible)
```python
@api_view(['GET'])
def my_view(request):
    base_url = request.build_absolute_uri('/')[:-1]
    # base_url = "https://example.com"
```

### 2. En Celery Tasks (Sin HTTP Request)
```python
@shared_task
def my_task():
    from django.conf import settings
    base_url = settings.BASE_URL
    # base_url = "https://example.com"
```

### 3. En Management Commands (Sin HTTP Request)
```python
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        base_url = settings.BASE_URL
        # base_url = "https://example.com"
```

---

## ✅ Checklist de Implementación

1. **Configuración**
   - [ ] Agregar `BASE_URL` a `settings.py`
   - [ ] Agregar `BASE_URL` a `.env` (desarrollo y producción)
   - [ ] Verificar que `DOMAIN_NAME` ya existe y tiene valor correcto

2. **Corrección de código existente**
   - [ ] Corregir `apps/billing/tasks.py` línea 17
   - [ ] Verificar otros usos de `BASE_DIR` como URL

3. **Actualización de vistas**
   - [ ] Actualizar vistas para pasar `base_url` correctamente
   - [ ] Usar `request.build_absolute_uri('/')` o `settings.BASE_URL`

4. **Testing**
   - [ ] Probar generación de PDFs en desarrollo
   - [ ] Verificar que CSS/imágenes se resuelven correctamente
   - [ ] Probar en staging antes de producción

---

## 🚨 IMPORTANTE

**NO uses `BASE_DIR` para WeasyPrint**:
- ❌ `BASE_DIR = '/home/user/project'` → NO es una URL
- ✅ `BASE_URL = 'https://example.com'` → Correcto

**NO confundas con `MEDIA_ROOT`**:
- ❌ `MEDIA_ROOT = '/path/to/media_cluster/'` → Es donde se GUARDAN archivos
- ✅ `BASE_URL = 'https://example.com'` → Es para CARGAR CSS/imágenes

**WeasyPrint necesita una URL HTTP** para:
- Resolver archivos CSS desde STATIC_ROOT
- Cargar imágenes desde STATIC_ROOT
- Generar links en el PDF

**MEDIA_ROOT es diferente:**
- Es el path del filesystem donde se GUARDAN los PDFs generados
- Puede estar en cualquier ubicación del disco
- No lo usa WeasyPrint para cargar recursos

**Diagrama:**
```
WeasyPrint:
  base_url → http://localhost:8000 → Carga CSS desde STATIC_ROOT
  
Sistema:
  MEDIA_ROOT → /path/to/media/ → Guarda PDF generado
```

**Ver:** `MEDIA_ROOT_VS_BASE_URL.md` para más detalles.

---

## 📚 Referencias

- WeasyPrint docs: https://weasyprint.readthedocs.io/
- Django build_absolute_uri: https://docs.djangoproject.com/en/stable/ref/request-response/

---

**Fecha:** Marzo 16, 2026  
**Autor:** GitHub Copilot

