# 🚀 GUÍA RÁPIDA - ENDPOINTS DE TOKENS DE PAGO

## 📦 Instalación

### 1. Instalar dependencia
```bash
pip install itsdangerous==2.1.2
```

### 2. Verificar instalación
```bash
python test_payment_token.py
```

---

## 🔌 Endpoints Implementados

### 1️⃣ Validar Token (Público)

```http
POST /api/v1/payment-orders/validate-token/
Content-Type: application/json

{
  "token": "eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9..."
}
```

**Respuesta exitosa:**
```json
{
  "valid": true,
  "message": "Token válido. Puede proceder con el pago.",
  "order_id": 123,
  "order_number": "PO-2025-00123",
  "student_name": "Juan Pérez",
  "total_amount": 1500.00,
  "balance_due": 1500.00,
  "allows_partial_payment": true,
  "expires_at": "2025-01-15"
}
```

### 2️⃣ Generar Enlace (Autenticado)

```http
POST /api/v1/payment-orders/123/generate-payment-link/?days_valid=7
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "success": true,
  "token": "eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9...",
  "payment_link": "https://lc.com/pay/eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9.../",
  "expires_at": "2025-01-15",
  "order_id": 123,
  "order_number": "PO-2025-00123"
}
```

---

## 💡 Ventajas del Token Cifrado

✅ **No se guarda en BD** - Solo la fecha de expiración  
✅ **Búsqueda por ID** - Más rápido que buscar por token  
✅ **Firma criptográfica** - No puede ser manipulado  
✅ **Stateless** - No requiere sincronización  

---

## 📖 Documentación Completa

Ver: `apps/orden_pagos/docs/IMPLEMENTACION_TOKENS_CIFRADOS.md`

