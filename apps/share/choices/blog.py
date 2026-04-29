from django.utils.translation import gettext_lazy as _

POST_STATUS_CHOICES = (
    ('', _('Seleccione')),
    (1, _('Borrador')),
    (2, _('Publicado')),
    (3, _('Lista para Edición')),
)

OWNER_CHOICES = (
    ('', _('Seleccione')),
    (1, _('LC')),
    (2, _('EXPO-MUNDO')),
)