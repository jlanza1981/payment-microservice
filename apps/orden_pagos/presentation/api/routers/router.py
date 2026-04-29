"""
Router principal de Django Ninja para órdenes de pago.
Migración de PaymentOrderViewSet a Django Ninja.
"""

import logging
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from ninja import Router, Query
from rest_framework.exceptions import ValidationError

from api.DRF.pagination import paginate as custom_paginate
from apps.administrative_cost_type.application.use_cases.get_type_administrative_cost import \
    GetTypeAdministrativeCostUseCase

from apps.core.infrastructure.security.auth_bearer import AuthBearer
from apps.orden_pagos.application.commands import (
    CreatePaymentOrderCommand,
    UpdatePaymentOrderCommand,
    DeletePaymentOrderCommand,
    VerifyOrderCommand,
)
from apps.orden_pagos.application.use_cases import (
    CreatePaymentOrderUseCase,
    UpdatePaymentOrderUseCase,
    GetPaymentOrderByIdUseCase,
    GetPaymentOrderByNumberUseCase,
    ListPaymentOrdersUseCase,
    CancelOrderUseCase,
    VerifyOrderUseCase,
    ValidatePaymentTokenUseCase, GetConceptByIdUseCase,
)
from apps.orden_pagos.application.use_cases.list_payment_orders_student import ListPaymentOrdersStudentUseCase
from apps.orden_pagos.domain.interface.services import PaymentOrderDomainService
from apps.orden_pagos.infrastructure.repository.category_repository import CategoryRepository
from apps.orden_pagos.infrastructure.repository.city_repository import CityRepository
from apps.orden_pagos.infrastructure.repository.country_repository import CountryRepository
from apps.orden_pagos.infrastructure.repository.institution_repository import InstitutionRepository
from apps.orden_pagos.infrastructure.repository.material_cost_type_repository import MaterialCostTypeRepository
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.infrastructure.repository.program_repository import ProgramRepository
from apps.orden_pagos.infrastructure.services.payment_token_service import PaymentTokenService
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.orden_pagos.tasks import send_payment_notification as send_payment_notification_task
from apps.orden_pagos.presentation.api.rate_limiting import rate_limit
from .administrative_cost_router import administrative_costs_router
from .exonerated_payment_router import exonerated_router
from .payment_concept_router import payment_concepts_router, repository_administrative_cost
from .payment_structure_router import payment_structures_router
from apps.orden_pagos.presentation.api.schemas import (
    # Input schemas
    CreatePaymentOrderSchema,
    VerifyOrderSchema,
    MinimalUpdatePaymentOrderSchema,
    ValidatePaymentTokenInputSchema,
    # Output schemas
    PaymentOrderSchema,
    PaymentOrderListSchema,
    PaginatedPaymentOrderListSchema,
    PaymentOrderResponseSchema,
    ValidatePaymentTokenOutputSchema,
    TokenExpiredErrorSchema,
    # Filter schemas
    PaymentOrderFilterSchema,
    PaymentStructureSchema,
)
logger = logging.getLogger(__name__)
# Crear router con autenticación
router = Router(tags=["Payment Orders"], auth=AuthBearer())

# Instancias de servicios
domain_service = PaymentOrderDomainService()
repository_payment_order = PaymentOrderRepository()
repository_payment_concept = PaymentConceptRepository()
token_service = PaymentTokenService()

# ============================================================================
# IMPORTANTE: Registrar sub-routers con rutas específicas ANTES de rutas dinámicas
# Esto evita que rutas como /{order_id}/ capturen URLs como /payment-concepts/
# ============================================================================


# Registrar el sub-router de conceptos de pago ANTES de las rutas dinámicas
router.add_router("/payment-concepts", payment_concepts_router)

# Registrar el sub-router de estructuras de pago
router.add_router("/payment-structures", payment_structures_router)

# Registrar el sub-router de costos administrativos
router.add_router("/administrative-costs", administrative_costs_router)

# Registrar el sub-router de pagos exonerados
router.add_router("/exonerated", exonerated_router)


# ============================================================================
# Endpoints de tokens de pago (rutas públicas sin autenticación)
# ============================================================================

@rate_limit(requests_per_minute=5, requests_per_hour=20)  # Límite: 5 intentos/minuto, 20/hora
@router.post("/validate-token/",
             response={200: ValidatePaymentTokenOutputSchema, 400: TokenExpiredErrorSchema, 404: dict, 429: dict, 500: dict},
             summary="Validar token de enlace de pago",
             auth=None)  # Sin autenticación - endpoint público
def validate_payment_token(
    request: HttpRequest,
    payload: ValidatePaymentTokenInputSchema,
):
    """
    Valida el token de un enlace de pago y retorna la información de la orden.
    ⚠️ SEGURIDAD:
    - Rate limiting: 5 intentos por minuto, 20 por hora por IP
    - Token firmado criptográficamente (no se puede falsificar)
    - Validación de expiración (24-48 horas por defecto)
    - Validación de estado de orden
    """
    logger.info(f'Validando token de pago: {payload.token[:20]}...')

    try:
        # Validar token usando el caso de uso
        result = ValidatePaymentTokenUseCase(repository_payment_order, token_service).execute(payload.token)

        logger.info(f'Token válido para orden: {result.get("payment_order", {}).get("order_number")}')

        # Construir respuesta exitosa
        return 200, {
            'valid': result['valid'],
            'message': result['message'],
            'payment_order': result['payment_order'],
            'expires_at': result['expires_at'],
            'status': result.get('status', ''),
        }

    except ValidationError as ve:
        # Errores de validación de DRF
        logger.warning(f'Error de validación en token: {ve.detail}')

        error_detail = ve.detail if isinstance(ve.detail, dict) else {'message': str(ve.detail)}

        # Verificar si es un error de expiración
        if error_detail.get('expired'):
            return 400, {
                'valid': False,
                'expired': True,
                'message': error_detail.get('message', 'El enlace de pago ha expirado. Por favor, contacte a su asesor.'),
                'error': str(error_detail.get('token', ''))
            }

        # Error de validación genérico (orden no encontrada, cancelada, etc.)
        return 400, {
            'valid': False,
            'expired': False,
            'message': error_detail.get('message', 'El token no es válido.'),
            'error': str(error_detail)
        }

    except ValueError as ve:
        # Errores del token service (firma inválida, expirado, etc.)
        logger.warning(f'Error en token service: {str(ve)}')

        return 400, {
            'valid': False,
            'expired': True,
            'message': str(ve),
            'error': 'Token inválido o expirado'
        }

    except Exception as e:
        # Error inesperado
        logger.error(f'Error inesperado validando token: {str(e)}', exc_info=True)

        return 500, {
            'valid': False,
            'error': str(e),
            'message': 'Ocurrió un error interno al validar el token. Por favor, contacte al administrador.'
        }

# ============================================================================
# Endpoints de órdenes de pago (rutas específicas primero, dinámicas después)

# ============================================================================


@router.get("/", response=PaginatedPaymentOrderListSchema, summary="Listar órdenes de pago")
def list_payment_orders(
      request: HttpRequest,
      filters: PaymentOrderFilterSchema = Query(...),
):
    """
    Listar órdenes de pago con filtros y paginación.
    GET /api/v1/payment-orders/
    """
    # Construir diccionario de filtros
    filter_dict = {}

    if filters:
        if filters.order_number:
            filter_dict['order_number'] = filters.order_number
        if filters.status:
            filter_dict['status'] = filters.status
        if filters.student:
            filter_dict['student'] = filters.student
        if filters.advisor:
            filter_dict['advisor'] = filters.advisor
        if filters.opportunity:
            filter_dict['opportunity'] = filters.opportunity
        if filters.quotation:
            filter_dict['quotation'] = filters.quotation
        if filters.created_from:
            filter_dict['date_from'] = filters.created_from.isoformat()
        if filters.created_to:
            filter_dict['date_to'] = filters.created_to.isoformat()

    # Obtener queryset filtrado
    queryset = ListPaymentOrdersUseCase(repository_payment_order).execute(filter_dict)

    page = filters.page if filters else 1
    per_page = filters.per_page if filters else 10

    paginated_data = custom_paginate(queryset, request, page, per_page)

    results = [PaymentOrderListSchema.from_orm(obj) for obj in paginated_data['results']]
    return {
        'count': paginated_data.get('count', len(results)),
        'next': paginated_data.get('next'),
        'previous': paginated_data.get('previous'),
        'results': results,
    }
@router.get("/list/{student_id}/", response=PaginatedPaymentOrderListSchema, summary="Listar órdenes de pago")
def list_payment_orders_student(
      request: HttpRequest,
      student_id: int,
      filters: PaymentOrderFilterSchema = Query(...),
):
    """
    Listar órdenes de pago con filtros y paginación.
    GET /api/v1/payment-orders/
    """
    # Construir diccionario de filtros
    filter_dict = {}

    if filters:
        if filters.order_number:
            filter_dict['order_number'] = filters.order_number
        if filters.status:
            filter_dict['status'] = filters.status
        if filters.student:
            filter_dict['student'] = filters.student
        if filters.advisor:
            filter_dict['advisor'] = filters.advisor
        if filters.opportunity:
            filter_dict['opportunity'] = filters.opportunity
        if filters.quotation:
            filter_dict['quotation'] = filters.quotation
        if filters.created_from:
            filter_dict['date_from'] = filters.created_from.isoformat()
        if filters.created_to:
            filter_dict['date_to'] = filters.created_to.isoformat()

    # Obtener queryset filtrado
    queryset = ListPaymentOrdersStudentUseCase(repository_payment_order).execute(student_id, filter_dict)

    page = filters.page if filters else 1
    per_page = filters.per_page if filters else 10

    paginated_data = custom_paginate(queryset, request, page, per_page)

    results = [PaymentOrderListSchema.from_orm(obj) for obj in paginated_data['results']]
    return {
        'count': paginated_data.get('count', len(results)),
        'next': paginated_data.get('next'),
        'previous': paginated_data.get('previous'),
        'results': results,
    }

@router.post("/", response={201: PaymentOrderResponseSchema, 400: dict, 500: dict}, summary="Crear orden de pago")
def create_payment_order(
      request: HttpRequest,
      payload: CreatePaymentOrderSchema,
      send_link: bool = Query(False, alias="send_payment_link"),
):
    print('payload', payload.dict())
    #try:
    creation_message = 'Orden de pago creada correctamente.'
        #with transaction.atomic():
    send_link_flag = bool(getattr(payload, 'send_payment_link', False) or send_link)

    # Excluir solo send_payment_link del payload, mantener allows_partial_payment y minimum_payment_amount
    payload_dict = payload.dict(exclude={'send_payment_link'})
    payload_dict['status'] = 'PENDING'  # Asegurar estado inicial
    data = CreatePaymentOrderCommand(**payload_dict)
    concept_by_id_uc = GetConceptByIdUseCase(repository_payment_concept)
    type_administrative_cost_uc = GetTypeAdministrativeCostUseCase(repository_administrative_cost)
    result = CreatePaymentOrderUseCase(
        domain_service,
        concept_by_id_uc,
        type_administrative_cost_uc,
        repository_payment_order,
        CategoryRepository(),
        InstitutionRepository(),
        CountryRepository(),
        CityRepository(),
        ProgramRepository(),
        MaterialCostTypeRepository(),
    ).execute(data)

    # 2. Obtener la orden a retornar
    if isinstance(result, list):
        payment_order = result[0]
    else:
        payment_order = result

    # 3. Serializar la orden (puede fallar aquí)
    payment_order_schema = PaymentOrderSchema.from_orm(payment_order)
    # ✅ Si llegamos aquí, todo salió bien → commit automático

    # 4. Enviar enlace de pago DESPUÉS del commit (fuera de la transacción)
    send_link_triggered = False
    task_id = None
    if send_link_flag and payment_order.status == 'PENDING':
        #try:
        base_url = getattr(settings, 'BASE_DIR', request.build_absolute_uri('/'))
        result = send_payment_notification_task.delay(
            order_id=payment_order.id,
            base_url=str(base_url)
        )
        task_id = result.id
        send_link_triggered = True
        # Reemplazar mensaje si se envía el link
        creation_message = f'El enlace de pago para la orden {payment_order.order_number} está siendo enviado.'
        #except Exception as email_error:
            # ⚠️ Si falla el email, loguear pero NO revertir la orden
            #logger.error(f"Error al enviar email para orden {payment_order.id}: {email_error}")

        # Mantener consistencia de respuesta con update: devolver objeto y mensaje
    return 201, {
        'payment_order': payment_order_schema.dict(),
        'message': creation_message,
        'send_link_triggered': send_link_triggered,
        'task_id': task_id,
    }

    #except Exception as e:
        # ❌ Si falla CUALQUIER cosa, rollback automático
        #print(f"Error al crear orden: {e}")
        #return 500, {'error': f'Error al crear la orden de pago: {str(e)}'}


@router.put("/by-id/{order_id}/", response={200: PaymentOrderResponseSchema, 400: dict, 500: dict},
            summary="Actualizar orden de pago")
def update_payment_order(
      request: HttpRequest,
      order_id: int,
      payload: MinimalUpdatePaymentOrderSchema,
      send_link: bool = Query(False, alias="send_payment_link"),
):
    """
    Actualiza SOLO los detalles o el programa de la orden.
    No modifica campos básicos de la orden (student, advisor, etc.).
    Usa order_id de la ruta y payload mínimo en el body.
    """
    try:
        message = 'Orden de pago actualizada correctamente.'
        with transaction.atomic():
            # Flag efectivo: si el body trae send_payment_link lo tomamos; si no, usamos query
            send_link_flag = bool(getattr(payload, 'send_payment_link', False) or send_link)

            # Construir el comando solo con lo necesario
            payload_dict = {
                'order_id': order_id,
                'payment_details': payload.payment_details,
                'program_data': payload.program_data,
                'suggested_payment_amount': payload.suggested_payment_amount,
            }

            data = UpdatePaymentOrderCommand(**payload_dict)
            concept_by_id_uc = GetConceptByIdUseCase(repository_payment_concept)
            type_administrative_cost_uc = GetTypeAdministrativeCostUseCase(repository_administrative_cost)
            payment_order = UpdatePaymentOrderUseCase(
                domain_service,
                concept_by_id_uc,
                type_administrative_cost_uc,
                repository_payment_order,
                CategoryRepository(),
                InstitutionRepository(),
                CountryRepository(),
                CityRepository(),
                ProgramRepository(),
                MaterialCostTypeRepository(),
            ).execute(data)

            # Serializar
            payment_order_schema = PaymentOrderSchema.from_orm(payment_order)

        # Enviar enlace de pago DESPUÉS del commit (fuera de la transacción)
        task_id = None
        send_link_triggered = False
        print('send_link_flag', send_link_flag)
        print('status', payment_order.status)
        if send_link_flag and payment_order.status in ['PENDING', 'ACTIVE']:
            try:
                base_url = getattr(settings, 'BASE_DIR', request.build_absolute_uri('/'))
                result = send_payment_notification_task.delay(
                    order_id=payment_order.id,
                    base_url=str(base_url)
                )

                task_id = result.id
                send_link_triggered = True

                message = f'El enlace de pago para la orden {payment_order.order_number} se ha enviado.'
            except Exception as email_error:
                # ⚠️ Si falla el email, loguear pero NO revertir la orden
                print(f"Error al enviar email: {email_error}")

        return 200, {
            'payment_order': payment_order_schema.dict(),
            'send_link_triggered': send_link_triggered,
            'task_id': task_id,
            'message': message,
        }

    except Exception as e:
        # ❌ Si falla CUALQUIER cosa, rollback automático
        print(f"Error al actualizar orden: {e}")
        return 500, {'error': f'Error al actualizar la orden de pago: {str(e)}'}

@router.get("/by-number/{order_number}/", response=PaymentOrderSchema, summary="Buscar orden por número")
def get_payment_order_by_number(request: HttpRequest, order_number: str):
    """
    Buscar orden de pago por número de orden.
    """
    payment_order = GetPaymentOrderByNumberUseCase(repository_payment_order).execute(order_number)
    return PaymentOrderSchema.from_orm(payment_order)


@router.get("/by-id/{order_id}/", response=PaymentOrderSchema, summary="Obtener orden de pago")
def get_payment_order(request: HttpRequest, order_id: int):
    """
    Obtener una orden de pago específica por ID.
    """
    payment_order = GetPaymentOrderByIdUseCase(repository_payment_order).execute(order_id)
    return PaymentOrderSchema.from_orm(payment_order)


@router.delete("/by-id/{order_id}/", response={200: dict}, summary="Anular orden de pago")
def cancel_payment_order(request: HttpRequest, order_id: int):
    """
    Anular orden de pago (soft delete).

    """
    data = DeletePaymentOrderCommand(order_id=order_id)
    payment_order_by_id_uc = GetPaymentOrderByIdUseCase(repository_payment_order)
    result = CancelOrderUseCase(repository_payment_order, payment_order_by_id_uc).execute(data)

    if result:
        return 200, {'message': 'Orden de pago anulada correctamente'}
    else:
        return 400, {
            'error': 'No se puede anular esta orden. Solo se pueden anular órdenes en estado PENDING.'
        }


@router.post("/by-id/{order_id}/verify/", response=PaymentOrderSchema, summary="Verificar orden de pago")
def verify_order(
      request: HttpRequest,
      order_id: int,
      payload: VerifyOrderSchema,
):
    """
    Verificar una orden de pago por tesorería.

    POST /api/v1/payment-orders/{order_id}/verify/
    """
    command = VerifyOrderCommand(order_id=order_id, **payload.dict())
    payment_order_by_id_uc = GetPaymentOrderByIdUseCase(repository_payment_order)
    payment_order = VerifyOrderUseCase(repository_payment_order, payment_order_by_id_uc).execute(command)
    return PaymentOrderSchema.from_orm(payment_order)



@router.get("/by-id/{order_id}/structure/", response=PaymentStructureSchema, summary="Obtener estructura de orden")
def get_order_structure(request: HttpRequest, order_id: int):
    """
    Obtener estructura completa de la orden en formato JSON.
    Incluye información detallada del programa y conceptos de pago.

    GET /api/v1/payment-orders/{order_id}/structure/
    """
    payment_order = GetPaymentOrderByIdUseCase(repository_payment_order).execute(order_id)
    structure = payment_order.get_order_structure()
    return structure


@router.post("/send-payment-notification/{order_id}/", response={200: dict, 400: dict, 500: dict}, summary="Enviar link de pago")
def send_payment_notification_endpoint(
      request: HttpRequest,
      order_id: int,
      suggested_amount: float = Query(None, description="Monto sugerido para el siguiente abono (opcional)"),
):
    """
    Envía el enlace de pago al estudiante y al asesor por correo electrónico.
    Se puede enviar para órdenes en estado PENDING o ACTIVE.
    """
    payment_order = GetPaymentOrderByIdUseCase(repository_payment_order).execute(order_id)

    if payment_order.status not in ['PENDING', 'ACTIVE']:
        return 400, {
            'error': f'Solo se puede enviar el enlace de pago para órdenes en estado PENDING o ACTIVE. Estado actual: {payment_order.status}'
        }

    base_url = getattr(settings, 'BASE_DIR', request.build_absolute_uri('/'))
    try:
        result = send_payment_notification_task.delay(
            order_id=payment_order.id,
            base_url=str(base_url)
        )

        # Calcular información de progreso
        total_paid = float(payment_order.get_total_paid())
        balance_due = float(payment_order.get_balance_due())
        total_order = float(payment_order.total_order)
        payment_progress_pct = (total_paid / total_order * 100) if total_order > 0 else 0
        payment_count = payment_order.get_payment_count()
        next_payment_number = payment_order.get_next_payment_number()

        return 200, {
            'message': f'El enlace de pago para la orden {payment_order.order_number} está siendo enviado.',
            'order_number': payment_order.order_number,
            'task_id': result.id,
            'student_email': payment_order.student.email,
            'advisor_email': payment_order.advisor.email,
            'suggested_amount': float(payment_order.suggested_payment_amount) if payment_order.suggested_payment_amount else None,
            'payment_info': {
                'total_order': total_order,
                'total_paid': total_paid,
                'balance_due': balance_due,
                'payment_progress_pct': round(payment_progress_pct, 2),
                'payment_count': payment_count,
                'next_payment_number': next_payment_number,
                'is_first_payment': total_paid == 0,
                'allows_partial_payment': payment_order.allows_partial_payment,
            }
        }
    except Exception as e:
        return 500, {'error': f'Error al procesar el envío del enlace de pago: {str(e)}'}
