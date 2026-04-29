# Contexto de Refactorización - SendPaymentLinkUseCase

**Fecha:** 2025-11-30
**Archivo:** `apps/orden_pagos/application/use_cases/send_payment_link.py`

## Resumen del Trabajo Realizado

Se está refactorizando el caso de uso `SendPaymentLinkUseCase` para mejorar la separación de responsabilidades y la
legibilidad del código.

## Estado Actual

### Archivo Principal

- **Ruta:** `c:\proyectos_django\api\apps\orden_pagos\application\use_cases\send_payment_link.py`
- **Clase:** `SendPaymentLinkUseCase`

### Métodos Existentes

1. **`execute(order_id, base_url)`** - Método principal
    - Valida la orden
    - Prepara y envía correos
    - Actualiza la fecha de envío

2. **`_prepare_and_send_emails(payment_order, base_url)`** - Preparación de correos
    - Genera el PDF usando `pdf_generator`
    - **⚠️ PENDIENTE:** Guarda el PDF en `payment_order.payment_order_file`
    - Llama a `_send_email()`

3. **`_generate_payment_link(payment_order)`** - Genera el enlace de pago
    - Crea el token
    - Construye la URL con el token

4. **`_prepare_email_data(payment_order)`** - Prepara datos para la plantilla
    - Obtiene la estructura de la orden
    - Incluye el enlace de pago

5. **`_get_payment_types_description(payment_order)`** - Obtiene tipos de pago
    - Recorre los detalles de la orden
    - Construye descripción concatenada

6. **`_send_email(payment_order, pdf_content)`** - Envía el correo
    - Prepara destinatarios (estudiante y asesor)
    - Genera el cuerpo del correo
    - Adjunta el PDF
    - Envía el correo

7. **`_build_response(email_result, payment_order)`** - Construye respuesta
    - Formatea el resultado del envío

## Tareas Pendientes

### 1. Extraer código a método privado

**Código a extraer (líneas 90-112):**

```python
student_email = payment_order.student.email
student_advisor = payment_order.opportunity.asesor.email
emails = [student_email, student_advisor]
pdf_filename = f"orden_pago_{payment_order.order_number}_{payment_order.student.nombre}_{payment_order.student.apellido}.pdf"
payment_types_desc = self._get_payment_types_description(payment_order)
email_data = self._prepare_email_data(payment_order)
body = render_to_string('email_payment_link_order.html', {'data': email_data})
try:
    subject = _(
        f'Realiza tu pago de {payment_types_desc} - Orden N° {payment_order.order_number} a través de nuestro sistema- LC Mundo'
    )
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        emails
    )
    email.attach_alternative(body, "text/html")
    email.attach(pdf_filename, pdf_content, 'application/pdf')
    email.send()
    logger.info(f"Enlace enviado al estudiante {student_email} - Orden {payment_order.order_number}")
    return {'success': True, 'emails': emails}

except Exception as e:
    logger.error(f"Error al enviar correo al estudiante {student_email}: {str(e)}")
    return {'success': False, 'error': str(e)}
```

**Acción requerida:**

- Crear un método privado nuevo (sugerencia: `_prepare_and_send_email_message()`)
- Este método debe encapsular toda la lógica de preparación y envío del correo
- Actualizar `_send_email()` para que llame a este nuevo método

### 2. Actualizar `payment_order_file` en la orden de pago

**Ubicación:** Método `_prepare_and_send_emails()`, líneas 66-69

**Código actual:**

```python
pdf_content = self.pdf_generator.execute(payment_order, base_url, 'pdf_order_payment.html',
                                         'pdf_order_payment.css')
payment_order.payment_order_file = pdf_content
payment_order.save()
```

**Problema:** Se está guardando la orden completa con `save()`, pero debería usar el repositorio y actualizar solo el
campo necesario.

**Acción requerida:**

- Cambiar `payment_order.save()` por `self.repository.save_order(payment_order, update_fields=['payment_order_file'])`

### 3. Verificar método `update` en la vista

**Nota del usuario:** "también el método update de la vista" no fue cambiado

**Acción requerida:**

- Localizar la vista relacionada con órdenes de pago
- Verificar el método `update`
- Aplicar los cambios necesarios para mantener consistencia con el caso de uso

## Estructura del Proyecto

```
apps/
  orden_pagos/
    application/
      use_cases/
        send_payment_link.py  ← Archivo actual
    domain/
      interface/
        repository/
          repository_interface.py
    views/
      [buscar vista con método update]
```

## Notas Importantes

- El proyecto usa arquitectura hexagonal/clean architecture
- Se separan casos de uso de la lógica de infraestructura
- Los repositorios deben usarse para persistencia en lugar de `.save()` directo
- El código debe ser modular y cada método debe tener una única responsabilidad

## Próximos Pasos para Continuar

1. Extraer el código seleccionado a un método privado `_prepare_and_send_email_message()`
2. Actualizar `_prepare_and_send_emails()` para usar `repository.save_order()` con `update_fields`
3. Localizar la vista con el método `update` relacionado
4. Aplicar refactorización similar en la vista si es necesario
5. Ejecutar pruebas para validar los cambios

## Comandos Útiles

```powershell
# Ver estructura de archivos
Get-ChildItem -Path "apps\orden_pagos" -Recurse -Filter "*.py"

# Buscar vistas relacionadas
Select-String -Path "apps\orden_pagos\views\*.py" -Pattern "def update"

# Ejecutar pruebas
python manage.py test apps.orden_pagos
```

---

**Fin del Contexto**

