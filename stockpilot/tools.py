"""Herramientas verificables e inyectables para facilitar pruebas sin Internet.
La herramienta de cotizacion REAL apunta al proveedor publico; modo simulado se etiqueta.
"""
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import requests

API_URL = "https://open.er-api.com/v6/latest/USD"
ATTRIBUTION = "Rates By Exchange Rate API - https://www.exchangerate-api.com"


def money(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class InventoryTools:
    def __init__(self, path):
        self.path = Path(path)
        self.catalog = json.loads(self.path.read_text(encoding="utf-8"))

    def producto(self, sku):
        for item in self.catalog["productos"]:
            if item["sku"] == sku:
                return dict(item)
        return None

    def inventario(self, sku):
        item = self.producto(sku)
        if not item:
            return "ERROR: SKU no encontrado en inventario simulado"
        return {"sku": sku, "producto": item["nombre"], "stock": item["stock"], "ventas_14d": item["ventas_14d"], "fuente": "inventario simulado local"}

    def reposicion(self, sku):
        item = self.producto(sku)
        if not item:
            return "ERROR: SKU inexistente"
        dias = self.catalog["objetivo_cobertura_dias"]
        periodo = self.catalog["periodo_ventas_dias"]
        objetivo = math.ceil(item["ventas_14d"] / periodo * dias)
        unidades = max(0, objetivo - item["stock"])
        usd = Decimal(str(unidades)) * Decimal(str(item["costo_unitario_usd"]))
        return {
            "sku": sku, "stock": item["stock"], "ventas_14d": item["ventas_14d"],
            "objetivo_dias": dias, "stock_objetivo": objetivo, "unidades_sugeridas": unidades,
            "costo_unitario_usd": money(item["costo_unitario_usd"]), "costo_total_usd": money(usd),
            "formula": "max(0, ceil(ventas_14d / 14 * 21) - stock)"
        }


class CurrencyAPI:
    def __init__(self, session=None, timeout=5):
        self.session = session or requests.Session()
        self.timeout = timeout

    def consultar_usd_bob(self):
        """Llamada HTTPS real sin credenciales; cualquier fallo empieza con ERROR:."""
        try:
            r = self.session.get(API_URL, timeout=self.timeout, headers={"Accept": "application/json"})
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, dict) or payload.get("result") != "success" or payload.get("base_code") != "USD":
                return "ERROR: La API devolvio un resultado no exitoso o base inesperada"
            rate = payload.get("rates", {}).get("BOB")
            if not isinstance(rate, (int, float)) or not 0 < rate < 1000:
                return "ERROR: La API no proporciono una tasa USD/BOB valida"
            return {"usd_bob": float(rate), "fuente": API_URL,
                    "actualizado_utc": payload.get("time_last_update_utc", "no informado"),
                    "modo": "API_REAL", "atribucion": ATTRIBUTION,
                    "advertencia": "Tasa informativa del proveedor; no sustituye tasa bancaria, oficial ni de venta"}
        except requests.exceptions.Timeout:
            return "ERROR: Tiempo de espera agotado consultando la API publica"
        except requests.exceptions.RequestException as ex:
            return "ERROR: Fallo de red o HTTP al consultar la API: " + type(ex).__name__
        except (ValueError, TypeError):
            return "ERROR: Respuesta JSON invalida de la API publica"


class SimulatedCurrency:
    """Solo para demos de cero red, no afirma consultar la API."""
    def consultar_usd_bob(self):
        return {"usd_bob": 11.70, "fuente": "ESCENARIO SIMULADO", "actualizado_utc": "SIMULADO",
                "modo": "SIMULADO_SIN_RED", "atribucion": "No es una cotizacion de mercado",
                "advertencia": "Tasa inventada para pruebas; no usar en precios reales"}


class FailingCurrency:
    def consultar_usd_bob(self):
        return "ERROR: HTTP 503 simulado; proveedor temporalmente no disponible"


class OrderTool:
    """Accion de escritura; su uso SOLO esta permitido despues de una aprobacion externa."""
    def __init__(self, path):
        self.path = Path(path)

    def registrar(self, sku, unidades, costo_total_usd, costo_total_bob, thread_id, aprobado):
        if aprobado is not True:
            return "ERROR: Se requiere una aprobacion humana explicita antes de registrar"
        if not isinstance(unidades, int) or unidades <= 0:
            return "ERROR: Unidades invalidas para orden"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existente = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    existente.append(json.loads(line))
        # Idempotencia: una aprobacion de hilo solo crea una orden.
        for order in existente:
            if order["thread_id"] == thread_id:
                return {"estado": "YA_EXISTE", "orden": order}
        order = {"orden_id": "SIM-" + str(len(existente) + 1).zfill(4), "sku": sku,
                 "unidades": unidades, "total_usd": costo_total_usd, "total_bob": costo_total_bob,
                 "tipo": "ORDEN_SIMULADA", "aprobacion": "APROBACION_EXTERNA_EXPLICITA",
                 "thread_id": thread_id, "creado_utc": datetime.now(timezone.utc).isoformat()}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(order, ensure_ascii=False) + "\n")
        return {"estado": "REGISTRADA", "orden": order}
