"""
Endpoint para procesar pagos exonerados (gratuitos).
Permite crear órdenes de pago sin costo y registrar el asiento contable.
"""

from django.db import transaction
from django.http import HttpRequest
from ninja import Router

from apps.administrative_cost_type.application.use_cases.get_type_administrative_cost import \
    GetTypeAdministrativeCostUseCase
from apps.administrative_cost_type.infrastructure.repository.administrative_cost_repository import \
    AdministrativeCostRepository
from apps.billing.application.commands import CreateInvoiceCommand
from apps.billing.application.mappers.invoice_mapper import InvoiceMapper
from apps.billing.application.mappers.payment_mapper import PaymentMapper
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository
from apps.billing.presentation.api.schemas.output_schemas import InvoiceSchema
from apps.core.infrastructure.security.auth_bearer import AuthBearer
from apps.orden_pagos.application.commands import CreatePaymentOrderCommand
from apps.orden_pagos.application.use_cases import CreatePaymentOrderUseCase, GetConceptByIdUseCase, \
    GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.services import PaymentOrderDomainService
from apps.orden_pagos.infrastructure.repository.category_repository import CategoryRepository
from apps.orden_pagos.infrastructure.repository.city_repository import CityRepository
from apps.orden_pagos.infrastructure.repository.country_repository import CountryRepository
from apps.orden_pagos.infrastructure.repository.institution_repository import InstitutionRepository
from apps.orden_pagos.infrastructure.repository.material_cost_type_repository import MaterialCostTypeRepository
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.orden_pagos.infrastructure.repository.program_repository import ProgramRepository
from apps.orden_pagos.models import PaymentOrder
from apps.pagos.application.use_cases.create_payment import CreatePaymentUseCase
from apps.pagos.application.use_cases.prepare_payment_allocations import PreparePaymentAllocationsUseCase
from apps.pagos.application.use_cases.prepare_payment_data import PreparePaymentDataUseCase
from apps.user.infrastructure.repository.users_repository import UsersRepository
from apps.orden_pagos.presentation.api.schemas import CreatePaymentOrderSchema, PaymentOrderSchema
from apps.orden_pagos.presentation.api.schemas.exonerated_payment_schemas import (
    ExoneratedPaymentOutput,
    ErrorResponse
)
from apps.pagos.application.commands import CreatePaymentCommand
from apps.pagos.application.services.payment_processing_service import PaymentProcessingService
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.presentation.api.schemas.output_schemas import PaymentSchema


domain_service = PaymentOrderDomainService()
repository_payment_order = PaymentOrderRepository()
repository_payment_concept = PaymentConceptRepository()
repository_administrative_cost = AdministrativeCostRepository()
invoice_service = InvoiceDomainService()
invoice_repository = InvoiceRepository()
user_repository = UsersRepository()
payment_concept_repository = PaymentConceptRepository()
payment_repository = PaymentRepository()
create_invoice_uc = CreateInvoiceUseCase(invoice_service, invoice_repository,repository_payment_order, user_repository, payment_concept_repository)
prepare_payment_data_uc = PreparePaymentDataUseCase(user_repository, invoice_repository)
prepare_payment_allocations_uc = PreparePaymentAllocationsUseCase(invoice_repository, payment_concept_repository)

create_payment_uc = CreatePaymentUseCase(
            payment_repository,
            payment_concept_repository,
            invoice_repository, PaymentProcessingService(),
            prepare_payment_data_uc
)
# Crear router para pagos exonerados
exonerated_router = Router(tags=["Exonerated Payments"], auth=AuthBearer())


@exonerated_router.post(
    "/",
    response={201: ExoneratedPaymentOutput, 400: ErrorResponse, 500: ErrorResponse},
    summary="Crear pago exonerado"
)
def create_exonerated_payment(request: HttpRequest, payload: CreatePaymentOrderSchema):
    creation_message = 'Orden de pago creada correctamente.'
    payload_dict = payload.dict(exclude={'send_payment_link'})

    try:
        with transaction.atomic():
            # Convertir payload a diccionario y agregar status
            payload_dict['status'] = 'EXONERATED'

            data = CreatePaymentOrderCommand(**payload_dict)

            # Crear casos de uso necesarios
            concept_by_id_uc = GetConceptByIdUseCase(repository_payment_concept)
            type_administrative_cost_uc = GetTypeAdministrativeCostUseCase(repository_administrative_cost)

            payment_order = CreatePaymentOrderUseCase(
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

            payment_order_schema = PaymentOrderSchema.from_orm(payment_order)

            if payment_order:
                # Convertir el schema a diccionario para prepare_invoice_data
                payment_order_dict = payment_order_schema.dict()

                payload_invoice = InvoiceMapper.prepare_invoice_data(
                    payment_order_dict
                )
                payload_invoice['status'] = 'E'
                data_invoice = CreateInvoiceCommand(**payload_invoice)
                invoice = create_invoice_uc.execute(data_invoice)

                if invoice:
                    creation_message = 'Orden de pago y factura creadas correctamente.'
                    invoice_schema = InvoiceSchema.from_orm(invoice)
                    invoice_schema = invoice_schema.dict()


                    # Preparar payment_allocation (pago exonerado = pago completo sin costo)
                    payment_allocation = prepare_payment_allocations_uc.execute(
                        invoice_schema.get('invoice_details'),
                        payment_amount=invoice_schema.get('total'),
                        is_full_payment=False,
                        status='EXONERATED'
                    )

                    payload_data = PaymentMapper.prepare_payment_data(
                        invoice_schema=invoice_schema,
                        payment_reference_number=f"Exonerated - {invoice.invoice_number}",
                        payment_method='EX',
                        status='E',
                        payment_allocation=payment_allocation
                    )

                    payment_data = CreatePaymentCommand(**payload_data)

                    payment = create_payment_uc.execute(payment_data)

                    payment_schema = PaymentSchema.from_orm(payment)
                    creation_message = 'Orden de pago, factura y pago EXONERADO creados correctamente.'

            return 201, {
                'success': True,
                'message': creation_message,
                'data': {
                    'payment_order': payment_order_schema,
                    'invoice': invoice_schema,
                    'payment': payment_schema,
                }
            }

    except ValueError as e:
        # Errores de validación
        return 400, {
            'success': False,
            'message': 'Error de validación',
            'detail': str(e)
        }
    except Exception as e:
        # Errores generales
        print(f"Error al crear orden de pago exonerado: {e}")
        return 500, {
            'success': False,
            'message': 'Error al crear la orden de pago exonerado',
            'detail': str(e)
        }

@exonerated_router.put(
    "/by-id/{order_id}/",
    response={200: ExoneratedPaymentOutput, 400: dict, 500: dict},
    summary="Actualizar pago exonerado"
)
def update_payment_order_exonerated(
      request: HttpRequest,
      order_id: int
):
    creation_message = 'Orden de pago actualizada correctamente.'
    invoice_schema = {}
    payment_schema = {}
    payment_order = GetPaymentOrderByIdUseCase(repository_payment_order).execute(order_id)
    try:
        with transaction.atomic():
            if payment_order:
                payment_order_schema = PaymentOrderSchema.from_orm(payment_order)
                payment_order_update_dict = payment_order_schema.dict()
                payload_invoice = InvoiceMapper.prepare_invoice_data(
                    payment_order_update_dict
                )
                payload_invoice['status'] = 'E'

                data_invoice = CreateInvoiceCommand(**payload_invoice)
                invoice = create_invoice_uc.execute(data_invoice)

                if invoice:
                    invoice_schema = InvoiceSchema.from_orm(invoice)
                    invoice_schema = invoice_schema.dict()

                    # Preparar payment_allocation (pago exonerado = pago completo sin costo)
                    payment_allocation = prepare_payment_allocations_uc.execute(
                        invoice_schema.get('invoice_details'),
                        payment_amount=None,
                        is_full_payment=True
                    )
                    payload_data = PaymentMapper.prepare_payment_data(
                        invoice_schema=invoice_schema,
                        payment_reference_number=f"Exonerated - {invoice.invoice_number}",
                        payment_method='EX',
                        status='E',
                        payment_allocation=payment_allocation
                    )

                    payment_data = CreatePaymentCommand(**payload_data)

                    payment = create_payment_uc.execute(payment_data)


                    payment_schema = PaymentSchema.from_orm(payment)

                    # Verificar que payment_order sea una instancia y actualizar su status
                    if isinstance(payment_order, PaymentOrder):
                        payment_order.update_status('EXONERATED')

                    creation_message = 'Orden de pago actualizada, factura y pago EXONERADO creados correctamente.'

                return 200, {
                    'success': True,
                    'message': creation_message,
                    'data': {
                        'payment_order': payment_order_schema,
                        'invoice': invoice_schema,
                        'payment': payment_schema,
                    }
                }

    except ValueError as e:
        # Errores de validación
        return 400, {
            'success': False,
            'message': 'Error de validación',
            'detail': str(e)
        }
    except Exception as e:
        # Errores generales
        print(f"Error al crear orden de pago exonerado: {e}")
        return 500, {
            'success': False,
            'message': 'Error al crear la orden de pago exonerado',
            'detail': str(e)
        }