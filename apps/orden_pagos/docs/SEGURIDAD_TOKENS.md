# 🔒 Seguridad en Validación de Tokens de Pago

## ⚠️ Problema Identificado

El endpoint `/api/v1/payment-orders/validate-token/` es **público** (sin autenticación) porque debe ser accesible desde la website para estudiantes que reciben un enlace de pago por email.

**Riesgo:** Cualquier persona con acceso a internet podría intentar ataques de fuerza bruta o validación masiva de tokens.

---

## ✅ Medidas de Seguridad Implementadas

### 1. **Rate Limiting (Límite de Intentos)**

**Implementación:** `rate_limiting.py`

```python
@rate_limit(requests_per_minute=5, requests_per_hour=20)
@router.post("/validate-token/", auth=None)
```

**Protección:**
- ✅ **5 intentos por minuto** por IP
- ✅ **20 intentos por hora** por IP
- ✅ Usa cache de Django (Redis/Memcached en producción)
- ✅ Bloquea IPs sospechosas automáticamente
- ✅ Retorna HTTP 429 (Too Many Requests) con `retry_after`

**Ejemplo de respuesta bloqueada:**
```json
{
  "error": "Demasiados intentos. Por favor, intente más tarde.",
  "retry_after": 45,
  "message": "Has excedido el límite de intentos. Intenta nuevamente en 45 segundos."
}
```

---

### 2. **Tokens Firmados Criptográficamente**

**Implementación:** `PaymentTokenService` usando `itsdangerous`

```python
URLSafeTimedSerializer(
    secret_key=settings.SECRET_KEY,
    salt='payment-order-token'
)
```

**Protección:**
- ✅ **No se pueden falsificar** - Firmados con SECRET_KEY de Django
- ✅ **No se pueden modificar** - Cualquier alteración invalida la firma
- ✅ **Contienen datos encriptados** - order_id + fecha de expiración
- ✅ **Stateless** - No necesitan almacenamiento en BD

**Ejemplo de token:**
```
eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNC0wMS0xNVQwMDowMDowMCJ9.XYZ...
```

---

### 3. **Validación de Expiración Temporal**

**Implementación:** `validate_token()` en `PaymentTokenService`

```python
if datetime.now() > expires_at:
    raise ValueError('El enlace de pago ha expirado')
```

**Protección:**
- ✅ **Tokens tienen vida útil limitada** (24-48 horas por defecto)
- ✅ **Auto-expiración** - No se pueden usar después de la fecha límite
- ✅ **Configuración flexible** - Se puede ajustar el tiempo de vida

---

### 4. **Validación de Estado de Orden**

**Implementación:** `ValidatePaymentTokenUseCase`

```python
# Validar que la orden pueda recibir pagos
if payment_order.status == 'CANCELLED':
    raise ValidationError('Orden cancelada')

if payment_order.status in ('PAID', 'VERIFIED'):
    raise ValidationError('Orden ya pagada')

if payment_order.consumed:
    raise ValidationError('Enlace ya utilizado')
```

**Protección:**
- ✅ **Validación de estado** - Solo órdenes PENDING/ACTIVE son válidas
- ✅ **Prevención de re-uso** - Flag `consumed` evita uso múltiple
- ✅ **Validación de existencia** - Verifica que la orden exista en BD

---

### 5. **Información Mínima Expuesta**

**Implementación:** Solo se retorna información necesaria

```json
{
  "valid": true,
  "payment_order": {
    "order_number": "ORD-2024-001",
    "student_name": "Juan Pérez",
    "total_order": 1000.00,
    "balance_due": 500.00,
    "allows_partial_payment": true
  },
  "expires_at": "2024-01-15",
  "message": "Token válido"
}
```

**Protección:**
- ✅ **No expone IDs internos sensibles** (estudiante, asesor, etc.)
- ✅ **Solo datos necesarios para el pago**
- ✅ **No expone información de otros pagos**

---

## 🛡️ Arquitectura de Seguridad

```
┌─────────────────────────────────────────────────────────────┐
│ 1. REQUEST                                                   │
│    POST /api/v1/payment-orders/validate-token/              │
│    Body: { "token": "abc123..." }                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. RATE LIMITING (5/min, 20/hora por IP)                    │
│    ✓ Verifica intentos previos en cache                     │
│    ✓ Bloquea si excede límites → 429 Too Many Requests      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. VALIDACIÓN DE FIRMA (itsdangerous)                       │
│    ✓ Verifica firma criptográfica                           │
│    ✓ Detecta manipulación → 400 Bad Request                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. VALIDACIÓN DE EXPIRACIÓN                                 │
│    ✓ Compara datetime.now() vs expires_at                   │
│    ✓ Token expirado → 400 Token Expired                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. VALIDACIÓN EN BASE DE DATOS                              │
│    ✓ Orden existe                                           │
│    ✓ Estado válido (PENDING/ACTIVE)                         │
│    ✓ No consumida                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. RESPONSE EXITOSA                                          │
│    200 OK - Información de orden para pago                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Comparación con Autenticación

### Opción A: Sin Autenticación (Actual) ✅

**Pros:**
- ✅ Experiencia de usuario simple (click en email → pagar)
- ✅ No requiere login del estudiante
- ✅ Compatible con enlaces en emails
- ✅ Funciona incluso si el estudiante no tiene cuenta

**Contras:**
- ⚠️ Endpoint público expuesto a internet
- ⚠️ Posible target para ataques automatizados

**Mitigación:**
- ✅ Rate limiting agresivo
- ✅ Tokens firmados imposibles de falsificar
- ✅ Expiración automática
- ✅ Monitoreo de intentos fallidos

---

### Opción B: Con Autenticación ❌

**Pros:**
- ✅ Mayor seguridad percibida
- ✅ Endpoint protegido por login

**Contras:**
- ❌ **Estudiante debe estar logueado**
- ❌ **Experiencia de usuario pobre** (click en email → login → pagar)
- ❌ **No funciona si el estudiante olvidó su contraseña**
- ❌ **No funciona para pagos de invitados/prospectos**
- ❌ **Más fricción = menos conversión de pagos**

---

## 🎯 Recomendación Final

**✅ MANTENER SIN AUTENTICACIÓN CON PROTECCIONES ADICIONALES**

### Justificación:

1. **Seguridad Adecuada:**
   - Token firmado = **imposible de falsificar**
   - Rate limiting = **protección contra fuerza bruta**
   - Expiración = **ventana de ataque limitada**

2. **Experiencia de Usuario:**
   - Click directo desde email → formulario de pago
   - Sin fricción de login
   - Mayor conversión de pagos

3. **Casos de Uso Reales:**
   - Estudiantes sin cuenta aún
   - Estudiantes que olvidaron contraseña
   - Pagos urgentes (becas, inscripciones)

4. **Casos de Uso Similares en la Industria:**
   - **Stripe Payment Links** - Sin autenticación, protegidos por token
   - **PayPal Payment Links** - Sin autenticación
   - **Mercado Pago** - Enlaces de pago públicos
   - **Stripe Checkout Sessions** - Token único por sesión

---

## 🚨 Monitoreo Recomendado

### 1. Alertas de Seguridad

Configurar alertas para:
- ❌ Más de 50 intentos fallidos en 1 hora (posible ataque)
- ❌ Misma IP con múltiples tokens inválidos
- ❌ Picos de tráfico anormales en el endpoint

### 2. Logs de Auditoría

Registrar:
- ✅ IP del cliente
- ✅ Token usado (parcial, ej: "abc...xyz")
- ✅ Resultado de validación (éxito/fallo)
- ✅ Timestamp
- ✅ User-Agent

### 3. Métricas

Monitorear:
- 📊 Tasa de intentos fallidos vs exitosos
- 📊 Cantidad de bloqueos por rate limiting
- 📊 Tokens expirados usados (intentos tardíos)

---

## 🔧 Configuración Adicional (Producción)

### 1. Usar Redis para Rate Limiting

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 2. Configurar Firewall (CloudFlare, AWS WAF, etc.)

- Bloquear IPs con comportamiento sospechoso
- Rate limiting a nivel de infraestructura
- Protección DDoS

### 3. HTTPS Obligatorio

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 📝 Conclusión

El endpoint `validate-token` **es seguro sin autenticación** gracias a:

1. ✅ **Rate Limiting**: 5 intentos/minuto, 20/hora
2. ✅ **Tokens firmados**: Imposible de falsificar
3. ✅ **Expiración temporal**: Ventana limitada de ataque
4. ✅ **Validación de estado**: Solo órdenes válidas
5. ✅ **Información mínima**: No expone datos sensibles

**Esta arquitectura es la misma que usan Stripe, PayPal y Mercado Pago** para sus enlaces de pago públicos.

---

## 📚 Referencias

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Django itsdangerous - Token Signing](https://itsdangerous.palletsprojects.com/)
- [Stripe Payment Links Security](https://stripe.com/docs/payments/payment-links/security)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

