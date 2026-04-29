from django.utils.translation import gettext_lazy as _

PAYMENT_TYPES = (
    ('C', _('Costo Administrativo')),
    ('I', _('Inscripción')),
    ('A', _('Costo Administrativo e Inscripción')),
    ('E', _('Extension de Matricula')),
    ('M', _('Matricula')),
    ('B', _('Inscripción y Matricula')),
    ('T', _('Costo Administrativo, Inscripción y Matricula')),
    ('P', _('Abono de Matricula')),
    ('F', _('Inscripción con Abono de Matricula')),
    ('G', _('Costo e Inscripción con Abono de Matricula')),
    ('N', _('Abono de Adicionales')),
    ('O', _('Todo Excepto Costo')),
    ('K', _('Registro de HomeStay')),
    ('J', _('Inscripción y Registro de HomeStay')),
    ('L', _('Costo, Inscripción, Matricula y Registro de HomeStay')),
    ('R', _('Inscripción, Matricula y Registro de HomeStay ')),
    ('S', _('Matricula y Registro de HomeStay ')),
    ('U', _(' Adicionales completos')),
    ('D', _('Pago Total')),
    ('W', _('Inscripción, Matricula, Booking Fee y adicionales')),
    ('V', _('Abono de Matricula y adicionales')),
    ('Z', _('Costo con Abono de Matricula')),
)
STATUS_PAYMENT = (
    ('P', _('Pendiente')),
    ('D', _('Disponible')),
    ('A', _('Asignado a Cotizacion')),
)
EVENT_TYPES = (
    ('expomundo', _('Expomundo')),
)
STATUS_PAY_CHOICES = [
    ('PENDING', 'Pendiente de pago'),
    ('PAID', 'Pagado'),
    ('VERIFIED', 'Verificado por Tesorería'),
    ('CANCELLED', 'Cancelado'),
    ('ACTIVE', 'Activa - En proceso de pago'),  # Nueva: recibiendo pagos parciales
]
DISCOUNT_TYPE = (
    ('percentage', _('Porcentaje')),
    ('fixed', _('Monto Fijo')),
)
SALE_TYPES = (
    ('Q', _('Venta con cotización')),
    ('D', _('Venta directa sin cotización')),
)

INVOICE_STATUS = (
    ('B', _('Borrador')),
    ('I', _('Emitida')),
    ('PP', _('Parcialmente pagada')),
    ('P', _('Pagada')),
    ('A', _('Anulada')),
    ('PV', _('Pendiente por Verificar por Tesorería')),
    ('V', _('Verificada por Tesorería')),
    ('R', _('Reembolsada')),
)
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
PAYMENT_ALLOCATION_STATUS = (
    ('PAID', _('PAGADO')),
    ('PENDDING', _('PENDIENTE')),
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
CREDIT_STATUS = (
    ('E', _('Emitido')),
    ('P', _('Pago')),
)
STATUS_TRANSACTION = (
    ("CREATED", "Created"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
    ("REFUNDED", "Refunded"),
)
