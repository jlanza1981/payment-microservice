from django.utils.translation import gettext_lazy as _

DATA_LOAD_CHOICES = (
    ('G', _('Datos Generales')),
    ('S', _('Cargó sedes')),
    ('A', _('Asoció cursos a las sedes')),
    ('F', _('Fin'))
)

STATUS_INSTITUTION_CHOICES = (
    ('A', _('Activo')),
    ('P', _('Pendiente')),
    ('I', _('Inactivo')),
    ('C', _('Comfirmado'))
)
STATUS_CAMPUS_CHOICES = (
    ('A', _('Activo')),
    ('I', _('Inactivo'))
)
DATA_LOAD_CAMPUS_CHOICES = (
    ('C', _('Completo')),
    ('I', _('Incompleto'))
)