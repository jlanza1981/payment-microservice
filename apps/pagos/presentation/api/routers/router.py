import logging

from django.http import HttpRequest

from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from ninja import Router, Query
from api.DRF.pagination import paginate as custom_paginate
from apps.orden_pagos.presentation.api.routers.exonerated_payment_router import invoice_repository
from apps.orden_pagos.tasks import send_payment_notification as send_payment_notification_task

from apps.pagos.application.use_cases.capture_order_paypal import CreateCaptureOrderPaypalUseCase
from apps.pagos.application.use_cases.create_partial_payment import CreatePartialPaymentUsoCase
from apps.pagos.application.use_cases.create_payment_paypal import CreatePaymentPaypalUseCase
from apps.pagos.application.use_cases.student_payment_history import StudentPaymentHistoryUseCase
from apps.pagos.application.utils import get_domain_name
from apps.pagos.infrastructure.paypal.paypal_gateway import PayPalGateway
from apps.pagos.infrastructure.repository.legacy_payment_repository import LegacyPaymentRepository
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.presentation.api.schemas.filter_schemas import PaymentFilterSchema
from apps.pagos.presentation.api.schemas.input_paypal_schemas import CreateOrderPaypalSchema, CaptureOrderPaypalSchema
from apps.pagos.presentation.api.schemas.input_schemas import PartialPaymentInputSchema
from apps.pagos.presentation.api.schemas.output_schemas import PaginatedListSchema, StudentPaymentHistorySchema

logger = logging.getLogger(__name__)
router = Router(tags=["Payments"], auth=None)
payment_order_repository = PaymentOrderRepository()

payment_repository = PaymentRepository()
legacy_payment_repository = LegacyPaymentRepository()

@router.post("/paypal/create-order/")
def create_order(request, payload: CreateOrderPaypalSchema):
    payment_order = GetPaymentOrderByIdUseCase(payment_order_repository).execute(payload.payment_order_id)
    if payment_order.suggested_payment_amount is not None and payment_order.suggested_payment_amount > 0:
        amount = payment_order.suggested_payment_amount
    else:
        amount = payment_order.total_order

    result = CreatePaymentPaypalUseCase(PayPalGateway()).execute(
        amount=amount,
        currency=payment_order.currency,
        payment_order=payment_order.id
    )
    result['payment_order_id'] = payment_order.id
    return result

@router.post("/paypal/capture-order/")
def capture_order(request, payload: CaptureOrderPaypalSchema):
    result = CreateCaptureOrderPaypalUseCase(PayPalGateway()).execute(order_id=payload.order_id)
    return result

@router.get("/list/{student_id}/", response=PaginatedListSchema, summary="Listar pagos del estudiante")
def list_payments(
      request: HttpRequest,
      student_id: int,
      filters: PaymentFilterSchema = Query(...),
):
    # Construir diccionario de filtros
    filter_dict = {}
    
    if filters.invoice_number:
        filter_dict['invoice_number'] = filters.invoice_number
    if filters.created_from:
        filter_dict['date_from'] = filters.created_from.isoformat()
    if filters.created_to:
        filter_dict['date_to'] = filters.created_to.isoformat()
    # Obtener queryset filtrado
    domain_name = get_domain_name()
    queryset = StudentPaymentHistoryUseCase(payment_repository, legacy_payment_repository).execute(student_id, filter_dict, domain_name)

    # Usar los valores de paginación del schema
    page = filters.page
    per_page = filters.per_page

    paginated_data = custom_paginate(queryset, request, page, per_page)
   
    # Convertir a schemas y luego a diccionarios para mantener el esquema de paginación genérico
    results = [StudentPaymentHistorySchema.from_orm(obj).model_dump() for obj in paginated_data['results']]
    return {
        'count': paginated_data.get('count', len(results)),
        'next': paginated_data.get('next'),
        'previous': paginated_data.get('previous'),
        'results': results,
    }

@router.post("/create-partial-payment/", response={200: dict, 400: dict, 500: dict},
             summary="Crear pago parcial")
def create_partial_payment(
      request: HttpRequest,
      payload: PartialPaymentInputSchema,
):
    payment_order = CreatePartialPaymentUsoCase(invoice_repository, payment_order_repository).execute(payload.invoice, payload.amount)
    task_id = None
    message = f'El enlace de pago de abono para la orden {payment_order.order_number} se ha enviado.'
    try:
        result = send_payment_notification_task.delay(
            order_id=payment_order.id
        )
        task_id = result.id

    except Exception as email_error:
        # ⚠️ Si falla el email, loguear pero NO revertir la orden
        print(f"Error al enviar email: {email_error}")
        message = f'El enlace de pago de abono para la orden {payment_order.order_number} no se ha enviado.'

    return 200, {

        'task_id': task_id,
        'message': message,
    }