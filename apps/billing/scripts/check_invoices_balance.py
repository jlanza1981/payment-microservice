"""
Script para verificar el estado de balance de facturas.
Muestra estadísticas sin hacer cambios.

USO:
    Desde la raíz del proyecto:
    python apps/billing/scripts/check_invoices_balance.py
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
from apps.billing.models import Invoice


def check_invoices_status():
    """
    Verifica el estado de balance de todas las facturas y muestra estadísticas
    """
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE BALANCE EN FACTURAS")
    print("=" * 80 + "\n")

    # Facturas anuladas
    print("📋 FACTURAS ANULADAS (Status 'A')")
    print("-" * 80)
    anuladas_total = Invoice.objects.filter(status='A').count()
    anuladas_incorrectas = Invoice.objects.filter(status='A').exclude(balance_due=Decimal('0.00')).count()
    print(f"Total facturas anuladas: {anuladas_total}")
    print(f"Con balance incorrecto (!=0): {anuladas_incorrectas}")
    if anuladas_incorrectas > 0:
        print("❌ Hay facturas anuladas con balance incorrecto")
        for inv in Invoice.objects.filter(status='A').exclude(balance_due=Decimal('0.00'))[:5]:
            print(f"  - {inv.invoice_number}: Balance = ${inv.balance_due}")
        if anuladas_incorrectas > 5:
            print(f"  ... y {anuladas_incorrectas - 5} más")
    else:
        print("✅ Todas las facturas anuladas tienen balance correcto (0.00)")
    print()

    # Facturas exoneradas
    print("🎁 FACTURAS EXONERADAS (Status 'E')")
    print("-" * 80)
    exoneradas_total = Invoice.objects.filter(status='E').count()
    exoneradas_incorrectas = Invoice.objects.filter(status='E').exclude(balance_due=Decimal('0.00')).count()
    print(f"Total facturas exoneradas: {exoneradas_total}")
    print(f"Con balance incorrecto (!=0): {exoneradas_incorrectas}")
    if exoneradas_incorrectas > 0:
        print("❌ Hay facturas exoneradas con balance incorrecto")
        for inv in Invoice.objects.filter(status='E').exclude(balance_due=Decimal('0.00'))[:5]:
            print(f"  - {inv.invoice_number}: Total=${inv.total}, Balance=${inv.balance_due}")
        if exoneradas_incorrectas > 5:
            print(f"  ... y {exoneradas_incorrectas - 5} más")
    else:
        print("✅ Todas las facturas exoneradas tienen balance correcto (0.00)")
    print()

    # Facturas pagadas
    print("💰 FACTURAS PAGADAS (Status 'P')")
    print("-" * 80)
    pagadas_total = Invoice.objects.filter(status='P').count()
    pagadas_incorrectas = Invoice.objects.filter(status='P').exclude(balance_due=Decimal('0.00')).count()
    print(f"Total facturas pagadas: {pagadas_total}")
    print(f"Con balance incorrecto (!=0): {pagadas_incorrectas}")
    if pagadas_incorrectas > 0:
        print("❌ Hay facturas pagadas con balance incorrecto")
        for inv in Invoice.objects.filter(status='P').exclude(balance_due=Decimal('0.00'))[:5]:
            print(f"  - {inv.invoice_number}: Total=${inv.total}, Balance=${inv.balance_due}")
        if pagadas_incorrectas > 5:
            print(f"  ... y {pagadas_incorrectas - 5} más")
    else:
        print("✅ Todas las facturas pagadas tienen balance correcto (0.00)")
    print()

    # Facturas parcialmente pagadas
    print("📊 FACTURAS PARCIALMENTE PAGADAS (Status 'PP')")
    print("-" * 80)
    parciales_total = Invoice.objects.filter(status='PP').count()
    parciales_invalidas = Invoice.objects.filter(status='PP').filter(balance_due__lte=Decimal('0.00')).count()
    print(f"Total facturas parcialmente pagadas: {parciales_total}")
    print(f"Con balance <= 0 (inválido): {parciales_invalidas}")
    if parciales_invalidas > 0:
        print("❌ Hay facturas parciales con balance inválido")
        for inv in Invoice.objects.filter(status='PP').filter(balance_due__lte=Decimal('0.00'))[:5]:
            print(f"  - {inv.invoice_number}: Total=${inv.total}, Balance=${inv.balance_due}")
    else:
        print("✅ Todas las facturas parciales tienen balance válido (>0)")
    print()

    # Facturas pendientes
    print("⏳ FACTURAS PENDIENTES (Status 'PE')")
    print("-" * 80)
    pendientes_total = Invoice.objects.filter(status='PE').count()
    pendientes_invalidas = Invoice.objects.filter(status='PE').exclude(balance_due=models.F('total')).count()
    print(f"Total facturas pendientes: {pendientes_total}")
    print(f"Con balance != total: {pendientes_invalidas}")
    if pendientes_invalidas > 0:
        print("⚠️ Hay facturas pendientes donde balance != total")
        for inv in Invoice.objects.filter(status='PE').exclude(balance_due=models.F('total'))[:5]:
            print(f"  - {inv.invoice_number}: Total=${inv.total}, Balance=${inv.balance_due}")
    else:
        print("✅ Todas las facturas pendientes tienen balance = total")
    print()

    # Resumen
    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    total_incorrectas = anuladas_incorrectas + exoneradas_incorrectas + pagadas_incorrectas + parciales_invalidas
    if total_incorrectas > 0:
        print(f"❌ Total de facturas con balance incorrecto: {total_incorrectas}")
        print(f"\n💡 Para corregir, ejecuta:")
        print(f"   python apps/billing/scripts/fix_exonerated_invoices_balance.py")
    else:
        print("✅ Todas las facturas tienen balance correcto")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    from django.db import models

    check_invoices_status()
