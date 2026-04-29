from django.utils.translation import gettext_lazy as _

STATUS_OPPORTUNITY_CHOICE = (
    ('P', _('Oportunidad')),
    ('O', _('Prospecto')),
    ('T', _('Tramite')),
    ('C', _('Concretado')),
    ('R', _('Cerrada')),
)
PAYMENT_STATUS_RECORDS_CHOICE = (
    ('P', 'PENDIENTE'),
    ('L', 'VENTA COMPLETADA'),
    ('C', 'VENTA CANCELADA'),
)
PROGRAM_TYPE_CHOICE = (
    ('', 'Seleccione'),
    ('Bachelor Degree (4y)', 'Bachelor Degree (4y)'),
    ('Degree (3y)', 'Degree (3y)'),
    ('Diploma (2y)', 'Diploma (2y)'),
    ('High School', 'High School'),
    ('Language Program', 'Language Program'),
    ('Maestría', 'Maestría'),
    ('Post Graduate Certificate (1y)', 'Post Graduate Certificate (1y)'),
    ('Postgraduate Certificate (2Y)', 'Postgraduate Certificate (2Y)'),
    ('Summer Camp', 'Summer Camp'),
    ('No Asignado', 'No Asignado'),
)
PAYMENT_METHOD_CHOICE = (
    ('', 'Seleccione'),
    ('Directo', 'Directo'),
    ('Applyboard', 'Applyboard'),
    ('Canadian Edge', 'Canadian Edge'),
)
TRAVEL_DOCUMENT_STATUS_CHOICE = (
    ('A', 'Aprobado'),
    ('P', 'Pendiente'),
    ('E', 'Eliminado')
)
TYPE_TRAVEL_DOCUMENT_CHOICE = (
    ('E', 'Enviado'),
    ('R', 'Recibido'),
)


FOLLOW_TYPE_CHOICES = (
    ('E', 'Estatus'),
    ('S', 'Seguimiento'),
)