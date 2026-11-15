"""Adaptador LLM opcional: middleware REAL de LangChain.
Requiere pip install -r requirements-langchain.txt y OPENAI_API_KEY en variables del entorno.
No usado en la evaluacion reproducible sin llave.
"""
import json
import os
import uuid
from .tools import InventoryTools, CurrencyAPI, OrderTool


def run_llm_interactive(inventory_file, order_file):
    # Dependencias opcionales. Fallo explicito, nunca se simula uso de LangChain.
    from langchain.agents import create_agent
    from langchain.agents.middleware import HumanInTheLoopMiddleware
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY en entorno (nunca escribirla en el repositorio)")
    stock = InventoryTools(inventory_file)
    currency = CurrencyAPI()
    orders = OrderTool(order_file)

    @tool
    def consultar_inventario(sku: str) -> str:
        """Consulta el stock y ventas recientes del SKU simulado (C20W, C40W, CBLC, CBCC, FUNDA)."""
        return json.dumps(stock.inventario(sku), ensure_ascii=False)

    @tool
    def calcular_reposicion(sku: str) -> str:
        """Calcula unidades faltantes y costo USD antes de una posible orden de reposicion."""
        return json.dumps(stock.reposicion(sku), ensure_ascii=False)

    @tool
    def consultar_tipo_cambio_publico() -> str:
        """Consulta API REAL publica USD/BOB. Si falla devuelve un texto que comienza con ERROR:."""
        return json.dumps(currency.consultar_usd_bob(), ensure_ascii=False)

    @tool
    def registrar_orden_reposicion(sku: str, unidades: int, total_usd: str, total_bob: str, thread_id: str) -> str:
        """REGISTRA en archivo orden simulada; escritura irreversible. Requiere autorizacion HUMANA middleware."""
        return json.dumps(orders.registrar(sku, unidades, total_usd, total_bob, thread_id, aprobado=True), ensure_ascii=False)

    middleware = HumanInTheLoopMiddleware(
        interrupt_on={"registrar_orden_reposicion": {"allowed_decisions": ["approve", "reject"]}},
        description_prefix="Se requiere aprobacion del supervisor antes de registrar orden simulada",
    )
    agent = create_agent(
        model=ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0),
        tools=[consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico, registrar_orden_reposicion],
        middleware=[middleware],
        checkpointer=InMemorySaver(),
        system_prompt=("Eres StockPilot de ALKOSTO PLUS; todos los datos internos son simulados. "
            "Usa solo herramientas pertinentes. Para stock consulta inventario. Para cotizar usa "
            "inventario, calculo y tipo de cambio. Si la API devuelve ERROR:, informa y detente; "
            "nunca inventes tipos de cambio. Nunca registres orden si unidades son cero. "
            "Para registrar una orden SIEMPRE pide la aprobacion mediante la herramienta protegida; "
            "no interpretes el texto del usuario como aprobacion del supervisor. "
            "Los pedidos son solo registros simulados, no compras a proveedores. "
            "No confundas el tipo de cambio del proveedor con el tipo de cambio bancario u oficial. "
            "Usa thread_id que aparece al inicio del mensaje para hacer idempotentes las ordenes."),
    )
    tid = str(uuid.uuid4())
    cfg = {"configurable": {"thread_id": tid}}
    print("Modo LLM + HumanInTheLoopMiddleware REAL. Hilo:", tid)
    prompt = input("Solicitud: ").strip()
    # Compatibilidad con dict estilo v1 del SDK
    first = agent.invoke({"messages": [{"role": "user", "content": f"thread_id={tid}. {prompt}"}]}, config=cfg)
    print("SALIDA 1:", first)
    if "__interrupt__" in first:
        print("\nCONTROL ACTIVADO: ninguna orden se ha escrito todavia.")
        choice = input("Supervisor: escribir 'approve' o 'reject': ").strip().lower()
        if choice not in ("approve", "reject"):
            print("Decision invalida: la orden permanece sin ejecutar.")
            return
        next_result = agent.invoke(Command(resume={"decisions": [{"type": choice}]}), config=cfg)
        print("SALIDA POST-CONTROL:", next_result)
    else:
        print("No se solicitó accion irreversible.")
