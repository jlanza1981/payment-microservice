"""
Ejemplos de uso del endpoint de pagos exonerados.

Este archivo contiene ejemplos prácticos de cómo consumir el endpoint
desde Python usando la librería requests.

Instalación: pip install requests
"""
import json

import requests

# Configuración
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/payment-orders/exonerated/"
AUTH_TOKEN = "tu_token_aqui"  # Reemplazar con token real

# Headers
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def crear_pago_exonerado_orden_nueva():
    """
    Ejemplo 1: Crear pago exonerado con una orden nueva.

    Caso de uso: Estudiante con beca completa que necesita
    registrar inscripción y materiales sin costo.
    """
    payload = {
        "student_id": 123,
        "concepts": [
            {"concept_id": 1, "quantity": 1},  # Inscripción
            {"concept_id": 5, "quantity": 2}  # Materiales
        ],
        "payer_name": "Juan Pérez González",
        "advisor_id": 5,
        "notes": "Beca completa 2026 - Mérito académico"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Pago exonerado creado exitosamente!")
        print(f"Orden: {data['data']['order_number']}")
        print(f"Factura: {data['data']['invoice_number']}")
        print(f"Pago: {data['data']['payment_number']}")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"Respuesta: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def crear_pago_exonerado_orden_existente():
    """
    Ejemplo 2: Exonerar una orden de pago existente.

    Caso de uso: Una orden ya fue creada pero se aprueba
    una exoneración posteriormente.
    """
    payload = {
        "order_payment_id": 456,
        "payer_name": "María García López",
        "advisor_id": 3,
        "notes": "Exoneración aprobada por Dirección - Convenio institucional"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Orden exonerada exitosamente!")
        print(f"Orden: {data['data']['order_number']}")
        print(f"Factura: {data['data']['invoice_number']}")
        print(f"Pago: {data['data']['payment_number']}")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"Respuesta: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def crear_pago_exonerado_sin_advisor():
    """
    Ejemplo 3: Crear pago exonerado sin especificar asesor.

    Caso de uso: Proceso automatizado o cuando el asesor
    no es relevante para el registro.
    """
    payload = {
        "student_id": 789,
        "concepts": [
            {"concept_id": 1, "quantity": 1}
        ],
        "payer_name": "Carlos Rodríguez",
        "notes": "Cortesía - Evento especial"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Pago exonerado creado sin asesor!")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"Respuesta: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def crear_pago_exonerado_multiples_conceptos():
    """
    Ejemplo 4: Crear pago con múltiples conceptos y cantidades.

    Caso de uso: Beca que cubre varios servicios diferentes.
    """
    payload = {
        "student_id": 234,
        "concepts": [
            {"concept_id": 1, "quantity": 1},  # Inscripción
            {"concept_id": 2, "quantity": 4},  # Semanas de curso
            {"concept_id": 5, "quantity": 1},  # Materiales
            {"concept_id": 8, "quantity": 1}  # Certificado
        ],
        "payer_name": "Ana Martínez Silva",
        "advisor_id": 7,
        "notes": "Beca completa - Programa de becarios 2026"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Pago exonerado con múltiples conceptos!")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"Respuesta: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def manejar_error_estudiante_no_existe():
    """
    Ejemplo 5: Manejo de error cuando el estudiante no existe.
    """
    payload = {
        "student_id": 99999,  # ID que no existe
        "concepts": [
            {"concept_id": 1, "quantity": 1}
        ],
        "payer_name": "Usuario Inexistente"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Respuesta:", data)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ Error 404: Estudiante no encontrado")
            print(f"Detalle: {e.response.json()}")
        else:
            print(f"❌ Error HTTP {e.response.status_code}")
            print(f"Respuesta: {e.response.text}")


def manejar_error_orden_ya_pagada():
    """
    Ejemplo 6: Manejo de error cuando se intenta pagar una orden ya pagada.
    """
    payload = {
        "order_payment_id": 123,  # Orden que ya está pagada
        "payer_name": "Test Usuario"
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Respuesta:", data)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("❌ Error 400: Esta orden ya está pagada")
            print(f"Detalle: {e.response.json()}")
        else:
            print(f"❌ Error HTTP {e.response.status_code}")
            print(f"Respuesta: {e.response.text}")


def manejar_error_validacion():
    """
    Ejemplo 7: Manejo de error de validación (falta información).
    """
    payload = {
        "payer_name": "Test Usuario",
        "notes": "Sin orden ni estudiante"
        # Falta order_payment_id O (student_id + concepts)
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Respuesta:", data)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:  # Unprocessable Entity (validación)
            print("❌ Error de validación")
            print(f"Detalle: {e.response.json()}")
        else:
            print(f"❌ Error HTTP {e.response.status_code}")
            print(f"Respuesta: {e.response.text}")


def procesar_multiples_exoneraciones(lista_estudiantes):
    """
    Ejemplo 8: Procesar múltiples exoneraciones en batch.

    Args:
        lista_estudiantes: Lista de IDs de estudiantes a exonerar
    """
    resultados = []

    for student_id in lista_estudiantes:
        payload = {
            "student_id": student_id,
            "concepts": [
                {"concept_id": 1, "quantity": 1}
            ],
            "payer_name": f"Estudiante {student_id}",
            "notes": "Exoneración masiva - Evento especial"
        }

        try:
            response = requests.post(
                API_ENDPOINT,
                headers=HEADERS,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            resultados.append({
                "student_id": student_id,
                "success": True,
                "data": data
            })
            print(f"✅ Estudiante {student_id}: {data['data']['order_number']}")

        except Exception as e:
            resultados.append({
                "student_id": student_id,
                "success": False,
                "error": str(e)
            })
            print(f"❌ Estudiante {student_id}: {e}")

    return resultados


# Función principal para ejecutar ejemplos
def main():
    """
    Ejecuta los ejemplos.
    Descomenta el que quieras probar.
    """
    print("=" * 60)
    print("EJEMPLOS DE USO - ENDPOINT DE PAGOS EXONERADOS")
    print("=" * 60)
    print()

    # Ejemplo 1: Orden nueva
    # print("\n--- Ejemplo 1: Crear orden nueva ---")
    # crear_pago_exonerado_orden_nueva()

    # Ejemplo 2: Orden existente
    # print("\n--- Ejemplo 2: Exonerar orden existente ---")
    # crear_pago_exonerado_orden_existente()

    # Ejemplo 3: Sin asesor
    # print("\n--- Ejemplo 3: Sin asesor ---")
    # crear_pago_exonerado_sin_advisor()

    # Ejemplo 4: Múltiples conceptos
    # print("\n--- Ejemplo 4: Múltiples conceptos ---")
    # crear_pago_exonerado_multiples_conceptos()

    # Ejemplo 5: Error - Estudiante no existe
    # print("\n--- Ejemplo 5: Manejo de errores ---")
    # manejar_error_estudiante_no_existe()

    # Ejemplo 6: Error - Orden ya pagada
    # print("\n--- Ejemplo 6: Orden ya pagada ---")
    # manejar_error_orden_ya_pagada()

    # Ejemplo 7: Error - Validación
    # print("\n--- Ejemplo 7: Error de validación ---")
    # manejar_error_validacion()

    # Ejemplo 8: Batch processing
    # print("\n--- Ejemplo 8: Procesamiento en batch ---")
    # estudiantes = [101, 102, 103, 104, 105]
    # resultados = procesar_multiples_exoneraciones(estudiantes)
    # print(f"\nProcesados: {len(resultados)}")
    # print(f"Exitosos: {sum(1 for r in resultados if r['success'])}")
    # print(f"Fallidos: {sum(1 for r in resultados if not r['success'])}")

    print("\n✅ Recuerda configurar el AUTH_TOKEN antes de ejecutar!")


if __name__ == "__main__":
    main()
