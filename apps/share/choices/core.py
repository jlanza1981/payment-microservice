from django.utils.translation import gettext_lazy as _

VISA_CHOICES = (
    ('', _('Seleccione')),
    ('si', _('SI')),
    ('no', _('NO'))
)

MANAGERS = (
    ('', _('Ninguno')),
    ('O', _('Gerente de Oficina')),
    ('R', _('Gerente Regional')),
    ('G', _('Gerente General')),
    ('P', _('Presidente')),
    ('A', _('Administrador')),
)