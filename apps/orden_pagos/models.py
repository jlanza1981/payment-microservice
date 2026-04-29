import secrets
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.utils.GenerateCorrelative import generate_correlative
from apps.core.models import Categorias, Paises, Ciudades, path_and_rename
from apps.instituciones.models import Institucion, Intensidad, Cursos
from apps.utils.dates import date_range_is
from apps.website.models import TipoCosto


def payment_order_upload_to(instance, filename):
    return path_and_rename("payment_order", filename)


# Create your models here.
class Modelo(models.Model):
    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('-created_at', '-updated_at')
        default_permissions = ('add', 'change', 'delete', 'view')


class PaymentCategory(Modelo):
    """
    Categoría para clasificar tipos de pago.
    Permite filtrar y organizar conceptos según su naturaleza.
    """
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Código'))
    name = models.CharField(max_length=100, verbose_name=_('Nombre de la Categoría'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'payment_category'
        verbose_name = _('Categoría de Pago')
        verbose_name_plural = _('Categorías de Pago')


class PaymentConcept(Modelo):
    """
    Concepto de pago atómico (unidad básica).
    Representa un solo concepto facturable como Inscripción, Matrícula, etc.
    """
    code = models.CharField(max_length=5, unique=True, verbose_name=_('Código del Concepto'))
    name = models.CharField(max_length=100, verbose_name=_('Nombre del Concepto'))
    category = models.ForeignKey(
        'PaymentCategory',
        on_delete=models.PROTECT,
        related_name='concepts',
        verbose_name=_('Categoría')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    split_order = models.BooleanField(default=False, verbose_name=_('Dividir orden?'), help_text=_(
        'Indica si este concepto debe ir en una orden separada cuando se combina con otros conceptos que requieren programa.'))
    requires_program = models.BooleanField(default=False, verbose_name=_('Requiere Programa'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    @classmethod
    def set_admin_fee_split_order(cls, id: int):
        value: Optional[bool] = cls.objects.filter(id=id).values_list('split_order', flat=True).first()
        return bool(value)

    class Meta:
        db_table = 'payment_concept'
        verbose_name = _('Concepto de Pago')
        verbose_name_plural = _('Conceptos de Pago')


### este modelo fue pensado para definir las estructura por tipo de pago
class PaymentStructure(Modelo):
    payment_type = models.ForeignKey(
        'PaymentConcept',
        on_delete=models.PROTECT,
        related_name='structure',
        verbose_name=_('Tipo de Pago')
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(_('Notas'), blank=True)
    has_discount = models.BooleanField(default=False)
    choices = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.payment_type.code} - {self.payment_type.name}'

    def to_json(self):
        """
        Retorna un JSON estructurado con:
        - Información básica de la estructura
        - Tipo de pago principal
        - Fields dinámicos asociados (PaymentStructureFields)
        """
        return {
            "id": self.id,
            "payment_concept": {
                "id": self.payment_type.id,
                "name": self.payment_type.name,
                "code": getattr(self.payment_type, "code", None),
            },
            "has_discount": self.has_discount,
            "notes": self.notes,
            "is_active": self.is_active,
            "fields": [
                {
                    "id": field.id,
                    "name": field.name,
                    "label": field.label,
                    "field_type": field.field_type,
                    "choice": field.choices,
                    "required": field.required,
                    "order": field.order,
                    "default_value": field.default_value,
                    "active": field.active,
                }
                for field in self.structure_section_payment_structure.all().order_by("order")
            ],
        }

    class Meta:
        db_table = 'payment_structure'
        verbose_name = _('Estructura de Pago')
        verbose_name_plural = _('Estructuras de Pago')


class PaymentStructureFields(Modelo):
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('hidden', 'Oculto'),
        ('div', 'Div'),
        ('number', 'Número'),
        ('select', 'Select'),
        ('readonly', 'Solo Lectura'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
    ]
    DISCOUNT_TYPES = [
        ('fixed', _('Fijo')),
        ('percentage', _('Porcentual')),
    ]
    payment_structure = models.ForeignKey('PaymentStructure', related_name='structure_section_payment_structure',
                                          on_delete=models.PROTECT, verbose_name=_('Estructura'))
    name = models.CharField(max_length=50)  # Ej: "precio", "descuento_pct"
    label = models.CharField(max_length=100)  # Ej: "Precio", "Descuento (%)"
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    choices = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=True)
    readonly = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    default_value = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.payment_structure.payment_type}::{self.name}'

    class Meta:
        db_table = 'payment_structure_section'
        verbose_name = _('Sección de Estructura de Pago')
        verbose_name_plural = _('Secciones de Estructura de Pago')
        ordering = ['order']


class PaymentOrder(Modelo):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de pago'),
        ('PAID', 'Pagado'),
        ('VERIFIED', 'Verificado por Tesorería'),
        ('CANCELLED', 'Cancelado'),
        ('EXONERATED', 'Exonerado'),
        ('ACTIVE', 'Activa - En proceso de pago'),  # Nueva: recibiendo pagos parciales
    ]
    order_number = models.CharField(max_length=15, unique=True)
    student = models.ForeignKey('administrador.Usuarios', on_delete=models.PROTECT, related_name='payment_orders')
    advisor = models.ForeignKey('administrador.Usuarios', on_delete=models.PROTECT, related_name='created_orders')
    opportunity = models.ForeignKey('crm.Oportunidades', on_delete=models.PROTECT, null=True, blank=True)
    quotation = models.ForeignKey('website.Cotizaciones', on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING', choices=STATUS_CHOICES)

    # Nuevos campos para soporte de pagos parciales
    allows_partial_payment = models.BooleanField(default=True, verbose_name=_('Permite pagos parciales'),
                                                 help_text=_('Si está activo, el estudiante puede pagar por abonos'))
    minimum_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                 default=Decimal('50.00'),
                                                 verbose_name=_('Monto mínimo de abono'),
                                                 help_text=_('Monto mínimo permitido para cada abono (opcional)'))
    suggested_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                   verbose_name=_('Monto sugerido para el pago'),
                                                   help_text=_('Monto sugerido para el pago actual. Se actualiza cada vez que el asesor envía un link de pago (1ra, 2da, 3ra, 4ta cuota, etc.)'))
    payment_link_date = models.DateField(auto_now_add=True, null=True, blank=True,
                                         verbose_name=_('Fecha de envío del link'))
    payment_types = models.ManyToManyField('PaymentConcept', through='PaymentOrderDetails',
                                           related_name='payment_types')
    total_order = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      verbose_name=_('Monto total de la orden'))
    payment_order_file = models.FileField(max_length=200, null=True, blank=True, upload_to=payment_order_upload_to,
                                          validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                                          verbose_name=_('Orden de pago generada'), help_text=_(
            'PDF de la orden de pago  generada por el sistema, que se enviará al estudiante'))
    link_expires_at = models.DateField(default='', null=True, blank=True)
    token = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    consumed = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, default='USD', verbose_name=_('Moneda'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate payment order number automatically if it doesn't exist
        if not self.order_number:
            self.order_number = generate_correlative('payment order', 'PO')
        if self.link_expires_at == '':
            self.link_expires_at = None
        super().save(*args, **kwargs)


    def calculate_total_order(self):
        self.total_order = self.calculated_total
        self.save(update_fields=['total_order', 'updated_at'])

    def cancel(self) -> bool:
        if self.status == 'PENDING':
            self.status = 'CANCELLED'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    @property
    def calculated_total(self):
        return self.payment_order_details.aggregate(sub_total=models.Sum('sub_total'))['sub_total'] or Decimal('0.00')

    def mark_as_paid(self) -> bool:
        if self.status in ['ACTIVE', 'PENDING'] and self.get_balance_due() <= 0:
            self.status = 'PAID'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    def mark_consumed(self):
        self.consumed = True
        self.save(update_fields=["consumed", "updated_at"])

    def update_consumed_false(self):
        self.consumed = False
        self.save(update_fields=["consumed", "updated_at"])

    def update_status(self, status):
        self.status = status
        self.save()

    def initialize_suggested_payment_amount(self):
        self.suggested_payment_amount = Decimal('0.00')
        self.save(update_fields=["suggested_payment_amount", "updated_at"])

    def is_expired(self) -> bool:
        return timezone.now() > self.link_expires_at

    def verify(self) -> bool:
        """
        Verifica la orden por tesorería.
        Solo se pueden verificar órdenes en estado PAID.
        """
        if self.status == 'PAID':
            self.status = 'VERIFIED'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    def can_be_updated(self) -> bool:
        return self.status == 'PENDING' or self.status == 'ACTIVE'

    def can_receive_payments(self) -> bool:
        """
        Verifica si la orden puede recibir pagos.
        Solo órdenes PENDING o ACTIVE pueden recibir pagos.
        """
        if self.status not in ['PENDING', 'ACTIVE']:
            return False
        if self.link_expires_at and timezone.now().date() > self.link_expires_at:
            return False
        return True

    def get_total_paid(self) -> Decimal:
        """
        Obtiene el total pagado a través de la factura asociada.
        """
        invoice = self.invoices_payment_order.first()
        if invoice:
            return invoice.get_total_paid()
        return Decimal('0.00')

    def get_balance_due(self) -> Decimal:
        """
        Obtiene el saldo pendiente de la orden.
        """
        return self.total_order - self.get_total_paid()

    def get_payment_count(self) -> int:
        """
        Obtiene el número de pagos realizados para esta orden.
        Útil para saber en qué cuota se encuentra (1ra, 2da, 3ra, 4ta, etc.)
        """
        invoice = self.invoices_payment_order.first()
        if invoice:
            return invoice.invoice_credit_detail_invoice.filter(credit_status='P').count()
        return 0

    def get_next_payment_number(self) -> int:
        """
        Obtiene el número del siguiente pago (para mostrar "Cuota 2", "Cuota 3", etc.)
        """
        return self.get_payment_count() + 1

    def is_partially_paid(self) -> bool:
        """
        Verifica si la orden tiene pagos parciales (al menos un pago pero no completada).
        """
        total_paid = self.get_total_paid()
        return 0 < total_paid < self.total_order

    def activate_for_payments(self) -> bool:
        """
        Activa la orden para comenzar a recibir pagos parciales.
        """
        if self.status == 'PENDING' and self.allows_partial_payment:
            self.status = 'ACTIVE'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    def should_split_orders(self) -> tuple[bool, list, list]:
        """
        Determina si la orden debe dividirse en dos órdenes separadas.

        """
        independent_details = []
        dependent_details = []

        for detail in self.payment_order_details.all():
            concept_id = getattr(detail.payment_concept, 'id', None)
            split: Optional[bool] = PaymentConcept.objects.filter(id=concept_id).values_list('split_order',
                                                                                             flat=True).first()
            if bool(split):
                independent_details.append(detail)
            else:
                dependent_details.append(detail)

        # Solo separar si hay ambos tipos
        should_split = len(independent_details) > 0 and len(dependent_details) > 0

        return should_split, independent_details, dependent_details

    def generate_expiration_date(self, days_valid: int = 7):
        self.link_expires_at = (timezone.now() + timedelta(days=days_valid)).date()
        self.save(update_fields=['link_expires_at', 'updated_at'])
        return self.link_expires_at

    def __str__(self):
        return f"Order {self.order_number} - {self.student}"

    @property
    def formatted_date_range(self):
        """
        Retorna el rango de fechas en formato:
        27 de octubre 2025 – 19 de diciembre 2025
        """
        program = getattr(self, 'payment_order_program', None)
        if not program or not program.start_date:
            return ''
        return date_range_is(program.start_date, program.end_date)

    def get_order_structure(self, another_program=None):
        """
        Retorna un dict con la estructura completa de la orden de pago:
        - Datos del estudiante
        - Datos del programa
        - Conceptos a facturar (tipos de pago con sus montos)
        """

        order_json = {
            "id": self.id,
            "order_number": self.order_number,
            "student": {
                "id": self.student.id,
                "identity_document": self.student.identity_document(),
                "name": str(self.student.get_full_name()),
                "email": getattr(self.student, 'email', None),
                "customer_code": getattr(self.student, 'cod_cliente_web', None),
            },
            "advisor": {
                "id": self.advisor.id,
                "name": str(self.advisor.get_full_name()),
                "email": getattr(self.advisor, 'email', None),
            },
            "status": self.status,
            "registration_date": self.payment_link_date.strftime('%d/%m/%Y') if self.payment_link_date else None,
            "link_expires_at": self.link_expires_at.strftime('%d/%m/%Y') if self.link_expires_at else None,
            "total_order": "{:,.2f}".format(Decimal(self.total_order).quantize(Decimal('0.01'))),
            "calculated_total": "{:,.2f}".format(Decimal(self.calculated_total).quantize(Decimal('0.01'))),
            # Campos de pagos parciales
            "allows_partial_payment": self.allows_partial_payment,
            "minimum_payment_amount": Decimal(self.minimum_payment_amount).quantize(Decimal('0.01')) if self.minimum_payment_amount else None,
            "suggested_payment_amount": float(Decimal(self.suggested_payment_amount).quantize(Decimal('0.01'))) if self.suggested_payment_amount else None,
            "suggested_payment_amount_texto": "{:,.2f}".format(Decimal(self.suggested_payment_amount).quantize(Decimal('0.01'))) if self.suggested_payment_amount else None,
            "balance_due": "{:,.2f}".format(Decimal(self.get_balance_due()).quantize(Decimal('0.01'))),
            "total_paid": "{:,.2f}".format(Decimal(self.get_total_paid()).quantize(Decimal('0.01'))),
            "payment_count": self.get_payment_count(),
            "next_payment_number": self.get_next_payment_number(),
            'document': 'payment_order',
            "program": {},
            "payment_concepts": [],
            "credits": []
        }

        # Programa
        program = getattr(self, 'payment_order_program', None)
        order_json['currency'] = program.country.currency_symbol if program and program.country else 'USD'
        if program:
            order_json["program"] = {
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
        elif another_program:
            order_json["program"] = another_program

        # Conceptos de pago (detalles)
        details = self.payment_order_details.select_related('payment_concept', 'type_administrative_cost')

        for detail in details:
            split_order = getattr(detail.payment_concept, 'split_order', None)
            payment_code = getattr(detail.payment_concept, 'code', None)
            cost_type = " / " + detail.type_administrative_cost.nombre if detail.type_administrative_cost else ''

            # Calcular el monto unitario según el tipo de concepto
            if payment_code == 'M' and program and program.price_week:
                # Para matrícula con price_week (idiomas), usar price_week
                amount = Decimal(program.price_week or 0)
            elif payment_code == 'P' and program and program.material_cost:
                # Para materiales, usar material_cost
                amount = Decimal(program.material_cost or 0)
            else:
                # Para otros conceptos o educación superior, usar el amount del detalle
                amount = Decimal(detail.amount or 0)

            if program and not bool(split_order):
                # Concepto con programa
                tuition_amount = Decimal(detail.sub_total).quantize(Decimal('0.01'))
                order_json["payment_concepts"].append({
                    "payment_type_code": payment_code,
                    "payment_type_name": f"{detail.payment_concept.description}",
                    "amount": "{:,.2f}".format(amount.quantize(Decimal('0.01'))),
                    "quantity": program.duration if payment_code in ['M', 'P', 'E'] else 1,
                    "unit": program.get_duration_type_display() if payment_code in ['M', 'P', 'E'] else "-",
                    "discount_type": detail.get_discount_type_display() if detail.discount_type else None,
                    "discount_amount": "{:,.2f}".format(Decimal(detail.discount_amount).quantize(Decimal('0.01'))),
                    "sub_total": "{:,.2f}".format(tuition_amount),
                    "currency": order_json['currency']

                })

            else:
                # Otros tipos de pago

                concept = {
                    "payment_type_code": payment_code,
                    "payment_type_name": detail.payment_concept.name + ' ' + cost_type,
                    "quantity": 1,
                    "unit": "-",
                    "amount": "{:,.2f}".format(Decimal(detail.amount).quantize(Decimal('0.01'))),
                    "discount_type": detail.get_discount_type_display() if detail.discount_type else None,
                    "discount_amount": "{:,.2f}".format(Decimal(detail.discount_amount).quantize(Decimal('0.01'))),
                    "sub_total": "{:,.2f}".format(Decimal(detail.sub_total).quantize(Decimal('0.01'))),
                    "currency": "USD"
                }

                # Agregar tipo de costo administrativo si existe
                if detail.type_administrative_cost:
                    concept["administrative_cost_type"] = detail.type_administrative_cost.nombre

                order_json["payment_concepts"].append(concept)
        
        # Abonos/Créditos aplicados (InvoiceCreditDetail)
        # Una orden tiene UNA sola factura asociada
        invoice = self.invoices_payment_order.first()
        if invoice:
            credits = invoice.invoice_credit_detail_invoice.select_related(
                'credit_balance',
                'payment_receipt'
            ).order_by('-created_at')
            
            if credits.exists():
                for credit in credits:
                    order_json["credits"].append({
                        "id": credit.id,
                        "amount": "{:,.2f}".format(Decimal(credit.amount).quantize(Decimal('0.01'))),
                        "credit_status": credit.get_credit_status_display(),
                        "created_at": credit.created_at.strftime('%d/%m/%Y %H:%M') if credit.created_at else None,
                        "credit_balance": {
                            "id": credit.credit_balance.id,
                            "total_amount": "{:,.2f}".format(
                                Decimal(credit.credit_balance.total_amount).quantize(Decimal('0.01'))),
                            "available_amount": "{:,.2f}".format(
                                Decimal(credit.credit_balance.available_amount).quantize(Decimal('0.01'))),
                            "reason": credit.credit_balance.reason,
                            "active": credit.credit_balance.active,
                        } if credit.credit_balance else None,
                        "payment_receipt": {
                            "id": credit.payment_receipt.id,
                            "receipt_number": credit.payment_receipt.receipt_number,
                        } if credit.payment_receipt else None,
                    })

        return order_json

    class Meta:
        db_table = 'payment_order'


class PaymentOrderDetails(Modelo):
    DISCOUNT_TYPE = (
        ('percentage', _('Porcentaje')),
        ('fixed', _('Monto Fijo')),
    )
    payment_order = models.ForeignKey('PaymentOrder', on_delete=models.PROTECT, related_name="payment_order_details")
    payment_concept = models.ForeignKey(
        'PaymentConcept',
        on_delete=models.PROTECT,
        related_name='order_details',
        null=True,
        blank=True,
        verbose_name=_('Concepto de pago'),
        help_text=_(
            'Concepto específico facturado. Si el tipo de pago es combinado, se crea un detalle por cada concepto.')
    )
    type_administrative_cost = models.ForeignKey(TipoCosto, on_delete=models.PROTECT, null=True, blank=True,
                                                 related_name='payment_order_administrative_cost_type')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, null=True, blank=True, default='',
                                     verbose_name=_('Tipo de descuento'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                          verbose_name=_('Monto del descuento'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Monto neto del pago'))
    quantity = models.IntegerField(default=1, verbose_name=_('Duracion'))
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                    verbose_name=_('Monto total a pagar'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_amount(self):
        code = getattr(self.payment_concept, 'code', None)
        # Intentamos calcular usando el programa
        program = getattr(self.payment_order, 'payment_order_program', None)

        if program and code in ('M', 'P'):
            if code == 'M' and getattr(program, 'total_enrollment', None) is not None:
                return Decimal(program.total_enrollment).quantize(Decimal('0.01'))
            elif code == 'P' and getattr(program, 'total_material', None) is not None:
                return Decimal(program.total_material).quantize(Decimal('0.01'))

        # Fallback seguro al payload o 0
        amount = getattr(self, 'amount', 0) or 0
        return Decimal(amount).quantize(Decimal('0.01'))

    def get_applied_discount(self):
        base = Decimal(self.amount)
        discount = Decimal(self.discount_amount or 0)
        if self.discount_type == 'percentage' and discount > 0:
            return (base * discount / Decimal('100')).quantize(Decimal('0.01'))
        elif self.discount_type == 'fixed' and discount > 0:
            return min(discount, base).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def calculate_subtotal(self):
        return Decimal(Decimal(self.amount) - self.get_applied_discount()).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def clean(self):
        """
        Valida los descuentos aplicados al detalle de pago.
        """
        # Validar descuento porcentual entre 0% y 30%
        if self.discount_type == 'percentage':
            if self.discount_amount is not None and (self.discount_amount < 0 or self.discount_amount > 30):
                raise ValidationError({
                    "discount_amount": _("El descuento porcentual debe estar entre 0% y 30%.")
                })

        # Si es monto fijo, no puede superar el amount
        if self.discount_type == 'fixed':
            if self.amount and self.discount_amount and self.discount_amount > self.amount:
                raise ValidationError({
                    "discount_amount": _("El descuento fijo no puede ser mayor que el monto base.")
                })

    class Meta:
        db_table = 'payment_order_details'


class PaymentOrderProgram(Modelo):
    DURATION_TYPE = (('A', _('Año(s)')), ('S', _('Semestres')), ('w', _('Semanas')))

    payment_order = models.OneToOneField(PaymentOrder, on_delete=models.PROTECT, related_name="payment_order_program")
    program_type = models.ForeignKey(Categorias, on_delete=models.PROTECT)
    institution = models.ForeignKey(Institucion, on_delete=models.PROTECT)
    country = models.ForeignKey(Paises, on_delete=models.PROTECT)
    city = models.ForeignKey(Ciudades, on_delete=models.PROTECT)
    program = models.ForeignKey(Cursos, null=True, blank=True, default=None, on_delete=models.PROTECT)
    intensity = models.ForeignKey(Intensidad, null=True, blank=True, default=None, on_delete=models.PROTECT)
    another_program = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Otro Programa'))
    start_date = models.DateField(verbose_name=_('Fecha de Inicio'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de Final'))
    duration = models.IntegerField(default=0, verbose_name=_('Duracion'))
    duration_type = models.CharField(max_length=1, choices=DURATION_TYPE, default='w',
                                     verbose_name=_('Tipo de Duración'))
    price_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     verbose_name=_('Precio por semana de la matricula (solo para idiomas)'))
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                        verbose_name=_('Costo de Material'))
    material_cost_type = models.ForeignKey('instituciones.TiposCostoMaterial',
                                           verbose_name=_('Tipo de Costo de Material'), null=True,
                                           blank=True, on_delete=models.PROTECT,
                                           related_name='payment_order_material_cost_type')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tuition_subtotal(self):
        duration = Decimal(self.duration or 0)
        price_week = Decimal(self.price_week or 0)
        return (price_week * duration).quantize(Decimal('0.01'))

    @property
    def total_material(self):
        return Decimal(self.material_cost * self.duration or 0).quantize(Decimal('0.01'))

    @property
    def total_enrollment(self):
        return self.tuition_subtotal.quantize(Decimal('0.01'))

    def clean(self):
        nombre = (self.program_type.nombre or '').lower()
        dt = self.duration_type  # 'A' = años, 'S' = semestres, 'w' = semanas

        if nombre == 'idiomas' and dt != 'w':
            raise ValidationError(_('Los programas de idiomas deben tener duración en semanas.'))
        if nombre in ('maestria', 'educacion superior') and dt not in ('S', 'A'):
            raise ValidationError(_('Las maestrías deben tener duración en semestres o años.'))

    class Meta:
        db_table = 'payment_order_program'
