from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.models import PaymentConcept
from apps.share.generate_correlative import generate_correlative
from apps.share.path_and_rename import path_and_rename


# Create your models here.
# ==========================================
# INVOICING MODELS
# ==========================================

def payment_proofs_upload_to(instance, filename):
    path_and_rename("payment_proofs", filename)


class Modelo(models.Model):
    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('-created_at', '-updated_at')
        default_permissions = ('add', 'change', 'delete', 'view')


class Payment(Modelo):
    """
    Payment model associated with invoices.
    Maintains compatibility with existing payment types from PagosEnLinea.
    """

    # Status from PagosEnLinea
    PAYMENT_STATUS = (
        ('P', _('Pendiente por verificar')),
        ('F', _('Pendiente por confirmacion')),
        ('D', _('Disponible')),
        ('V', _('Verificado')),
        ('R', _('Rechazado')),
        ('X', _('Anulado')),
        ('E', _('Exonerado')),
    )

    PAYMENT_METHODS = (
        ('PP', _('PayPal')),
        ('ST', _('Stripe')),
        ('TC', _('Credit Card')),
        ('TD', _('Debit Card')),
        ('BT', _('Bank Transfer')),
        ('EF', _('Cash')),
        ('CH', _('Check')),
        ('EX', _('Exonerated')),
        ('OT', _('Other')),
    )
    payment_number = models.CharField(max_length=50, unique=True, editable=False, verbose_name=_('Payment Number'),
                                      db_index=True)
    # Relationship with invoice
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.PROTECT, null=True, blank=True,
                                related_name='payments_invoice',
                                verbose_name=_('Factura'), db_index=True)
    # User who made the payment
    user = models.ForeignKey('administrador.Usuarios', on_delete=models.PROTECT, verbose_name=_('User'),
                             related_name='payments_user')
    # Advisor reference
    advisor = models.ForeignKey('administrador.Usuarios', null=True, blank=True, on_delete=models.PROTECT,
                                related_name='payments_advisor', verbose_name=_('Advisor'))
    payment_reference_number = models.CharField(max_length=50, null=True, blank=True,
                                                verbose_name=_('Número de Referencia del Pago PayPal, Stripe u otro'))

    # Dates
    payment_date = models.DateTimeField(auto_now_add=True, editable=False, blank=True, null=True,
                                        verbose_name=_('Fecha de Pago'))
    verification_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de Verificación por Tesorería'))
    # Payment method
    payment_method = models.CharField(max_length=2, choices=PAYMENT_METHODS, default='PP',
                                      verbose_name=_('Método de Pago'))
    payment_proof = models.FileField(max_length=200, null=True, blank=True,
                                     upload_to=payment_proofs_upload_to,
                                     validators=[
                                         FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
                                     verbose_name=_('Comprobante de Pago'),
                                     help_text=_('Adjuntar comprobante de transferencia, depósito, etc.'))
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                 verbose_name=_('Monto de la orden de pago'),
                                 validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                      verbose_name=_('Monto Pagado efectivamente'),
                                      validators=[MinValueValidator(0)])

    currency = models.CharField(max_length=10, default='USD', verbose_name=_('Moneda'))
    # Status
    status = models.CharField(max_length=1, choices=PAYMENT_STATUS, default='D', verbose_name=_('Estatus del Pago'),
                              db_index=True)
    # Payer name
    payer_name = models.CharField(max_length=50, default='', verbose_name=_('Payer Name'))
    payment_terms_conditions = models.BooleanField(default=True, verbose_name=_('Aceptó Términos y Condiciones'))

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('Updated At'))

    def save(self, *args, **kwargs):
        # Generate payment number automatically
        if not self.payment_number:
            self.payment_number = generate_correlative('payment', 'PAY')

        super().save(*args, **kwargs)

        # NOTA: NO actualizar balance aquí porque los PaymentAllocation
        # se crean DESPUÉS del save del Payment en el repositorio.
        # El update_balance() debe llamarse explícitamente después de
        # crear el Payment y sus PaymentAllocation en el use case.

    def verify(self):
        # Validar que el pago esté pendiente
        if self.status not in ['V']:
            raise ValueError(
                f"El pago {self.payment_number} ya se verifico"
                f"(estado actual: {self.get_status_display()})"
            )

        # Establecer fecha de verificación
        verification_date = timezone.now().date()

        self.status = 'V'
        self.verification_date = verification_date
        self.save(update_fields=['status', 'verification_date', 'updated_at'])

    def get_payment_structure(self):
        payment_data = {
            "id": self.id,
            "payment_number": self.payment_number,
            "payment_reference_number": self.payment_reference_number,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None,
            "payment_method": self.payment_method,
            "payment_method_display": self.get_payment_method_display(),
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "status_display": self.get_status_display(),
            "payer_name": self.payer_name,
            "payment_terms_conditions": self.payment_terms_conditions,
            "payment_proof": self.payment_proof.url if self.payment_proof else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Información del usuario
        if self.user:
            payment_data["user"] = {
                "id": self.user.id,
                "nombre": self.user.nombre,
                "apellido": self.user.apellido,
                "full_name": f"{self.user.nombre} {self.user.apellido}",
                "email": self.user.email,
                "pasaporte": getattr(self.user, 'pasaporte', None),
            }
        else:
            payment_data["user"] = None

        # Información del asesor
        if self.advisor:
            payment_data["advisor"] = {
                "id": self.advisor.id,
                "nombre": self.advisor.nombre,
                "apellido": self.advisor.apellido,
                "full_name": f"{self.advisor.nombre} {self.advisor.apellido}",
                "email": self.advisor.email,
            }
        else:
            payment_data["advisor"] = None

        # Información de la factura
        if self.invoice:
            payment_data["invoice"] = {
                "id": self.invoice.id,
                "invoice_number": self.invoice.invoice_number,
                "total": float(self.invoice.total),
                "balance_due": float(self.invoice.balance_due),
                "status": self.invoice.status,
                "status_display": self.invoice.get_status_display(),
                "created_at": self.invoice.created_at.isoformat() if self.invoice.created_at else None,
            }
        else:
            payment_data["invoice"] = None

        # Asignaciones del pago (PaymentAllocation)
        allocations = []
        for allocation in self.allocations.select_related(
            'invoice_detail',
            'invoice_detail__payment_concept',
            'payment_concept'
        ).all():
            allocations.append({
                "id": allocation.id,
                "amount_applied": float(allocation.amount_applied),
                "status": allocation.status,
                "status_display": allocation.get_status_display(),
                "payment_concept": {
                    "id": allocation.payment_concept.id,
                    "code": allocation.payment_concept.code,
                    "name": allocation.payment_concept.name,
                    "category": allocation.payment_concept.category,
                } if allocation.payment_concept else None,
                "invoice_detail": {
                    "id": allocation.invoice_detail.id,
                    "description": allocation.invoice_detail.description,
                    "quantity": float(allocation.invoice_detail.quantity),
                    "unit_price": float(allocation.invoice_detail.unit_price),
                    "subtotal": float(allocation.invoice_detail.subtotal),
                } if allocation.invoice_detail else None,
                "created_at": allocation.created_at.isoformat() if allocation.created_at else None,
            })

        payment_data["allocations"] = allocations
        payment_data["total_allocations"] = len(allocations)

        return payment_data

    def __str__(self):
        return f'{self.payment_number} - {self.invoice.invoice_number} - ${self.amount}'

    def clean(self):
        super().clean()

        # Validar que pagos externos requieren comprobante
        if self.payment_method in ['TF', 'EF', 'CH'] and not self.payment_proof:
            if self.status in ['D', 'V']:  # Disponible o Verificado
                raise ValidationError({
                    'payment_proof': _('Los pagos externos requieren comprobante adjunto de referencia')
                })

    class Meta:
        db_table = 'payments'
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']


class PaymentAllocation(Modelo):
    PAYMENT_ALLOCATION_STATUS = (
        ('PAID', _('PAGADO')),
        ('PENDING', _('PENDIENTE')),
        ('EXONERATED', _('EXONERADO')),
    )

    payment = models.ForeignKey(
        Payment,
        related_name='allocations',
        on_delete=models.PROTECT
    )

    invoice_detail = models.ForeignKey(
        'billing.InvoiceDetail',
        on_delete=models.PROTECT
    )

    payment_concept = models.ForeignKey(
        PaymentConcept,
        on_delete=models.PROTECT
    )

    amount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=15,
        choices=PAYMENT_ALLOCATION_STATUS,
        default='D',
        verbose_name=_('Estatus del Pago'),
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('Updated At'))

    class Meta:
        db_table = 'payment_allocations'
        verbose_name = _('asignaciones de pago')
        verbose_name_plural = _('asignaciones de pago')

class PaymentTransaction(Modelo):

    STATUS_TRANSACTION = (
        ("CREATED", "Created"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    )

    payment_order = models.ForeignKey('orden_pagos.PaymentOrder', on_delete=models.PROTECT, related_name='payment_transaction_payment_order', verbose_name=_('Orden de Pago'))
    payment = models.ForeignKey('pagos.Payment', on_delete=models.PROTECT, null=True, blank=True, related_name='payment_transaction_payment', verbose_name=_('Pago'))
    paypal_order_id = models.CharField(max_length=100, unique=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_TRANSACTION,  default="CREATED")

    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    paypal_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Datos opcionales de auditoría
    payee_email = models.EmailField(null=True, blank=True)
    payee_merchant_id = models.CharField(max_length=100, null=True, blank=True)
    resource_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_payment(self, payment: Payment) -> bool:
        self.payment = payment
        self.save(update_fields=['payment', 'updated_at'])
        return True

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = _('transacción de pago')
        verbose_name_plural = _('transacciones de pago')

class FeeConfig(Modelo):
    currency = models.CharField(max_length=3, unique=True)  # CAD, USD, EUR...
    currency_name = models.CharField(max_length=100)  # Dólares Canadienses, etc.
    base_percentage = models.DecimalField(max_digits=5, decimal_places=4)  # ej: 0.0349
    international_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    fixed_fee = models.DecimalField(max_digits=6, decimal_places=2)  # 0.49 CAD, etc.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.currency} - Base: {self.base_percentage}, Intl: {self.international_percentage}, Fixed: {self.fixed_fee}"

    class Meta:
        db_table = 'fee_config'
        verbose_name = _('Configuracion de fee por país')
        verbose_name_plural = _('Configuraciones de fees por paises')

class InboxEvent(Modelo):
    event_id = models.CharField(max_length=200, unique=True)
    event_type = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    payer_name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Nombre del Pagador'))
    payment_order_id = models.IntegerField(default=0, verbose_name=_('ID de la orden de pago'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event_type

    class Meta:
        db_table = 'inbox_event'
        verbose_name = _('Entrada de evento de pago')
        verbose_name_plural = _('Entradas de eventos de pago')