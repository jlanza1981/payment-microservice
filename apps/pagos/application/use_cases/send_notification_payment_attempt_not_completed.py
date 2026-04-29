from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.domain.entities.email_data import EmailData
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class SendNotificationPaymentAttemptNotCompleted:
    def __init__(self,  payment_order_repository: PaymentOrderRepositoryInterface):
        self.payment_order_repository = payment_order_repository

    def execute(self, order_id: int):
        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(
            order_id=order_id
        )
        recipients = [payment_order.student.email, payment_order.advisor.email]

        template_context = {
            'data': {
                'student_name': payment_order.student.nombre + ' ' + payment_order.student.apellido,
            }
        }

        subject = str(f'Intento de pago no completado')
        # Crear objeto EmailData
        email_data = EmailData(
            subject=subject,
            recipients=recipients,
            template_name='receipts/payment_receipt_email.html',
            template_context=template_context
        )

        # Enviar correo usando el caso de uso
        result = SendEmailUseCase(DjangoEmailSender()).execute(email_data)

        # Agregar la lista de emails al resultado para mantener compatibilidad
        if result['success']:
            result['emails'] = recipients

        return result