from django.utils.translation import gettext_lazy as _

TYPES_PROMOCODE = (
    ('C', _('EduSuperiorCanada')),
    ('S', _('LCSheryl')),
    ('M', _('OnTracktoPR in Montreal')),
    ('V', _('VENTEACANADA')),
    ('F', _('InglésFrancésCanadá')),
    ('E', _('DestinosEstudiayTrabaja')),
    ('R', _('TuInglesDaRisa')),
    ('A', _('GISMA')),
    ('P', _('EmpaqueLC')),
    ('Y', _('YoSoyRafaLC')),
    ('N', _('NC TORONTO(NC2022)'))
)
EVENT_MODALITY = (
    ('Presencial', _('Presencial')),
    ('Webinar', _('Webinar')),
    ('On-Demand', _('On-Demand')),
)
EVENT_TYPE = (
    ('general', _('General')),
    ('blackfriday', _('Black Friday')),
    ('expo', _('Expo Mundo')),
)
PROMO_TYPES = (
    ('expositor', _('Expositor')),
    ('general', _('General')),
)