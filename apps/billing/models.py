from decimal import Decimal

from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models, transaction
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.utils.GenerateCorrelative import generate_correlative
from apps.core.models import path_and_rename, Usuarios


def administrative_document_upload_to(instance, filename):
    path_and_rename("administrative_document", filename)


def invoice_file_upload_to(instance, filename):
    path_and_rename("invoice_file", filename)


class Modelo(models.Model):
    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('-created_at', '-updated_at')
        default_permissions = ('add', 'change', 'delete', 'view')


class Invoice(Modelo):
    """
    Main invoicing model.
    Allows invoicing with or without a prior quotation.
    """
    SALE_TYPES = (
        ('D', _('Venta directa sin cotización')),
    )

    INVOICE_STATUS = (
        ('B', _('BORRADOR')),
        ('I', _('EMITIDA')),
        ('PP', _('PARCIALMENTE PAGADA')),
        ('P', _('PAGADA')),
        ('A', _('ANULADA')),
        ('PV', _('PENDIENTE POR VERIFICAR POR TESORERIA')),
        ('V', _('VERIFICADA POR TESORERIA')),
        ('R', _('REEMBOLSADA')),
        ('E', _('EXONERATED')),
    )

    # Automatic invoice numbering
    invoice_number = models.CharField(max_length=50, unique=True, editable=False, verbose_name=_('Invoice Number'),
                                      db_index=True)

    # Main relationships
    user = models.ForeignKey('core.Usuarios', on_delete=models.PROTECT, related_name='invoice',
                             verbose_name=_('Student'))
    advisor = models.ForeignKey('core.Usuarios', on_delete=models.PROTECT, null=True, blank=True,
                                related_name='invoice_advisor', verbose_name=_('Advisor'))
    # MODIFICADO: Una factura corresponde a UNA orden de pago
    payment_order = models.ForeignKey('orden_pagos.PaymentOrder', on_delete=models.PROTECT,
                                      related_name='invoices_payment_order', verbose_name=_('Orden de Pago'),
                                      help_text=_('Una factura corresponde a UNA orden de pago'))
    credits = models.ManyToManyField('StudentCreditBalance', blank=True, through='InvoiceCreditDetail',
                                     related_name='invoice_credits',
                                     verbose_name=_('Abonos aplicados'))
    # Sale type
    sale_type = models.CharField(max_length=1, choices=SALE_TYPES, default='D', verbose_name=_('Tipo de venta'))
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), verbose_name=_('Subtotal'),
                                   validators=[MinValueValidator(0)])
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), verbose_name=_('Impuestos'),
                                validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), verbose_name=_('Total'),
                                validators=[MinValueValidator(0)])
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00),
                                      verbose_name=_('Saldo deudor'),
                                      validators=[MinValueValidator(0)], help_text=_('Monto pendiente por pagar'))
    # Currency
    currency = models.CharField(max_length=10, default='USD', verbose_name=_('Currency'))
    # Status
    status = models.CharField(max_length=2, choices=INVOICE_STATUS, default='B', verbose_name=_('Status'),
                              db_index=True)

    # Notes
    notes = models.TextField(null=True, blank=True, verbose_name=_('Notes'))
    administrative_document = models.FileField(max_length=200, null=True, blank=True,
                                               upload_to=administrative_document_upload_to, validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])],
                                               verbose_name=_('Documento de Referencia'),
                                               help_text=_(
                                                   'Documentos administrativos relacionados (orden de compra, autorización, etc.)'))
    invoice_file = models.FileField(max_length=200, null=True, blank=True,
                                    upload_to=invoice_file_upload_to,
                                    validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                                    verbose_name=_('Factura generada'), help_text=_(
            'PDF de la factura generada por el sistema, que se enviará al estudiante'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('fecha de Emisión'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('fecha de Emisión'))

    def save(self, *args, **kwargs):
        # Generate invoice number automatically if it doesn't exist
        if not self.invoice_number:
            self.invoice_number = generate_correlative('invoice', 'FAC')

        # Calculate total
        self.total = self.calculate_total()

        # If it's a new invoice, balance due equals total
        if not self.pk:
            self.balance_due = self.total

        super().save(*args, **kwargs)

    def calculate_total(self):
        return self.subtotal + self.taxes

    def update_status_balance_due(self):
        if self.balance_due <= 0:
            self.status = 'P'  # Pagada
        elif self.balance_due < self.total:
            self.status = 'PP'  # Parcialmente Pagada

    def update_balance(self):
        """
        Actualiza el saldo y el estado de la factura basado en los pagos recibidos.
        Genera la factura final PDF cuando se completa el pago.
        """
        # Facturas Anuladas o Exoneradas siempre tienen balance 0
        if self.status in ('A', 'E'):  # Anulada o Exonerada
            self.balance_due = Decimal('0.00')
            self.notes = f"Pago Exonerado el : {self.updated_at.strftime('%d/%m/%Y')}"
            self.save(update_fields=['balance_due', 'notes', 'updated_at'])
            return

        # Importar aquí para evitar import circular
        from apps.pagos.models import PaymentAllocation

        # Calcular total pagado basándose SOLO en PaymentAllocation.amount_applied
        # Esto es correcto porque PaymentAllocation ya distribuye el monto del pago
        # entre los conceptos de la factura
        total_paid = PaymentAllocation.objects.filter(
            invoice_detail__invoice=self,
            payment__status__in=['D', 'V']  # Pagos disponibles y verificados
        ).aggregate(total=models.Sum('amount_applied'))['total'] or Decimal('0.00')


        # Actualizar saldo pendiente
        self.balance_due = self.total - total_paid

        # Actualizar estado basado en el saldo
        if self.balance_due <= 0:
            self.status = 'P'  # Pagada
            
            # Actualizar orden de pago asociada
            if self.payment_order:
                self.payment_order.mark_as_paid()

        elif self.balance_due < self.total:
            self.status = 'PP'  # Parcialmente Pagada

            # Activar orden para pagos parciales si no está activa
            if self.payment_order and self.payment_order.allows_partial_payment:
                self.payment_order.activate_for_payments()


        # Descripción de pagos y saldo
        payment_description = f"Pagado: {total_paid:.2f}, Pendiente: {self.balance_due:.2f}"
        self.notes = payment_description
        self.save()

    def update_status(self, status):
        self.status = status
        self.save()

    def update_credit_balance(self, credit_balance, amount):
        """
        Actualiza el StudentCreditBalance al aplicar un crédito.
        
        Args:
            credit_balance: Instancia de StudentCreditBalance a actualizar
            amount: Monto del crédito aplicado
        """
        # Validar que el monto no excede el disponible
        if amount > credit_balance.available_amount:
            raise ValueError(
                f"El monto {amount} excede el saldo disponible "
                f"({credit_balance.available_amount}) del StudentCreditBalance {credit_balance.id}."
            )
        
        # Validar que hay saldo disponible
        if credit_balance.available_amount <= 0:
            raise ValueError(
                f"El StudentCreditBalance {credit_balance.id} no tiene saldo disponible."
            )
        
        with transaction.atomic():
            # Actualizar el saldo disponible
            credit_balance.available_amount -= amount
            
            # Desactivar si se agotó
            if credit_balance.available_amount <= 0:
                credit_balance.active = False
            
            credit_balance.save(update_fields=['available_amount', 'active'])
            
            # Actualizar el balance de la factura
            self.update_balance()

    def __str__(self):
        return f'{self.invoice_number} - {self.user.get_full_name()}'

    def get_total_paid(self) -> Decimal:
        return self.total - self.balance_due

    def get_payment_counter(self):
        return self.invoice_credit_detail_invoice.filter(credit_status='P').count()

    def get_invoice_structure(self):
        invoice_json = {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "student": {
                "id": self.user.id,
                "identity_document": self.user.identity_document(),
                "name": str(self.user.get_full_name()),
                "email": getattr(self.user, 'email', None),
                "customer_code": getattr(self.user, 'cod_cliente_web', None),
            },
            "advisor": {
                "id": self.advisor.id,
                "name": str(self.advisor.get_full_name()),
                "email": getattr(self.advisor, 'email', None),
            },
            "status": self.status,
            "registration_date": self.created_at.strftime('%d/%m/%Y') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%d/%m/%Y') if self.updated_at else None,
            "total_invoice": "{:,.2f}".format(Decimal(self.total).quantize(Decimal('0.01'))),
            "total_paid": "{:,.2f}".format(Decimal(self.get_total_paid()).quantize(Decimal('0.01'))),
            "balance_due": "{:,.2f}".format(Decimal(self.balance_due).quantize(Decimal('0.01'))),
            "payment_count": self.get_payment_counter(),
            "next_payment_number": self.payment_order.get_next_payment_number(),
            "allows_partial_payment": self.payment_order.allows_partial_payment if self.payment_order else False,
            'currency':self.currency,
            'note': self.notes,
            'document': 'invoice',
            "program": {},
            "credits": [],
            "payment_concepts": [],
            "payment": []
        }

        # Programa
        program = getattr(self.payment_order, 'payment_order_program', None)
        if program:
            invoice_json["program"] = {
                "program_type": program.program_type.nombre if program.program_type else None,
                "program_name": program.program.nombre if program.program else program.another_program,
                "institution": program.institution.nombre if program.institution else None,
                "currency": program.country.country_code if program.country else None,
                "country": program.country.pais if program.country else None,
                "city": program.city.ciudad if program.city else None,
                "intensity": program.intensity.nombre if program.intensity else None,
                "start_date": program.start_date.strftime("%d/%m/%Y") if program.start_date else None,
                "end_date": program.end_date.strftime("%d/%m/%Y") if program.end_date else None,
                "duration": program.duration,
                "duration_type": program.get_duration_type_display(),
                "price_week": Decimal(program.price_week).quantize(Decimal('0.01')) if program.price_week else None,
                "tuition_subtotal": Decimal(program.tuition_subtotal).quantize(Decimal('0.01')),
                "material_cost": Decimal(program.material_cost).quantize(Decimal('0.01')),
                "material_cost_type": program.material_cost_type.nombre if program.material_cost_type else None,
                "total_material": Decimal(program.total_material).quantize(Decimal('0.01')),
                "total_enrollment": Decimal(program.total_enrollment).quantize(Decimal('0.01'))
            }


        # Conceptos de pago (detalles)
        details_invoice = self.details.select_related('payment_concept')

        for detail in details_invoice:
            invoice_json["payment_concepts"].append({
                "payment_type_code": detail.payment_concept.code,
                "payment_type_name": f"{detail.payment_concept.description}",
                "amount": "{:,.2f}".format(detail.unit_price.quantize(Decimal('0.01'))),
                "quantity":detail.quantity,
                "unit": program.get_duration_type_display() if detail.payment_concept.code in ['M', 'P', 'E'] else "-",
                "discount_type": detail.get_discount_type_display() if detail.discount_type else None,
                "discount_amount": "{:,.2f}".format(Decimal(detail.discount).quantize(Decimal('0.01'))),
                "sub_total": "{:,.2f}".format(detail.subtotal.quantize(Decimal('0.01'))),
                "currency": self.currency

            })

        # Pagos directos asociados a la factura (Payment)
        payments = self.payments_invoice.select_related('user', 'advisor').order_by('-payment_date')
        if payments.exists():
            for payment in payments:
                invoice_json["payment"].append({
                    "id": payment.id,
                    "payment_number": payment.payment_number,
                    "payment_reference_number": payment.payment_reference_number,
                    "payment_date": payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else None,
                    "verification_date": payment.verification_date.strftime('%d/%m/%Y') if payment.verification_date else None,
                    "payment_method": payment.get_payment_method_display(),
                    "amount": "{:,.2f}".format(Decimal(payment.amount).quantize(Decimal('0.01'))),
                    "currency": payment.currency,
                    "status": payment.get_status_display(),
                    "payer_name": payment.payer_name,
                    "payment_proof": payment.payment_proof.url if payment.payment_proof else None,
                    # Asignaciones de este pago (PaymentAllocation)
                    "allocations": []
                })
    
            # Asignaciones de pagos (PaymentAllocation) agrupadas por pago
            from apps.pagos.models import PaymentAllocation
            allocations = PaymentAllocation.objects.filter(
                invoice_detail__invoice=self
            ).select_related('payment', 'invoice_detail', 'payment_concept').order_by('payment__payment_date')
    
            # Agrupar allocations por payment_number
            for allocation in allocations:
                # Buscar el pago correspondiente en el array de pagos
                payment_found = None
                for payment_item in invoice_json["payment"]:
                    if payment_item["payment_number"] == allocation.payment.payment_number:
                        payment_found = payment_item
                        break
    
                if payment_found:
                    payment_found["allocations"].append({
                        "id": allocation.id,
                        "amount_applied": "{:,.2f}".format(Decimal(allocation.amount_applied).quantize(Decimal('0.01'))),
                        "status": allocation.get_status_display(),
                        "payment_concept": {
                            "code": allocation.payment_concept.code,
                            "name": allocation.payment_concept.name,
                        } if allocation.payment_concept else None,
                        "invoice_detail": {
                            "description": allocation.invoice_detail.description,
                            "subtotal": "{:,.2f}".format(Decimal(allocation.invoice_detail.subtotal).quantize(Decimal('0.01'))),
                        } if allocation.invoice_detail else None,
                    })

        # Abonos/Créditos aplicados (InvoiceCreditDetail)
        credits = self.invoice_credit_detail_invoice.select_related('credit_balance', 'payment_receipt').order_by('-created_at')
        if credits.exists():
            for credit in credits:
                invoice_json["credits"].append({
                    "id": credit.id,
                    "amount": "{:,.2f}".format(Decimal(credit.amount).quantize(Decimal('0.01'))),
                    "credit_status": credit.get_credit_status_display(),
                    "created_at": credit.created_at.strftime('%d/%m/%Y %H:%M') if credit.created_at else None,
                    "credit_balance": {
                        "id": credit.credit_balance.id,
                        "total_amount": "{:,.2f}".format(Decimal(credit.credit_balance.total_amount).quantize(Decimal('0.01'))),
                        "available_amount": "{:,.2f}".format(Decimal(credit.credit_balance.available_amount).quantize(Decimal('0.01'))),
                        "reason": credit.credit_balance.reason,
                        "active": credit.credit_balance.active,
                    } if credit.credit_balance else None,
                    "payment_receipt": {
                        "id": credit.payment_receipt.id,
                        "receipt_number": credit.payment_receipt.receipt_number,
                    } if credit.payment_receipt else None,
                })

        return invoice_json

    class Meta:
        db_table = 'invoices'
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-updated_at']


class InvoiceDetail(Modelo):
    """
    Invoice line items (billed concepts)
    """
    DISCOUNT_TYPE = (
        ('percentage', _('Porcentaje')),
        ('fixed', _('Monto Fijo')),
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='details', verbose_name=_('Invoice'))
    payment_concept = models.ForeignKey(
        'orden_pagos.PaymentConcept',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='invoice_details',
        verbose_name=_('Concepto de Pago')
    )
    description = models.CharField(max_length=100, verbose_name=_('Nombre del concepto de pago'),
                                   help_text=_('Descripción detallada del pago'))
    quantity = models.IntegerField(default=1, verbose_name=_('Cantidad'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio Unitario'),
                                     validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Descuento'),
                                   validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, null=True, blank=True, default='',
                                     verbose_name=_('Tipo de descuento'))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Subtotal'),
                                   validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('fecha de Emisión'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('fecha de Emisión'))

    def calculate_subtotal(self):
        return (self.quantity * self.unit_price) - self.discount

    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.clean()
        with transaction.atomic():
            self.subtotal = self.calculate_subtotal()
            super().save(*args, **kwargs)

            # Recalculate invoice totals (subtotal, total, balance)
            invoice = self.invoice
            # Recalcular subtotal agregando todos los detalles
            invoice_subtotal = invoice.details.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
            invoice.subtotal = invoice_subtotal
            # Recalcular total usando la lógica del modelo
            invoice.total = invoice.calculate_total()
            # Si es nueva factura o si el balance_due no se ha ajustado, mantener coherencia
            if not invoice.pk:
                invoice.balance_due = invoice.total
            else:
                # Importar aquí para evitar import circular
                from apps.pagos.models import PaymentAllocation

                # Recalcular balance_due en base a pagos existentes (si los hay)
                # total_paid usando solo PaymentAllocation.amount_applied
                total_paid = PaymentAllocation.objects.filter(
                    invoice_detail__invoice=invoice,
                    payment__status__in=['D', 'V']  # Pagos disponibles y verificados
                ).aggregate(total=models.Sum('amount_applied'))['total'] or Decimal('0.00')

                invoice.balance_due = (invoice.total - total_paid)
                # Actualizar estado según balance
                invoice.update_status_balance_due()
            # Persistir cambios de la factura
            invoice.save(update_fields=['subtotal', 'total', 'balance_due', 'status', 'updated_at'])

    def clean(self):
        super().clean()

        # Validación: concepto requiere programa
        if self.payment_concept and self.payment_concept.requires_program:
            payment_order = getattr(self.invoice, 'payment_order', None)
            if not payment_order or not getattr(payment_order, 'payment_order_program', None):
                raise ValidationError({
                    'payment_concept': _(
                        'El concepto "{}" requiere que la orden de pago tenga un programa asociado.'.format(
                            self.payment_concept.name))
                })

    class Meta:
        db_table = 'invoice_details'
        verbose_name = _('Invoice Detail')
        verbose_name_plural = _('Invoice Details')
        unique_together = [['invoice', 'payment_concept']]


class PaymentReceipt(Modelo):
    """
    Recibo de pago / Constancia de abono
    Se genera automáticamente cuando se registra un pago (parcial o total)
    """
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

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name=_('Número de Recibo'),
        db_index=True,
        help_text=_('Formato: REC-2025-000001')
    )

    payment = models.OneToOneField(
        'pagos.Payment',
        on_delete=models.PROTECT,
        related_name='receipt',
        verbose_name=_('Pago asociado')
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='receipts',
        verbose_name=_('Factura'),
        db_index=True
    )

    student = models.ForeignKey(
        Usuarios,
        on_delete=models.PROTECT,
        related_name='payment_receipts',
        verbose_name=_('Estudiante'),
        db_index=True
    )

    # Información del pago en el momento del recibo
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Monto pagado'),
        validators=[MinValueValidator(0)]
    )

    previous_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Saldo anterior'),
        validators=[MinValueValidator(0)]
    )

    new_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Nuevo saldo'),
        validators=[MinValueValidator(0)]
    )

    payment_method = models.CharField(
        max_length=2,
        verbose_name=_('Método de pago'),
        choices=PAYMENT_METHODS
    )

    payment_date = models.DateTimeField(
        verbose_name=_('Fecha del pago')
    )

    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name=_('Moneda')
    )

    # PDF generado
    receipt_file = models.FileField(
        max_length=200,
        null=True,
        blank=True,
        upload_to='receipts/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name=_('Recibo PDF'),
        help_text=_('PDF del recibo generado automáticamente')
    )

    # Control de envío por email
    sent_to_student = models.BooleanField(
        default=False,
        verbose_name=_('Enviado al estudiante')
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de envío por email')
    )

    # Notas adicionales
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Notas')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Última actualización'))

    def save(self, *args, **kwargs):
        # Generar número de recibo automáticamente
        if not self.receipt_number:
            self.receipt_number = generate_correlative('receipt', 'REC')
        super().save(*args, **kwargs)

    def send_to_student_email(self):
        """
        Envía el recibo por email al estudiante de forma asíncrona
        """
        from apps.billing.tasks import send_receipt_email_task
        send_receipt_email_task.delay(self.id)

    def get_receipt_structure(self):
        """
        Retorna un dict con la estructura completa del recibo:
        - Datos del estudiante
        - Datos de la factura
        - Datos del pago
        - Información del recibo
        """
        from decimal import Decimal

        receipt_json = {
            "id": self.id,
            "receipt_number": self.receipt_number,
            "amount_paid": self.amount_paid,
            "new_balance": self.new_balance,
            "previous_balance": self.previous_balance,
            "currency": self.currency,
            'document': 'receip',
            "student": {
                "id": self.student.id,
                "identity_document": self.student.identity_document(),
                "name": str(self.student.get_full_name()),
                "email": getattr(self.student, 'email', None),
                "customer_code": getattr(self.student, 'cod_cliente_web', None),
            },
            "advisor": {
                "id": self.invoice.advisor.id,
                "name": str(self.invoice.advisor.get_full_name()),
                "email": self.invoice.advisor.email,
            },
            "invoice": {
                "id": self.invoice.id,
                "invoice_number": self.invoice.invoice_number,
                "total": "{:,.2f}".format(Decimal(self.invoice.total).quantize(Decimal('0.01'))),
                "balance_due": "{:,.2f}".format(Decimal(self.invoice.balance_due).quantize(Decimal('0.01'))),
                "status": self.invoice.get_status_display(),
                "currency": self.invoice.currency,
            },
            "payment": {
                "payment_number": self.payment.payment_number if hasattr(self.payment, 'payment_number') else 'N/A',
                "amount": "{:,.2f}".format(Decimal(self.payment.amount).quantize(Decimal('0.01'))),
                "payment_method": self.payment.get_payment_method_display(),
                "payment_reference": self.payment.payment_reference_number,
                "payment_date": self.payment.payment_date.strftime('%d/%m/%Y %H:%M'),
                "currency": self.payment.currency,
                "payer_name": self.payment.payer_name,
            },

            "notes": self.notes or "",
            "registration_date": self.created_at.strftime('%d/%m/%Y %H:%M'),
        }

        # Agregar programa si existe
        program = getattr(self.invoice.payment_order, 'payment_order_program', None)
        if program:
            receipt_json["program"] = {
                "program_type": program.program_type.nombre if program.program_type else None,
                "program_name": program.program.nombre if program.program else program.another_program,
                "institution": program.institution.nombre if program.institution else None,
                "country": program.country.pais if program.country else None,
                "city": program.city.ciudad if program.city else None,
                "start_date": program.start_date.strftime("%d/%m/%Y") if program.start_date else None,
            }
        else:
            receipt_json["program"] = {}

        return receipt_json

    def __str__(self):
        return f'{self.receipt_number} - {self.student.get_full_name()} - ${self.amount_paid}'

    class Meta:
        db_table = 'payment_receipts'
        verbose_name = _('Recibo de Pago')
        verbose_name_plural = _('Recibos de Pago')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['invoice', '-created_at']),
        ]


class InvoiceCreditDetail(Modelo):
    CREDIT_STATUS = (
        ('E', _('Emitido')),
        ('P', _('Pago')),
    )
    invoice = models.ForeignKey('Invoice', on_delete=models.PROTECT,
                                related_name='invoice_credit_detail_invoice')
    payment_receipt = models.ForeignKey(PaymentReceipt, null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='credit_details_receipt')
    credit_balance = models.ForeignKey('StudentCreditBalance', null=True, blank=True,
                                       on_delete=models.PROTECT, related_name='credit_details',
                                       verbose_name=_('Saldo a Favor'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.0,
                                 verbose_name=_('Monto del abono'), validators=[MinValueValidator(0)])
    credit_status = models.CharField(max_length=1, choices=CREDIT_STATUS, default='E', null=True,
                                     verbose_name=_('Estatus del Abono'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('fecha de actualziacion'))

    def __str__(self):
        return f"Crédito {self.amount} aplicado a {self.invoice.invoice_number}"

    def update_credit_status(self, status):
        self.status = status
        self.save()

    class Meta:
        db_table = 'invoice_credit_detail'
        verbose_name = _('Detalle de Abono en la Factura')
        verbose_name_plural = _('Detalles de Abono en la Factura')


class StudentCreditBalance(Modelo):
    """
    Model to track student credit balances for future payments"""

    student = models.ForeignKey("core.Usuarios", on_delete=models.PROTECT,
                                related_name='credit_balances_student')
    origin_invoice = models.ForeignKey("Invoice", on_delete=models.PROTECT,
                                       related_name='credit_balances_origin_invoice')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    available_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def apply_to_invoice(self, destination_invoice, amount):
        """
        Aplica parte del saldo a una nueva factura.
        """
        if amount > self.available_amount:
            raise ValueError("El monto a aplicar excede el saldo disponible.")

        # Registrar aplicación
        with transaction.atomic():
            ApplicationBalance.objects.create(balance=self, destination_invoice=destination_invoice,
                                              amount_applied=amount)
            # Actualizar saldo disponible
            self.available_amount -= amount
            if self.available_amount <= 0:
                self.active = False
            self.save()

    class Meta:
        db_table = 'student_credit_balance'
        verbose_name = _('saldo a favor del estudiante')
        verbose_name_plural = _('saldo a favor de los estudiantes')


class ApplicationBalance(Modelo):
    """
    Registro de aplicaciones de saldo de crédito a facturas.
    """
    balance = models.ForeignKey('StudentCreditBalance', on_delete=models.PROTECT, related_name='application_balance')
    destination_invoice = models.ForeignKey("Invoice", on_delete=models.PROTECT,
                                            related_name='application_balance_destination_invoice')
    amount_applied = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    application_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Aplicación de {self.amount_applied} a {self.destination_invoice.invoice_number}"

    class Meta:
        db_table = 'application_balance'
        verbose_name = _('Aplicacion del saldo a favor')
        verbose_name_plural = _('Aplicaciones del saldo a favor')
