"""
Script de prueba para verificar la interfaz y repositorio de Payment.
Ubicación: apps/pagos/tests/test_payment_repository.py
Ejecutar con: python manage.py shell < apps/pagos/tests/test_payment_repository.py
"""

import os
import sys
import django

# Ajustar path para estar en la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.models import Payment

print("=" * 60)
print("TEST: Verificación de Payment Repository")
print("=" * 60)

# 1. Verificar que la interfaz es abstracta
print("\n1. Verificando interfaz abstracta...")
try:
    interface = PaymentRepositoryInterface()
    print("   ❌ ERROR: No debería poder instanciar la interfaz")
except TypeError as e:
    print("   ✓ Correcto: La interfaz es abstracta")
    print(f"   Mensaje: {str(e)[:80]}...")

# 2. Verificar que el repositorio se puede instanciar
print("\n2. Instanciando repositorio...")
try:
    repo = PaymentRepository()
    print("   ✓ Repositorio instanciado correctamente")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# 3. Verificar que el repositorio implementa la interfaz
print("\n3. Verificando implementación de interfaz...")
if isinstance(repo, PaymentRepositoryInterface):
    print("   ✓ El repositorio implementa PaymentRepositoryInterface")
else:
    print("   ❌ ERROR: El repositorio no implementa la interfaz")

# 4. Verificar métodos principales
print("\n4. Verificando métodos principales...")
required_methods = [
    'list_all', 'create', 'update', 'cancel', 'verify', 'reject',
    'get_by_id', 'get_by_payment_number', 'get_by_id_with_relations',
    'save_payment', 'get_payments_by_invoice', 'get_payments_by_user',
    'get_pending_payments_by_user', 'get_verified_payments_by_invoice',
    'calculate_total_payments_by_invoice', 'get_payments_by_date_range',
    'get_payments_by_advisor', 'get_payment_allocations_by_payment'
]

missing_methods = []
for method_name in required_methods:
    if not hasattr(repo, method_name):
        missing_methods.append(method_name)

if not missing_methods:
    print(f"   ✓ Todos los métodos requeridos están presentes ({len(required_methods)} métodos)")
else:
    print(f"   ❌ Faltan métodos: {', '.join(missing_methods)}")

# 5. Verificar métodos privados
print("\n5. Verificando métodos privados (helpers)...")
private_methods = [
    '_normalize_payment_data',
    '_create_payment_allocations',
    '_normalize_allocation_data',
    '_reload_payment',
    '_apply_filters'
]

existing_private = []
for method_name in private_methods:
    if hasattr(repo, method_name):
        existing_private.append(method_name)

print(f"   ✓ Métodos privados encontrados: {len(existing_private)}/{len(private_methods)}")
for method_name in existing_private:
    print(f"     - {method_name}")

# 6. Verificar count de pagos existentes
print("\n6. Verificando modelo Payment...")
try:
    count = Payment.objects.count()
    print(f"   ✓ Total de pagos en BD: {count}")
except Exception as e:
    print(f"   ❌ ERROR al consultar BD: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETADO")
print("=" * 60)
print("\nNOTA: Para probar las operaciones CRUD, ejecuta:")
print("  python manage.py shell")
print("  >>> from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository")
print("  >>> repo = PaymentRepository()")
print("  >>> payments = repo.list_all()")
