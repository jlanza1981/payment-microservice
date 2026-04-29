from django.utils.translation import gettext_lazy as _
TYPES_DURATION_CHOICES = (
    ('A', _('Años')),
    ('S', _('Semestres')),
    ('w', _('Semanas'))
)
PRICE_TYPES_CHOICES = (
    ('S', _('Semanal')),
    ('Q', _('Quincenal')),
    ('M', _('Mensual'))
)
COURSE_STATUS_CHOICES = (
    ('A', _('Activo')),
    ('I', _('Inactivo'))
)