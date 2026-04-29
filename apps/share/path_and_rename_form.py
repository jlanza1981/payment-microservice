import os

from django.conf import settings


def planilla_path():
    return os.path.join(settings.TEMPLATES[0].get('DIRS')[0], 'planillas')
