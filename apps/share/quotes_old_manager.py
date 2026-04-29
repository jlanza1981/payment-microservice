from django.db import models
import datetime
from django.utils import timezone

class CotizacionesAntiguasManager(models.Manager):
	"""Manager que filtra cotizaciones mayores a 7 dias desde la fecha actual """

	def get_queryset(self):
		fecha_siete_dias = timezone.now() - datetime.timedelta(days=7)
		return super().get_queryset().filter(fecha_creacion__lt=fecha_siete_dias)
