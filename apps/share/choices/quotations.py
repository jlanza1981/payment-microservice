from django.utils.translation import gettext_lazy as _

QUOTE_STATUS_CHOICES = (
    ('A', _('Venta Total')),
    ('R', _('Rechazada')),
    ('P', _('Venta Pendiente')),
    ('E', _('Venta Reservada')),
    ('B', _('Inscripción Pagada')),
    ('I', _('Reserva Pendiente')),
    ('C', _('Venta Concretada')),
    ('S', _('Venta Asignada al Asesor')),
    ('M', _('Pago de Matricula')),
    ('F', _('Pago de Booking Fee')),
    ('J', _('Inscripción y Booking Fee')),
    ('L', _('Costo, Inscripción, Matricula y Booking Fee')),
    ('H', _('Inscripción, Matricula y Booking Fee')),
    ('T', _('Matricula y Booking Fee')),
    ('Q', _('Costo Administrativo, Inscripción y Matricula')),
    ('U', _('Abono de Matricula y adicionales')),
    ('V', _('Vencida')),
)
OPPORTUNITY_STATE_CHOICES = (
    ('S', _('Asignado')),
    ('P', _('Pendiente')),
    ('C', _('Cerrado')),
)

STATUS_EXTERNAL_QUOTATION_CHOICES = (
    ('S', _('Asociada')),
    ('R', _('Rechazada')),
    ('P', _('Pendiente')),
    ('C', _('Cerrada'))
)
QUOTE_CREDIT_TYPES = (
    ('M', _('Matricula')),
    ('H', _('Home Stay')),
)
ACCOMMODATION_TYPE_CHOICES = (
    ('', _('Ninguno')),
    ('T', _('TOTAL')),
    ('N', _('NOCHES EXTRA')),
    ('D', _('DIAS ESPECIFICOS')),
)