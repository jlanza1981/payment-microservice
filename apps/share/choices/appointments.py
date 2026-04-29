from django.utils.translation import gettext_lazy as _

APPOINTMENT_STATUS_CHOICES = (
    ('', _('Seleccione')),
    ('S', _('Asignado')),
    ('R', _('Rechazado')),
    ('P', _('Pendiente')),
    ('C', _('Cerrado'))
)
CREDENTIAL_CHOICES = (
    (_(''), _('Seleccione')),
    (_('Diplomado de 2 años'), _('Diploma de 2 años')),
    (_('Diploma Avanzado 3 años'), _('Diploma Avanzado 3 años')),
    (_('Licenciaturas'), _(' Licenciaturas')),
    (_('Postgrados y/o Maestrías'), _('Postgrados y/o Maestrías'))
)

TRAVEL_PLAN_CHOICES = (
    ('', _('Seleccione')),
    ('Lo antes posible', _('Lo antes posible')),
    ('Antes de un año', _('Antes de un año')),
    ('Después de un año', _('Después de un año')),
    ('No tengo planes específicos de viaje', _('No tengo planes específicos de viaje'))
)
STATUS_APPOINTMENT_ACADEMIC_CHOICES = (
    ('P', _('Pendiente')),
    ('A', _('Aprobado')),
    ('R', _('Reprobado')),
    ('I', _('Inactivo'))
)

WORKING_CHOICES = (
    ('', _('Seleccione')),
    ('si', _('SI')),
    ('no', _('NO'))
)

