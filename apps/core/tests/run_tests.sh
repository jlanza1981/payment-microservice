#!/bin/bash
# Script para ejecutar tests de WebhookEventProcessor
# Uso: ./run_tests.sh [opción]

echo "🧪 Tests de WebhookEventProcessor - LC Mundo"
echo "=============================================="
echo ""

case "$1" in
  "all")
    echo "Ejecutando todos los tests..."
    python manage.py test apps.core.tests.test_webhook_event_processor -v 2
    ;;
  "completed")
    echo "Test: Pago Completado (PAYMENT.CAPTURE.COMPLETED)"
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_completed_success -v 2
    ;;
  "declined")
    echo "Test: Pago Rechazado (PAYMENT.CAPTURE.DECLINED)"
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_declined_sends_notification -v 2
    ;;
  "denied")
    echo "Test: Pago Denegado (PAYMENT.CAPTURE.DENIED)"
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_denied_sends_notification -v 2
    ;;
  "multiple")
    echo "Test: Múltiples Eventos"
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_process_multiple_pending_events -v 2
    ;;
  "failed")
    echo "Tests: Solo pagos fallidos (DECLINED + DENIED)"
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_declined_sends_notification -v 2
    python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_denied_sends_notification -v 2
    ;;
  *)
    echo "Uso: ./run_tests.sh [opción]"
    echo ""
    echo "Opciones disponibles:"
    echo "  all       - Ejecutar todos los tests"
    echo "  completed - Test de pago completado"
    echo "  declined  - Test de pago rechazado"
    echo "  denied    - Test de pago denegado"
    echo "  multiple  - Test de múltiples eventos"
    echo "  failed    - Solo tests de pagos fallidos"
    echo ""
    echo "Ejemplo: ./run_tests.sh completed"
    ;;
esac

