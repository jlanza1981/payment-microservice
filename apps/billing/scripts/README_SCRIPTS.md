# Scripts de Corrección de Balance en Facturas

## Ubicación

`apps/billing/scripts/`

## Scripts Disponibles

### 1. check_invoices_balance.py

**Propósito:** Verificar el estado de balance de facturas sin hacer cambios.

**Uso:**

```bash
python apps/billing/scripts/check_invoices_balance.py
```

**Qué hace:**

- ✅ Muestra estadísticas de facturas por estado
- ✅ Identifica facturas con balance incorrecto
- ✅ NO hace ningún cambio en la base de datos
- ✅ Ejecuta rápidamente sin interacción

**Salida:**

```
📋 FACTURAS ANULADAS (Status 'A')
Total facturas anuladas: 5
Con balance incorrecto (!=0): 2
❌ Hay facturas anuladas con balance incorrecto
  - INV-001: Balance = $100.00
  - INV-002: Balance = $250.00

🎁 FACTURAS EXONERADAS (Status 'E')
Total facturas exoneradas: 3
Con balance incorrecto (!=0): 1
❌ Hay facturas exoneradas con balance incorrecto
  - INV-003: Total=$500.00, Balance=$500.00

...
```

---

### 2. fix_exonerated_invoices_balance.py

**Propósito:** Corregir el balance de facturas con problemas.

**Uso:**

```bash
python apps/billing/scripts/fix_exonerated_invoices_balance.py
```

**Opciones:**

1. **Corregir solo facturas exoneradas**
    - Establece `balance_due = 0` en facturas con status 'E'

2. **Verificar y corregir todas las facturas**
    - Facturas anuladas (status 'A') → balance_due = 0
    - Facturas exoneradas (status 'E') → balance_due = 0
    - Facturas pagadas (status 'P') → balance_due = 0

**Flujo:**

1. El script muestra las facturas a corregir
2. Solicita confirmación (si/no)
3. Aplica los cambios en transacción atómica
4. Muestra resultado

**Ejemplo de ejecución:**

```
================================================================================
SCRIPT DE CORRECCIÓN DE BALANCE EN FACTURAS
================================================================================

Opciones:
1. Corregir solo facturas exoneradas
2. Verificar y corregir todas las facturas (anuladas, exoneradas, pagadas)

Seleccione una opción (1/2): 1

=== Corrección de balance_due en facturas exoneradas ===

Facturas exoneradas con balance_due incorrecto: 3

Facturas a corregir:
--------------------------------------------------------------------------------
ID: 123
Número: INV-2024-001
Estudiante: Juan Pérez
Total: $500.00
Balance actual (incorrecto): $500.00
--------------------------------------------------------------------------------
ID: 124
Número: INV-2024-002
Estudiante: María García
Total: $300.00
Balance actual (incorrecto): $300.00
--------------------------------------------------------------------------------
ID: 125
Número: INV-2024-003
Estudiante: Carlos López
Total: $450.00
Balance actual (incorrecto): $450.00
--------------------------------------------------------------------------------

¿Desea corregir estas 3 facturas? (si/no): si

✅ 3 facturas actualizadas correctamente.
   balance_due establecido en 0.00 para todas las facturas exoneradas.
```

---

## Flujo Recomendado

### Paso 1: Verificar Estado Actual

```bash
python apps/billing/scripts/check_invoices_balance.py
```

Esto te mostrará:

- Cuántas facturas tienen problemas
- Qué tipo de problemas tienen
- Sin riesgo de cambios accidentales

### Paso 2: Aplicar Correcciones

```bash
python apps/billing/scripts/fix_exonerated_invoices_balance.py
```

Selecciona la opción apropiada:

- Opción 1: Si solo necesitas corregir facturas exoneradas
- Opción 2: Para una corrección completa de todos los estados

### Paso 3: Verificar Correcciones

```bash
python apps/billing/scripts/check_invoices_balance.py
```

Deberías ver:

```
✅ Todas las facturas tienen balance correcto
```

---

## Problemas Comunes

### Error: ModuleNotFoundError: No module named 'apps'

**Causa:** El script no está configurando correctamente el path de Django.

**Solución:** El script ya está corregido. Asegúrate de ejecutarlo desde la raíz del proyecto:

```bash
cd C:\proyectos_django\api
python apps/billing/scripts/fix_exonerated_invoices_balance.py
```

### Warning: GLib-GIO-WARNING

**Causa:** Warnings normales de WeasyPrint en Windows.

**Solución:** Puedes ignorarlos, no afectan el funcionamiento del script.

---

## Seguridad

Ambos scripts usan:

- ✅ Transacciones atómicas (`transaction.atomic()`)
- ✅ Confirmación antes de aplicar cambios
- ✅ Filtros precisos para evitar cambios accidentales
- ✅ Logs detallados de los cambios aplicados

---

## Cuándo Usar Estos Scripts

### Usar `check_invoices_balance.py` cuando:

- 🔍 Quieras auditar el estado de las facturas
- 🔍 Necesites estadísticas rápidas
- 🔍 Estés investigando un problema reportado
- 🔍 Después de aplicar correcciones para verificar

### Usar `fix_exonerated_invoices_balance.py` cuando:

- 🔧 Detectes facturas exoneradas con balance > 0
- 🔧 Necesites corregir facturas anuladas/pagadas con balance incorrecto
- 🔧 Después de migrar datos
- 🔧 Después de cambios en la lógica de balance

---

## Notas Técnicas

- Los scripts configuran Django automáticamente
- Usan `Decimal` para precisión en cálculos monetarios
- Filtran por status usando los códigos del modelo:
    - 'A': Anulada
    - 'E': Exonerada
    - 'P': Pagada
    - 'PP': Parcialmente Pagada
    - 'PE': Pendiente
