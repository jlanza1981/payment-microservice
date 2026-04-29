"""
Configuración de Ejemplo para Probar con Correos Reales

Copia estas configuraciones en tu settings.py o en un archivo settings_test.py
"""

# =============================================================================
# OPCIÓN 1: VER CORREOS EN CONSOLA (Recomendado para desarrollo)
# =============================================================================
# Los correos se imprimen en la consola en lugar de enviarse
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# =============================================================================
# OPCIÓN 2: ENVIAR CORREOS REALES VÍA GMAIL
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_correo@gmail.com'  # ← Cambia aquí
EMAIL_HOST_PASSWORD = 'tu_app_password'  # ← Usa una App Password de Gmail
DEFAULT_FROM_EMAIL = 'tu_correo@gmail.com'

# Para obtener una App Password de Gmail:
# 1. Ve a https://myaccount.google.com/security
# 2. Habilita la verificación en 2 pasos
# 3. Ve a "Contraseñas de aplicaciones"
# 4. Genera una nueva contraseña para "Correo"
# 5. Usa esa contraseña aquí


# =============================================================================
# OPCIÓN 3: ENVIAR CORREOS REALES VÍA SMTP GENÉRICO
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.tu-proveedor.com'
EMAIL_PORT = 587  # o 465 para SSL
EMAIL_USE_TLS = True  # o False si usas SSL
EMAIL_USE_SSL = False  # o True si tu proveedor requiere SSL
EMAIL_HOST_USER = 'tu_usuario@dominio.com'
EMAIL_HOST_PASSWORD = 'tu_contraseña'
DEFAULT_FROM_EMAIL = 'noreply@lcmundo.com'


# =============================================================================
# OPCIÓN 4: GUARDAR CORREOS EN ARCHIVOS (Para debugging)
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-emails'  # Los correos se guardan aquí como archivos


# =============================================================================
# CONFIGURACIÓN ADICIONAL PARA TESTS
# =============================================================================

# Si quieres usar una configuración diferente solo para tests:
# Crea un archivo settings_test.py y úsalo así:
#   python manage.py test --settings=api.settings_test

# O define la variable de entorno:
#   export DJANGO_SETTINGS_MODULE=api.settings_test
#   python manage.py test apps.core.tests.test_webhook_event_processor


# =============================================================================
# DATOS DE PRUEBA - EDITA ESTOS EN test_webhook_event_processor.py
# =============================================================================

ESTUDIANTE_TEST = {
    'nombre': 'Carlos',
    'apellido': 'Rodríguez',
    'email': 'carlos.rodriguez@test.com',  # ← Cambia por tu email real
    'tipo_usuario': 'student'
}

ASESOR_TEST = {
    'nombre': 'Ana',
    'apellido': 'Martínez',
    'email': 'ana.martinez@test.com',  # ← Cambia por otro email real
    'tipo_usuario': 'advisor'
}

# En test_webhook_event_processor.py, busca el método setUp() y edita:
# self.student = Usuarios.objects.create(
#     nombre='Carlos',
#     apellido='Rodríguez',
#     email='TU_EMAIL_REAL@gmail.com',  # ← Aquí
#     ...
# )

