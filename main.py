"""CLI reproducible de StockPilot.
Ejemplos: python main.py --demo | --eval | --interactive | --live-api | --llm
"""
import argparse
import json
from pathlib import Path
from stockpilot.tools import InventoryTools, CurrencyAPI, SimulatedCurrency, OrderTool
from stockpilot.agent import StockPilotAgent

ROOT = Path(__file__).resolve().parent


def create_agent(mode="simulado", orders_file=None):
    currency = CurrencyAPI() if mode == "real" else SimulatedCurrency()
    return StockPilotAgent(InventoryTools(ROOT / "data/inventario_simulado.json"), currency,
                           OrderTool(orders_file or ROOT / "salidas/ordenes_simuladas.jsonl"))


def show(output):
    print(json.dumps(output, ensure_ascii=False, indent=2))


def demo():
    dest = ROOT / "salidas/demo_ordenes.jsonl"
    if dest.exists():
        dest.unlink()  # solo archivo de DEMO, no produccion
    for title, text, answer in [
        ("CASO NORMAL - COTIZACION", "Analiza la reposicion del cable C-L", None),
        ("CASO ERROR API", "Cotiza la reposicion del cargador 20W", "error"),
        ("CONTROL - APROBACION", "Registra orden de cargador 20W", "approve"),
        ("CONTROL - RECHAZO", "Registra orden de cable C-L", "reject")
    ]:
        print("\n" + "=" * 22 + " " + title + " " + "=" * 22)
        from stockpilot.tools import FailingCurrency
        agent = create_agent(orders_file=dest)
        if answer == "error":
            agent.currency = FailingCurrency()
        r = agent.run(text, thread_id=title.replace(" ", "-"))
        show(r)
        if answer in ("approve", "reject"):
            print("\n[OPERADOR EXTERNO] DECISION:", answer)
            show(agent.resume(r["thread_id"], answer))


def interactive(live=False):
    agent = create_agent("real" if live else "simulado")
    print("StockPilot: modo", "API REAL" if live else "CAMBIO SIMULADO")
    print("Ejemplo: 'Cotiza reposicion del cargador 20W' o 'Registra orden cable C-L'.")
    while True:
        prompt = input("\nSolicitud (salir para terminar): ").strip()
        if prompt.lower() in ("salir", "exit"):
            break
        result = agent.run(prompt)
        show(result)
        if result["estado"] == "PENDIENTE_APROBACION_HUMANA":
            decision = input("[SUPERVISOR] approve / reject (otra opcion = sin ejecutar): ").strip().lower()
            show(agent.resume(result["thread_id"], decision))


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true", help="Casos visibles sin Internet")
    g.add_argument("--eval", action="store_true", help="Evaluacion 5 casos reales del orquestador")
    g.add_argument("--interactive", action="store_true", help="Operador aprueba/rechaza")
    g.add_argument("--live-api", action="store_true", help="Solicita API publica en tiempo real")
    g.add_argument("--llm", action="store_true", help="Modo OpenAI+LangChain HITL real, opcional")
    a = p.parse_args()
    if a.demo:
        demo()
    elif a.eval:
        from evaluacion.ejecutar_evaluacion import main as eval_main
        eval_main()
    elif a.llm:
        from stockpilot.langchain_agent import run_llm_interactive
        run_llm_interactive(ROOT / "data/inventario_simulado.json", ROOT / "salidas/ordenes_llm.jsonl")
    else:
        interactive(live=a.live_api)


if __name__ == "__main__":
    main()
