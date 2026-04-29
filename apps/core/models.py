import os
from datetime import date

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

def path_and_rename(path, filename):
    file_root, file_ext = os.path.splitext(filename)
    filename = '{}{}'.format(get_random_string(20).lower(), file_ext)

    return os.path.join(path, filename)
class Modelo(models.Model):
    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = (
            '-created_at',
            '-updated_at',
        )
        default_permissions = ('add', 'change', 'delete', 'view')

class Continente(Modelo):
    name = models.CharField(
        max_length=60, null=False, blank=False, verbose_name=_('Continente'))

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'continentes'
        verbose_name = _('Continente')
        verbose_name_plural = _('Continentes')
        get_latest_by = 'name'
        ordering = ('name',)

class Paises(Modelo):
    id = models.CharField(
        max_length=3, primary_key=True, verbose_name=_('Codigo país'))
    pais = models.CharField(
        max_length=60, null=False, blank=False, verbose_name=_('País'))
    country_code = models.CharField(
        max_length=2, null=False, blank=False, verbose_name=_('codigo ISO '))
    country_calling_code = models.CharField(
        max_length=6,
        default='',
        null=False,
        blank=False,
        verbose_name=_('codigo llamada país'))
    por_defecto = models.BooleanField(default=False)
    nombre_moneda = models.CharField(
        max_length=100,
        default='',
        null=False,
        blank=False,
        verbose_name=_('nombre de la moneda país'))
    currency_symbol = models.CharField(
        max_length=6,
        default='',
        null=False,
        blank=False,
        verbose_name=_('simbolo de la moneda país'))
    continente = models.ForeignKey(
        Continente,
        null=True,
        blank=True,
        related_name='paises_por_continente',
        on_delete=models.PROTECT)
    email_contacto = models.CharField(
        max_length=602, null=True, blank=True, verbose_name=_('Correo de Contacto '))

    def get_query_set(self):
        # TODO: este metodo no es necesario. probar
        return (super(Paises, self).get_query_set().order_by('país'))

    def __str__(self):
        return self.pais

    class Meta:
        db_table = 'paises'
        verbose_name = _('Pais')
        verbose_name_plural = _('Paises')
        get_latest_by = 'pais'
        ordering = ('pais',)


class Ciudades(Modelo):
    ciudad = models.CharField(
        max_length=60, null=False, blank=False, verbose_name=_('Ciudad'))
    # estado = models.ForeignKey(Estados, on_delete=models.CASCADE)
    pais = models.ForeignKey(Paises, related_name='pais_ciudades', on_delete=models.PROTECT)

    def get_query_set(self):
        # TODO: este metodo no es necesario. probar
        return (super(Ciudades, self).get_query_set().order_by('ciudad'))

    def __str__(self):
        return self.ciudad

    class Meta:
        db_table = 'ciudades'
        verbose_name = _('Ciudad')
        verbose_name_plural = _('Ciudades')
        get_latest_by = 'ciudad'
        ordering = ('ciudad',)


class TipoAsesores(Modelo):
    tipo = models.CharField(max_length=100)

    class Meta:
        db_table = 'tipo_asesores'


class TiposUsuarios(Modelo):
    id = models.CharField(max_length=3, primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'tipos_usuarios'


class Enterarse(Modelo):
    nombre = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('¿Como te enteraste de LC?'))
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_('Fecha de Creación'))
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Fecha de Actualización'))

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'enterarse'
        verbose_name = _('LC')
        verbose_name_plural = _('LC')

class Influencer(Modelo):
    id = models.CharField(max_length=3, primary_key=True, verbose_name=_('Codigo influencer'))
    nombre = models.CharField(max_length=100, null=False, blank=False, verbose_name=_('Nombre del influencer'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('Fecha de Actualización'))

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'influencer'
        verbose_name = _('influencer LC')
        verbose_name_plural = _('influencer LC')

class UsuariosManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given username must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class Usuarios(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['dni', 'genero', 'nacimiento', 'telefono']

    GENERO_CHOICES = (
        ('', _('Seleccione')),
        ('m', _('Hombre')),
        ('f', _('Mujer')),
    )
    TIPO_USUARIO = (
        ('LC', 'LC'),
        ('E', _('Estudiante')),
        ('I', _('Institucion educativa')),
        ('A', _('Arrendatarios')),
        ('S', _('Asesores')),
        ('F', _('Afiliados')),
        ('CR', 'CRM'),
    )

    GERENTES = (
        ('', _('Ninguno')),
        ('O', _('Gerente de Oficina')),
        ('R', _('Gerente Regional')),
        ('G', _('Gerente General')),
        ('P', _('Presidente')),
        ('A', _('Administrador')),
    )

    ESTADO_CIVIL_CHOICES = (
        ('', _('Seleccione')), ('CASADO', _('CASADO')), ('CONCUBINATO', _('CONCUBINATO')),
        ('DIVORCIADO', _('DIVORCIADO')),
        ('SEPARADO', _('SEPARADO')), ('SOLTERO', _('SOLTERO')), ('VIUDO', _('VIUDO')))
    VISA_CHOICES = (('', _('Seleccione')), ('si', _('SI')), ('no', _('NO')))
    INFLUENCER = (
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

    def rename_foto(self, filename):
        return path_and_rename("usuarios", filename)

    nombre = models.CharField(
        max_length=100, null=False, blank=False, verbose_name=_('Nombre'))
    apellido = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_('Apellido'))
    email = models.EmailField(
        max_length=80,
        null=False,
        blank=False,
        db_index=True,
        unique=True,
        verbose_name=_('Correo Electronico'))

    # documento nacional de identidad
    dni = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        db_index=True,
        unique=True,
        verbose_name=_('Documento de Identidad'))
    cod_cliente_web = models.CharField(
        max_length=12,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Codigo de Usuario Estudiante'))
    pasaporte = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        unique=True,
        verbose_name=_('Numero de Pasaporte'))
    genero = models.CharField(
        choices=GENERO_CHOICES,
        max_length=15,
        null=True,
        blank=True,
        verbose_name=_('Sexo'))
    nacimiento = models.DateField(
        null=True, blank=True, verbose_name=_('Fecha de Nacimiento'))
    direccion = models.TextField(
        max_length=250, null=True, blank=True, verbose_name=_('Dirección Actual'))
    telefono = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_('Teléfono'))
    telefono_movil = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_('Teléfono Movil'))
    foto = models.FileField(
        max_length=200,
        null=True,
        blank=True,
        upload_to=rename_foto,
        verbose_name=_('Imagen'))
    foto_google = models.TextField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name=_('Foto de Perfil de Google'))
    imagen_comprobante_idioma = models.FileField(
        max_length=200,
        null=True,
        blank=True,
        upload_to=rename_foto,
        verbose_name=_('Constancia de Idioma'))
    imagen_pasaporte = models.FileField(
        max_length=200,
        null=True,
        blank=True,
        upload_to=rename_foto,
        verbose_name=_('Pasaporte Digitalizado'))
    pais = models.ForeignKey(
        Paises,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='pais_residencia',
        verbose_name=_('País de Residencia'))
    pais_origen = models.ForeignKey(
        Paises,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='pais_origen',
        verbose_name=_('Nacionalidad'))
    ciudad = models.ForeignKey(
        Ciudades,
        null=True,
        blank=True,
        related_name='ciudad_usuarios',
        on_delete=models.PROTECT,
        verbose_name=_('Ciudad de Residencia'))
    ciudad_origen = models.ForeignKey(
        Ciudades,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ciudad_origen",
        verbose_name=_('Ciudad de Nacionalidad'))
    otra_nacionalidad = models.BooleanField(
        default=False, verbose_name=_('¿Tiene otra nacionalidad?'))
    cual_nacionalidad = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('¿Cual Nacionalidad?'))
    beca = models.BooleanField(default=False, verbose_name=_('¿Cuenta con una beca aprobada?'))
    proveerdor_beca = models.CharField(max_length=300, null=True, blank=True, default="",
                                       verbose_name=_('Nombre del Proveedor'))
    estado_civil = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        default="",
        choices=ESTADO_CIVIL_CHOICES,
        verbose_name=_('Estado Civil'))
    tipo_usuario = models.CharField(max_length=2, default='LC')
    tipos_usuario = models.ManyToManyField(TiposUsuarios, verbose_name=_('Tipos de Usuario'))
    activo = models.BooleanField(_('Activo'), default=False)
    token = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_('Token'))
    origen = models.CharField(max_length=50, default='Normal')
    seccion_pagina = models.CharField(max_length=50, default='')
    promocode = models.CharField(max_length=15, null=True, blank=True, default='', verbose_name=_('Codigo de Promo'))
    referido = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='asesor_referido',
        verbose_name=_('Asesor que lo atiende'))
    is_jefe_oficina = models.BooleanField(
        _('es jefe de oficina'),
        default=False,
        help_text=_('Se usa para saber si el usuario es jefe de la oficina a la que pertenece'),
    )
    gerente = models.CharField(choices=GERENTES, max_length=1, default='')
    oficina = models.ForeignKey('administrador.Oficinas', related_name='usuarios_oficina', null=True,
                                on_delete=models.SET_NULL)
    cargo = models.CharField(max_length=50, default='', null=True, blank=True, verbose_name=_('Cargo de Usuario CRM'))
    enterarse = models.ForeignKey(Enterarse, related_name='enterarse_usuarios', on_delete=models.PROTECT, null=True,
                                  verbose_name=_('¿Cómo te enteraste de LC'))
    pagar_matricula = models.BooleanField(
        verbose_name=_('Pagar Matricula'),
        default=False,
        help_text=_('Permite al usuario asesor pagar las matriculas de clientes por la web')
    )
    tipo_asesor = models.ManyToManyField(
        TipoAsesores,
        verbose_name=_('¿Tipo de Asesor?'))
    meta = models.PositiveIntegerField(
        null=True, blank=True, default=0, verbose_name=_('Meta del Asesor'))
    sesion_blackfriday = models.BooleanField(_('Blackfriday'), default=False)
    sesion_live_canada = models.BooleanField(_('Live Canada Virtual'), default=False)
    visa = models.CharField(max_length=2, null=True, blank=True, default="", choices=VISA_CHOICES,
                            verbose_name=_(' ¿Cuentas con visa vigente? '))
    pais_visa = models.CharField(max_length=100, null=True, blank=True, default="",
                                 verbose_name=_(' ¿De que país es su visa? '))
    influencer = models.ForeignKey(Influencer, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('Nombre del Influencer'))
    is_influencer = models.BooleanField(default=False, help_text='Influencer Marketing')

    # username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

    # username = models.CharField(
    #    _('username'),
    #    max_length=150,
    #    help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
    #    validators=[username_validator],
    # )

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_asistente = models.BooleanField(default=False, help_text='Asistente del Gerente de oficina')
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    recibe_noticias = models.BooleanField(
        default=False, verbose_name=_('Suscripción LC notícias'))
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_('Fecha de Creación'))
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Fecha de Actualización'))

    objects = UsuariosManager()

    def __str__(self):
        return str(self.nombre) + ' ' + str(self.apellido)

    def identity_document(self):
        return self.dni if self.dni else self.pasaporte

    def get_full_name(self):
        '''
		Returns the first_name plus the last_name, with a space in between.
		'''
        full_name = '%s %s' % (self.nombre, self.apellido)
        return full_name.strip()

    def get_short_name(self):
        '''
		Returns the short name for the user.
		'''
        return self.nombre

    def get_email_user(self):
        """
		Retorna el correo para que sea usado posteriormente
		"""
        return self.email.lower()

    def edad(self):
        if not self.nacimiento:
            return 0
        hoy = date.today()
        return hoy.year - self.nacimiento.year - ((hoy.month, hoy.day) < (self.nacimiento.month, self.nacimiento.day))

    def generar_cod_cliente_web(self):
        cod = str(self.id)
        self.cod_cliente_web = "LC-{}".format('00000000'[len(cod):] + cod)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)  # Guarda para que self.id exista
        if not self.cod_cliente_web:
            self.generar_cod_cliente_web()
            super().save(update_fields=['cod_cliente_web'])

    class Meta:
        db_table = 'usuarios'
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')

class LetrasCorrelativos(models.Model):
    letra = models.CharField(max_length=3, default='', verbose_name=_('Letra del Correlativo'))
    tabla = models.CharField(max_length=30, null=True, blank=True, verbose_name=_('Tabla del Correlativo'))
    document_type = models.CharField(max_length=50)
    last_number = models.PositiveIntegerField(default=0)
    year = models.PositiveIntegerField(default=timezone.now().year)

    class Meta:
        db_table = 'letras_correlativos'