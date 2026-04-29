# DIAGRAMA DE FLUJO - TOKENS CIFRADOS DE PAGO

## Flujo Visual Completo

### 1. Asesor Genera Enlace
```
POST /api/v1/payment-orders/123/generate-payment-link/
  → GeneratePaymentLinkUseCase
  → Token firmado generado
  → Response: { token, payment_link, expires_at }
```

### 2. Estudiante Recibe Email
```
Email con: https://lc.com/pay/{token}/
```

### 3. Frontend Valida Token
```
POST /api/v1/payment-orders/validate-token/
  → ValidatePaymentTokenUseCase
  → Token decodificado (order_id extraído)
  → PaymentOrder.objects.get(id=order_id)
  → Response: { valid: true, order_data }
```

### 4. Frontend Muestra Formulario
```
Si válido: Mostrar formulario de pago
Si expirado: Mostrar mensaje de contactar asesor
```

## Ventajas Implementadas

1. Busqueda por PRIMARY KEY (mas rapido)
2. No almacena tokens en BD
3. Firma criptografica (seguro)
4. Stateless y escalable

