"""
Ejemplo de uso del servicio refactorizado en vistas Django/DRF.

Este archivo muestra cómo migrar del código antiguo al nuevo.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.pagos.application.dependencies import get_payment_history_service


# ========================================
# EJEMPLO 1: Vista básica
# ========================================

@api_view(['GET'])
def get_student_payment_history(request, student_id):
    """
    Endpoint para obtener el historial de pagos de un estudiante.
    
    GET /api/students/{student_id}/payments/
    """
    try:
        # 1. Obtener el servicio con todas sus dependencias
        service = get_payment_history_service()
        
        # 2. Construir la URL base desde el request
        base_url = request.build_absolute_uri('/')
        
        # 3. Obtener el historial de pagos
        payments = service.get_student_payments(
            student_id=student_id,
            base_url=base_url,
            ensure_pdfs=True  # Asegura que los PDFs existan
        )
        
        # 4. Serializar y retornar
        from apps.pagos.serializers import StudentPaymentSerializer
        serializer = StudentPaymentSerializer(payments, many=True)
        
        return Response({
            'count': len(payments),
            'results': serializer.data
        })
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Error obteniendo historial de pagos'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================================
# EJEMPLO 2: Vista con filtros
# ========================================

@api_view(['GET'])
def get_filtered_payment_history(request, student_id):
    """
    Endpoint con filtros por query params.
    
    GET /api/students/{student_id}/payments/?date_from=2024-01-01&date_to=2024-12-31
    """
    try:
        service = get_payment_history_service()
        base_url = request.build_absolute_uri('/')
        
        # Construir filtros desde query params
        filters = {}
        if request.query_params.get('date_from'):
            filters['date_from'] = request.query_params.get('date_from')
        if request.query_params.get('date_to'):
            filters['date_to'] = request.query_params.get('date_to')
        if request.query_params.get('status'):
            filters['status'] = request.query_params.get('status')
        
        # Obtener pagos con filtros
        payments = service.get_student_payments(
            student_id=student_id,
            filters=filters if filters else None,
            base_url=base_url,
            ensure_pdfs=True
        )
        
        from apps.pagos.serializers import StudentPaymentSerializer
        serializer = StudentPaymentSerializer(payments, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================================
# EJEMPLO 3: ViewSet de DRF
# ========================================

from rest_framework import viewsets
from rest_framework.decorators import action


class StudentPaymentViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar pagos de estudiantes.
    """
    
    @action(detail=True, methods=['get'], url_path='payment-history')
    def payment_history(self, request, pk=None):
        """
        Acción personalizada para obtener el historial de pagos.
        
        GET /api/students/{pk}/payment-history/
        """
        try:
            student_id = int(pk)
            
            # Obtener el servicio
            service = get_payment_history_service()
            base_url = request.build_absolute_uri('/')
            
            # Opción de no verificar PDFs para mayor rapidez
            ensure_pdfs = request.query_params.get('ensure_pdfs', 'true').lower() == 'true'
            
            payments = service.get_student_payments(
                student_id=student_id,
                base_url=base_url,
                ensure_pdfs=ensure_pdfs
            )
            
            from apps.pagos.serializers import StudentPaymentSerializer
            serializer = StudentPaymentSerializer(payments, many=True)
            
            return Response({
                'student_id': student_id,
                'payment_count': len(payments),
                'payments': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'ID de estudiante inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Error obteniendo historial de pagos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ========================================
# EJEMPLO 4: Vista sin verificación de PDFs (más rápida)
# ========================================

@api_view(['GET'])
def get_student_payment_history_fast(request, student_id):
    """
    Endpoint rápido que no verifica/regenera PDFs.
    Útil para listados donde no se necesitan los PDFs inmediatamente.
    
    GET /api/students/{student_id}/payments/fast/
    """
    try:
        service = get_payment_history_service()
        
        # Sin verificación de PDFs = más rápido
        payments = service.get_student_payments(
            student_id=student_id,
            ensure_pdfs=False  # No toca archivos
        )
        
        from apps.pagos.serializers import StudentPaymentSerializer
        serializer = StudentPaymentSerializer(payments, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================================
# EJEMPLO 5: Uso en Command (Django Management Command)
# ========================================

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Regenera PDFs faltantes para todos los estudiantes'

    def handle(self, *args, **options):
        """
        Comando para ejecutar desde CLI:
        python manage.py regenerate_missing_pdfs
        """
        from django.contrib.auth.models import User
        from apps.pagos.application.dependencies import get_payment_history_service
        
        service = get_payment_history_service()
        base_url = "https://production-url.com"  # URL de producción
        
        students = User.objects.filter(profile__is_student=True)
        
        for student in students:
            self.stdout.write(f"Procesando estudiante {student.id}...")
            
            try:
                payments = service.get_student_payments(
                    student_id=student.id,
                    base_url=base_url,
                    ensure_pdfs=True  # Regenera PDFs faltantes
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {len(payments)} pagos procesados"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Error: {str(e)}"
                    )
                )


# ========================================
# EJEMPLO 6: Uso en Celery Task
# ========================================

from celery import shared_task
from apps.pagos.application.utils import get_domain_name


@shared_task
def generate_student_payment_report(student_id):
    """
    Tarea asíncrona para generar reporte de pagos.
    
    Uso:
    generate_student_payment_report.delay(student_id=123)
    """
    from apps.pagos.application.dependencies import get_payment_history_service
    
    service = get_payment_history_service()
    
    # En Celery tasks NO hay request HTTP disponible, usar helper
    domain_name = get_domain_name()  # ✅ Helper simplificado
    
    payments = service.get_student_payments(
        student_id=student_id,
        domain_name=domain_name,  # ✅ Pasado desde caso de uso
        ensure_pdfs=True
    )
    
    # Generar reporte con los pagos
    # ... lógica de generación de reporte
    
    return {
        'student_id': student_id,
        'payment_count': len(payments),
        'status': 'completed'
    }

