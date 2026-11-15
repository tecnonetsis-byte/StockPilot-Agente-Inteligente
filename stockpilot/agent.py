"""Orquestador observable. Selecciona herramientas, reacciona a errores y se detiene antes de escrituras.
Funciona sin LLM en modo de examen, con decisiones por reglas reproducibles.
Modo LLM real opcional en langchain_agent.py.
"""
import re
import unicodedata
import uuid
from decimal import Decimal
from .tools import money


def normalizar(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


class StockPilotAgent:
    MAX_PASOS = 5

    def __init__(self, inventory, currency, orders):
        self.inventory = inventory
        self.currency = currency
        self.orders = orders
        self.pending = {}

    def _sku(self, message):
        m = normalizar(message)
        for p in self.inventory.catalog["productos"]:
            if normalizar(p["sku"]) in m:
                return p["sku"]
        for p in self.inventory.catalog["productos"]:
            if any(normalizar(a) in m for a in p.get("alias", [])):
                return p["sku"]
        return None

    def run(self, message, thread_id=None):
        tid = thread_id or str(uuid.uuid4())
        trace = []
        def step(tool, result):
            if len(trace) >= self.MAX_PASOS:
                raise RuntimeError("Limite de pasos excedido")
            trace.append({"herramienta": tool, "salida": result})

        sku = self._sku(message)
        m = normalizar(message)
        if not sku:
            return {"thread_id": tid, "estado": "sin_herramientas", "respuesta": "Indica un SKU: C20W, C40W, CBLC, CBCC o FUNDA.", "traza": trace}
        requiere_orden = any(x in m for x in ["registr", "orden", "pedido", "comprar", "compra"])
        consulta_stock = any(x in m for x in ["cuant", "stock", "quedan", "existenc", "disponibl"])
        consulta_reponer = any(x in m for x in ["repon", "cotiz", "analiz", "calcul", "necesit", "suger"])
        if not any([requiere_orden, consulta_stock, consulta_reponer]):
            return {"thread_id": tid, "estado": "sin_herramientas", "respuesta": "Indica si deseas stock, cotizacion o registrar orden.", "traza": trace}
        dato = self.inventory.inventario(sku)
        step("consultar_inventario", dato)
        if isinstance(dato, str) and dato.startswith("ERROR:"):
            return {"thread_id": tid, "estado": "error", "respuesta": dato, "traza": trace}
        if consulta_stock and not (requiere_orden or consulta_reponer):
            return {"thread_id": tid, "estado": "finalizado", "respuesta": f"{dato['producto']}: {dato['stock']} unidades simuladas disponibles.", "traza": trace}
        calc = self.inventory.reposicion(sku)
        step("calcular_reposicion", calc)
        if isinstance(calc, str) and calc.startswith("ERROR:"):
            return {"thread_id": tid, "estado": "error", "respuesta": calc, "traza": trace}
        if calc["unidades_sugeridas"] == 0:
            return {"thread_id": tid, "estado": "finalizado", "respuesta": "No se necesita reposicion: stock suficiente. No se consulta API ni se registra orden.", "traza": trace}
        rate = self.currency.consultar_usd_bob()
        step("consultar_tipo_cambio_publico", rate)
        if isinstance(rate, str) and rate.startswith("ERROR:"):
            return {"thread_id": tid, "estado": "error_api", "respuesta": rate + ". No se crea orden ni se inventa tasa.", "traza": trace}
        bob = money(Decimal(calc["costo_total_usd"]) * Decimal(str(rate["usd_bob"])))
        summary = (f"SKU {sku}: sugeridas {calc['unidades_sugeridas']} unidades; "
                   f"USD {calc['costo_total_usd']}; BOB {bob} "
                   f"(tipo {rate['usd_bob']}, modo {rate['modo']}; no es cotizacion de venta).")
        if not requiere_orden:
            return {"thread_id": tid, "estado": "finalizado", "respuesta": summary, "traza": trace}
        self.pending[tid] = {"sku": sku, "unidades": calc["unidades_sugeridas"],
                             "total_usd": calc["costo_total_usd"], "total_bob": bob, "traza": trace,
                             "resumen": summary}
        # Interrupcion ANTES de ejecutar la escritura. El agente no se autoaprueba.
        return {"thread_id": tid, "estado": "PENDIENTE_APROBACION_HUMANA",
                "respuesta": summary + " ACCION BLOQUEADA: ¿Aprobar o rechazar registro simulado?",
                "traza": trace, "control": {"herramienta": "registrar_orden_reposicion",
                                          "opciones": ["approve", "reject"], "ejecutada": False}}

    def resume(self, thread_id, decision):
        if thread_id not in self.pending:
            return {"thread_id": thread_id, "estado": "error", "respuesta": "ERROR: No existe una ejecucion pendiente", "traza": []}
        if decision not in ("approve", "reject"):
            return {"thread_id": thread_id, "estado": "PENDIENTE_APROBACION_HUMANA",
                    "respuesta": "ERROR: Decision invalida; solo approve o reject.", "traza": self.pending[thread_id]["traza"]}
        p = self.pending.pop(thread_id)
        trace = list(p["traza"])
        if decision == "reject":
            trace.append({"herramienta": "control_humano", "salida": "RECHAZADO; registro nunca ejecutado"})
            return {"thread_id": thread_id, "estado": "RECHAZADO_POR_HUMANO", "respuesta": "Orden rechazada por el operador. Cero escrituras realizadas.", "traza": trace, "control": {"decision": "reject", "ejecutada": False}}
        result = self.orders.registrar(p["sku"], p["unidades"], p["total_usd"], p["total_bob"], thread_id, aprobado=True)
        trace.append({"herramienta": "registrar_orden_reposicion", "salida": result})
        return {"thread_id": thread_id, "estado": "APROBADO_Y_REGISTRADO_SIMULADO", "respuesta": p["resumen"] + " Orden registrada tras aprobacion explicita.", "traza": trace,
                "control": {"decision": "approve", "ejecutada": True}}
