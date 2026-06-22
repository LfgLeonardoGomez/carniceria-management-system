"""Tests for reporte.service.generar_csv.

TDD cycle: RED → GREEN → TRIANGULATE
Tasks:
  4.1 — generar_csv returns UTF-8 bytes with BOM, correct header (RN-REP-03 order),
         null ganancia renders as empty string, strings with commas are quoted
  4.3 — product list containing a comma is quoted correctly
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest


def _make_row(
    cliente_nombre: str = "Juan Perez",
    productos: str = "Asado",
    total_kilos: str = "2.000",
    subtotal: str = "2000.00",
    total: str = "2000.00",
    medios_pago: str = "efectivo",
    ganancia_estimada: str | None = "500.00",
) -> "VentaReporteRow":
    from src.modules.reporte.schemas import VentaReporteRow
    return VentaReporteRow(
        venta_id=uuid.uuid4(),
        fecha=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        cliente_nombre=cliente_nombre,
        productos=productos,
        total_kilos=Decimal(total_kilos),
        subtotal=Decimal(subtotal),
        total=Decimal(total),
        medios_pago=medios_pago,
        ganancia_estimada=Decimal(ganancia_estimada) if ganancia_estimada is not None else None,
    )


# ---------------------------------------------------------------------------
# Task 4.1 — RED: BOM, correct header, null ganancia, comma quoting
# ---------------------------------------------------------------------------

def test_generar_csv_returns_utf8_bom():
    """generar_csv returns bytes starting with UTF-8 BOM (\\xef\\xbb\\xbf)."""
    from src.modules.reporte.service import generar_csv

    result = generar_csv([_make_row()])
    assert isinstance(result, bytes)
    # UTF-8 BOM is the first 3 bytes: 0xEF 0xBB 0xBF
    assert result[:3] == b"\xef\xbb\xbf", f"Missing BOM, got: {result[:6]!r}"


def test_generar_csv_header_row():
    """Header matches RN-REP-03 column order."""
    from src.modules.reporte.service import generar_csv
    import csv, io

    result = generar_csv([_make_row()])
    # Decode without BOM
    text = result.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)

    expected = [
        "fecha", "cliente", "productos", "kilos_vendidos",
        "subtotal", "total", "medio_pago", "ganancia_estimada",
    ]
    assert header == expected


def test_generar_csv_null_ganancia_renders_as_empty_string():
    """Null ganancia_estimada renders as empty string (two consecutive commas)."""
    from src.modules.reporte.service import generar_csv
    import csv, io

    result = generar_csv([_make_row(ganancia_estimada=None)])
    text = result.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    next(reader)  # skip header
    row = next(reader)

    ganancia_col = row[7]  # 0-indexed: 8th column
    assert ganancia_col == "", f"Expected empty string, got: {ganancia_col!r}"


def test_generar_csv_strings_with_commas_are_quoted():
    """Strings containing commas are properly quoted in the output."""
    from src.modules.reporte.service import generar_csv

    result = generar_csv([_make_row(productos="Nalga, Cuadril")])
    text = result.decode("utf-8-sig")

    # The CSV parser should round-trip the value correctly
    import csv, io
    reader = csv.reader(io.StringIO(text))
    next(reader)  # header
    data_row = next(reader)
    assert data_row[2] == "Nalga, Cuadril"


# ---------------------------------------------------------------------------
# Task 4.3 — TRIANGULATE: comma in product list quoted correctly
# ---------------------------------------------------------------------------

def test_generar_csv_multiple_commas_in_products():
    """Multiple commas in productos column are all preserved after round-trip."""
    from src.modules.reporte.service import generar_csv
    import csv, io

    row = _make_row(productos="Nalga, Cuadril, Bife de lomo")
    result = generar_csv([row])
    text = result.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    next(reader)
    data_row = next(reader)
    assert data_row[2] == "Nalga, Cuadril, Bife de lomo"
