"""
Script para corregir el balance_due de facturas exoneradas.
Las facturas con status 'E' (Exonerada) deben tener balance_due = 0

USO:
    Desde la raíz del proyecto:
    python apps/billing/scripts/fix_exonerated_invoices_balance.py
"""
import os
import sys

import django

# Configurar el path de Django PRIMERO
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

# AHORA sí importar los modelos de Django
from decimal import Decimal
from django.db import transaction

from apps.billing.models import Invoice


def fix_exonerated_invoices_balance():
    """
    Actualiza el balance_due a 0 para todas las facturas exoneradas
    """
    print("=== Corrección de balance_due en facturas exoneradas ===\n")

    # Buscar facturas exoneradas con balance_due incorrecto
    exonerated_invoices = Invoice.objects.filter(
        status='E'  # Exonerada
    ).exclude(
        balance_due=Decimal('0.00')
    )

    count = exonerated_invoices.count()
    print(f"Facturas exoneradas con balance_due incorrecto: {count}\n")

    if count == 0:
        print("✅ No hay facturas exoneradas con balance incorrecto.")
        return

    # Mostrar detalles
    print("Facturas a corregir:")
    print("-" * 80)
    for invoice in exonerated_invoices:
        print(f"ID: {invoice.id}")
        print(f"Número: {invoice.invoice_number}")
        print(f"Estudiante: {invoice.user.get_full_name()}")
        print(f"Total: ${invoice.total}")
        print(f"Balance actual (incorrecto): ${invoice.balance_due}")
        print("-" * 80)

    # Confirmar corrección
    confirm = input(f"\n¿Desea corregir estas {count} facturas? (si/no): ").lower()

    if confirm == 'si':
        with transaction.atomic():
            updated = exonerated_invoices.update(balance_due=Decimal('0.00'))
            print(f"\n✅ {updated} facturas actualizadas correctamente.")
            print("   balance_due establecido en 0.00 para todas las facturas exoneradas.")
    else:
        print("\n❌ Operación cancelada.")


def verify_all_invoices_balance():
    """
    Verifica y corrige el balance de todas las facturas según su status
    """
    print("\n=== Verificación completa de balance en facturas ===\n")

    # Facturas anuladas
    anuladas = Invoice.objects.filter(status='A').exclude(balance_due=Decimal('0.00'))
    print(f"Facturas anuladas con balance incorrecto: {anuladas.count()}")

    # Facturas exoneradas
    exoneradas = Invoice.objects.filter(status='E').exclude(balance_due=Decimal('0.00'))
    print(f"Facturas exoneradas con balance incorrecto: {exoneradas.count()}")

    # Facturas pagadas
    pagadas = Invoice.objects.filter(status='P').exclude(balance_due=Decimal('0.00'))
    print(f"Facturas pagadas con balance incorrecto: {pagadas.count()}")

    total_incorrectas = anuladas.count() + exoneradas.count() + pagadas.count()

    if total_incorrectas == 0:
        print("\n✅ Todas las facturas tienen balance correcto.")
        return

    print(f"\nTotal de facturas con balance incorrecto: {total_incorrectas}")
    confirm = input("\n¿Desea corregir todas estas facturas? (si/no): ").lower()

    if confirm == 'si':
        with transaction.atomic():
            # Corregir anuladas
            if anuladas.exists():
                count_a = anuladas.update(balance_due=Decimal('0.00'))
                print(f"✅ {count_a} facturas anuladas corregidas")

            # Corregir exoneradas
            if exoneradas.exists():
                count_e = exoneradas.update(balance_due=Decimal('0.00'))
                print(f"✅ {count_e} facturas exoneradas corregidas")

            # Corregir pagadas
            if pagadas.exists():
                count_p = pagadas.update(balance_due=Decimal('0.00'))
                print(f"✅ {count_p} facturas pagadas corregidas")

            print(f"\n✅ Total: {total_incorrectas} facturas corregidas.")
    else:
        print("\n❌ Operación cancelada.")


if __name__ == '__main__':

    print("\n" + "=" * 80)
    print("SCRIPT DE CORRECCIÓN DE BALANCE EN FACTURAS")
    print("=" * 80)
    print("\nOpciones:")
    print("1. Corregir solo facturas exoneradas")
    print("2. Verificar y corregir todas las facturas (anuladas, exoneradas, pagadas)")

    opcion = input("\nSeleccione una opción (1/2): ")

    if opcion == '1':
        fix_exonerated_invoices_balance()
    elif opcion == '2':
        verify_all_invoices_balance()
    else:
        print("❌ Opción inválida")
