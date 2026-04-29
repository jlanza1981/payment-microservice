from django.utils.translation import gettext_lazy as _
#genero
GENDER_CHOICES = (
    ('', _('Seleccione')),
    ('m', _('Hombre')),
    ('f', _('Mujer')),
)
#estado civil
MARITAL_STATUS_CHOICES = (
    ('', _('Seleccione')),
    ('CASADO', _('CASADO')),
    ('CONCUBINATO', _('CONCUBINATO')),
    ('DIVORCIADO', _('DIVORCIADO')),
    ('SEPARADO', _('SEPARADO')),
    ('SOLTERO', _('SOLTERO')),
    ('VIUDO', _('VIUDO'))
)
SYSTEM_TYPES_CHOICES = (
    ('LC', _('CMS WEBSITE')),
    ('F', _('AFILIADOS')),
    ('CR', _('CRM')),
    ('WEB', _('WEBSITE')),
)

TYPE_CATEGORY_CHOICES = (
    ('', _('Seleccione')),
    ('A', _('Alojamientos')),
    ('C', _('Conferencias')),
    ('E', _('Educación')),
    ('D', _('Educación a Distancia')),
    ('O', _('Opinión')),
    ('R', _('Recreación')),
    ('S', _('Salud'))
)
MODALITY_TYPE_CHOICES = (
    ('I', _('Horas por Semana')),
    ('S', _('Por Semestre')),
    ('U', _('Año Escolar')),
    ('C', _('Campamento')),
    ('L', _('Clases en Línea')),
    ('O', _('Otros')),
)

ACCOMMODATION_STATUS_CHOICES = (
    ('P', _('Pendiente')),
    ('A', _('Aprobado')),
    ('R', _('Rechazado')),
    ('I', _('Inactivo')),
    ('C', _('Confirmado'))
)
ACADEMIC_LEVELS_CHOICES = (
    (_('SECUNDARIA'), _('Bachillerato / Preparatoria')),
    (_('UNIVERSITARIO'), _('Pregrado / Licenciatura')),
    (_('POSTGRADO'), _('Postgrado / Maestría'))
)
ENGLISH_LEVELS_CHOICES = (
    (_('C1-C2'), _('Avanzado')),
    (_('B1'), _('Intermedio')),
    (_('B2'), _('Intermedio / Avanzado')),
    (_('A1'), _('Principiante')),
    (_('A2'), _('Principiante / Intermedio')),
)
ACHIEVED_CHOICES = (
    ('', _('Seleccione')),
    ('Graduado', _('GRADUADO')),
    ('Estudiando', _('ESTUDIANDO')),
    ('Otro', _('OTRO'))
)
OCCUPATIONS = (
    ('', _('Seleccione')),
    ('1', _('Estudiante')),
    ('2', _('Profesional')),
    ('3', _('Otro'))
)

TYPES_PAGES_CHOICES = (
    ('W', _('Web Site')),
    ('E', _('Expomundo')),
    ('N', _('Noticia LC')),
)
PAY_STUDY_CHOICES = (
    ('', _('Seleccione')),
    ('Ahorros-Personales', _('Ahorros personales')),
    ('Apoyo familiar', _('Apoyo familiar')),
    ('Credito', _('Crédito de un banco'))
)
BUDGET_STUDIES_CHOICES = (
    ('', _('Select')),
    ('Hasta US $7,000.00', _('Up to US $7,000.00')),
    ('Desde US $7,000.00 a US $12,000.00', _('From US $7,000.00 to US $12,000.00')),
    ('Desde US $12,000.00 a US $20,000.00', _('From US $12,000.00 to US $20,000.00')),
    ('Desde US $20,000.00 US $25,000.00', _('From US $20,000.00 to US $25,000.00')),
    ('Desde US $25,000.00 o más', _('From US $25,000.00 or more'))
)
CONTACT_METHOD_CHOICES = (
    ('', _('Seleccione')),
    ('Email', _('Email')),
    ('Llamada Teléfonica', _('Llamada Teléfonica')),
    ('Whatsapp', _('Whatsapp'))
)
OPTIONS_CARD_CHOICES = (
    ('', _('Select')),
    ('A través de mi representante o familiar', _('Through my representative or family')),
    ('A través de una institución ﬁnanciera o prestamista', _('Through a financial institution or lender')),
    ('Ninguna', _('None')),
    ('Personal', _('Personal'))
)
ONLINE_FORM_CHOICES = (
    ('S', _('Asignada')),
    ('R', _('Rechazada')),
    ('P', _('Pendiente')),
    ('C', _('Cerrada')),
)
TYPE_BANNER = (
    ('P', _('Principal')),
    ('S', _('Promocional'))
)
TYPE_CATEGORY = (
    ('I', _('Idiomas')), ('S', _('College')),
    ('U', _('Bachillerato')),
     ('C', _('Campamentos'))
)
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