// ============================================================================
// EJEMPLO DE INTEGRACIÓN FRONTEND - VALIDACIÓN DE TOKEN DE PAGO
// ============================================================================

/**
 * Servicio para validar tokens de pago
 */
class PaymentTokenService {
  constructor(baseURL = '/api/v1/payment-orders') {
    this.baseURL = baseURL;
  }

  /**
   * Valida un token de enlace de pago
   *
   * @param {string} token - Token extraído de la URL
   * @returns {Promise<Object>} - Datos de la orden o error
   */
  async validateToken(token) {
    try {
      const response = await fetch(`${this.baseURL}/validate-token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
      });

      const data = await response.json();

      if (response.ok) {
        return {
          success: true,
          data: data
        };
      } else if (response.status === 400 && data.expired) {
        return {
          success: false,
          expired: true,
          message: data.message || 'El enlace de pago ha expirado.'
        };
      } else {
        return {
          success: false,
          expired: false,
          message: data.message || 'Error al validar el token.'
        };
      }
    } catch (error) {
      console.error('Error validando token:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Genera un nuevo enlace de pago (requiere autenticación)
   *
   * @param {number} orderId - ID de la orden de pago
   * @param {number} daysValid - Días de validez del token (default 7)
   * @param {string} authToken - Token de autenticación del asesor
   * @returns {Promise<Object>} - Enlace generado
   */
  async generatePaymentLink(orderId, daysValid = 7, authToken) {
    try {
      const response = await fetch(
        `${this.baseURL}/by-id/${orderId}/generate-payment-link/?days_valid=${daysValid}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          }
        }
      );

      const data = await response.json();

      if (response.ok) {
        return {
          success: true,
          data: data
        };
      } else {
        return {
          success: false,
          error: data.error || 'Error al generar enlace'
        };
      }
    } catch (error) {
      console.error('Error generando enlace:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// ============================================================================
// COMPONENTE REACT - Página de Pago del Estudiante
// ============================================================================

/**
 * Componente: Página de pago del estudiante
 * URL: /pay/{token}/
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function PaymentPage() {
  const { token } = useParams(); // Extraer token de la URL
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [orderData, setOrderData] = useState(null);
  const [error, setError] = useState(null);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    validatePaymentToken();
  }, [token]);

  const validatePaymentToken = async () => {
    const service = new PaymentTokenService();
    const result = await service.validateToken(token);

    setLoading(false);

    if (result.success) {
      // Token válido - mostrar formulario de pago
      setOrderData(result.data);
    } else if (result.expired) {
      // Token expirado - mostrar mensaje
      setExpired(true);
      setError(result.message);
    } else {
      // Otro error
      setError(result.message || 'No se pudo validar el enlace de pago.');
    }
  };

  if (loading) {
    return <div>Validando enlace de pago...</div>;
  }

  if (expired) {
    return (
      <div className="alert alert-warning">
        <h3>⚠️ Enlace Expirado</h3>
        <p>{error}</p>
        <p>Por favor, contacte a su asesor para obtener un nuevo enlace.</p>
        <button onClick={() => navigate('/')}>Volver al inicio</button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <h3>❌ Error</h3>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Volver al inicio</button>
      </div>
    );
  }

  return (
    <div className="payment-page">
      <h2>Orden de Pago: {orderData.order_number}</h2>

      <div className="student-info">
        <h3>Información del Estudiante</h3>
        <p><strong>Nombre:</strong> {orderData.student_name}</p>
        <p><strong>Email:</strong> {orderData.student_email}</p>
      </div>

      <div className="order-info">
        <h3>Detalles de la Orden</h3>
        <p><strong>Monto Total:</strong> ${orderData.total_amount}</p>
        <p><strong>Saldo Pendiente:</strong> ${orderData.balance_due}</p>

        {orderData.allows_partial_payment && (
          <>
            <p><strong>Monto Mínimo:</strong> ${orderData.minimum_payment_amount}</p>
            <p><strong>Monto Sugerido:</strong> ${orderData.suggested_payment_amount}</p>
            <p className="text-info">✓ Esta orden permite pagos parciales</p>
          </>
        )}

        <p><strong>Válido hasta:</strong> {new Date(orderData.expires_at).toLocaleDateString()}</p>
      </div>

      {/* Aquí va tu formulario de pago */}
      <PaymentForm
        orderId={orderData.order_id}
        balanceDue={orderData.balance_due}
        allowsPartial={orderData.allows_partial_payment}
        minAmount={orderData.minimum_payment_amount}
        suggestedAmount={orderData.suggested_payment_amount}
      />
    </div>
  );
}

// ============================================================================
// COMPONENTE REACT - Panel del Asesor (Generar Enlace)
// ============================================================================

/**
 * Componente: Botón para generar enlace de pago
 */
function GeneratePaymentLinkButton({ orderId, authToken, onSuccess }) {
  const [loading, setLoading] = useState(false);

  const handleGenerateLink = async () => {
    setLoading(true);

    const service = new PaymentTokenService();
    const result = await service.generatePaymentLink(orderId, 7, authToken);

    setLoading(false);

    if (result.success) {
      alert(`Enlace generado: ${result.data.payment_link}`);

      // Copiar al portapapeles
      navigator.clipboard.writeText(result.data.payment_link);

      if (onSuccess) {
        onSuccess(result.data);
      }
    } else {
      alert(`Error: ${result.error}`);
    }
  };

  return (
    <button
      onClick={handleGenerateLink}
      disabled={loading}
      className="btn btn-primary"
    >
      {loading ? 'Generando...' : 'Generar Enlace de Pago'}
    </button>
  );
}

// ============================================================================
// VUE.JS - Composable para Validación de Token
// ============================================================================

/**
 * Composable de Vue 3 para validar tokens de pago
 */
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

export function usePaymentToken() {
  const route = useRoute();
  const router = useRouter();

  const loading = ref(true);
  const orderData = ref(null);
  const error = ref(null);
  const expired = ref(false);

  const validateToken = async (token) => {
    try {
      const response = await fetch('/api/v1/payment-orders/validate-token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      const data = await response.json();

      if (response.ok) {
        orderData.value = data;
        return true;
      } else if (response.status === 400 && data.expired) {
        expired.value = true;
        error.value = data.message;
        return false;
      } else {
        error.value = data.message || 'Error validando el token';
        return false;
      }
    } catch (err) {
      error.value = 'Error de conexión';
      return false;
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    const token = route.params.token;
    if (token) {
      validateToken(token);
    }
  });

  return {
    loading,
    orderData,
    error,
    expired,
    validateToken
  };
}

// Uso en componente Vue
// <script setup>
// import { usePaymentToken } from '@/composables/usePaymentToken';
//
// const { loading, orderData, error, expired } = usePaymentToken();
// </script>

// ============================================================================
// ANGULAR - Service para Validación de Token
// ============================================================================

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PaymentTokenService {
  private baseURL = '/api/v1/payment-orders';

  constructor(private http: HttpClient) {}

  validateToken(token: string): Observable<any> {
    return this.http.post(`${this.baseURL}/validate-token/`, { token });
  }

  generatePaymentLink(orderId: number, daysValid: number = 7): Observable<any> {
    return this.http.post(
      `${this.baseURL}/by-id/${orderId}/generate-payment-link/?days_valid=${daysValid}`,
      {}
    );
  }
}

// Uso en componente
export class PaymentComponent implements OnInit {
  constructor(
    private route: ActivatedRoute,
    private paymentTokenService: PaymentTokenService
  ) {}

  ngOnInit() {
    const token = this.route.snapshot.params['token'];

    this.paymentTokenService.validateToken(token).subscribe({
      next: (data) => {
        this.orderData = data;
        this.showPaymentForm = true;
      },
      error: (err) => {
        if (err.status === 400 && err.error.expired) {
          this.showExpiredMessage = true;
        } else {
          this.errorMessage = err.error.message;
        }
      }
    });
  }
}

// ============================================================================
// CURL - Ejemplos de Testing
// ============================================================================

# 1. Generar enlace de pago (como asesor)
curl -X POST "http://localhost:8000/api/v1/payment-orders/123/generate-payment-link/?days_valid=7" \
  -H "Authorization: Bearer TU_TOKEN_ASESOR" \
  -H "Content-Type: application/json"

# Response:
# {
#   "success": true,
#   "token": "eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9...",
#   "payment_link": "https://lc.com/pay/eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9.../"
# }

# 2. Validar token (público, sin auth)
curl -X POST "http://localhost:8000/api/v1/payment-orders/validate-token/" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJvcmRlcl9pZCI6MTIzLCJleHBpcmVzX2F0IjoiMjAyNS0wMS0xNVQwMDowMDowMCJ9..."
  }'

# Response válido:
# {
#   "valid": true,
#   "order_id": 123,
#   "order_number": "PO-2025-00123",
#   "balance_due": 1500.00,
#   "allows_partial_payment": true
# }

# Response expirado:
# {
#   "valid": false,
#   "expired": true,
#   "message": "El enlace de pago ha expirado. Por favor, contacte a su asesor."
# }

