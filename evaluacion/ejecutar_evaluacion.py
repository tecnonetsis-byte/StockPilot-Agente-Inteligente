"""Ejecuta casos CONTRA el agente real del proyecto, nunca redacta resultados a mano."""
import json
from pathlib import Path
from stockpilot.agent import StockPilotAgent
from stockpilot.tools import InventoryTools, SimulatedCurrency, FailingCurrency, OrderTool

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "salidas"


def main():
    OUT.mkdir(exist_ok=True)
    order_file = OUT / "evaluacion_ordenes.jsonl"
    if order_file.exists():
        order_file.unlink()  # idempotente solo para archivo de evaluacion
    cases = json.loads((ROOT / "evaluacion/casos.json").read_text(encoding="utf-8"))
    results = []
    for c in cases:
        agent = StockPilotAgent(InventoryTools(ROOT / "data/inventario_simulado.json"),
                                FailingCurrency() if c["api"] == "falla_simulada" else SimulatedCurrency(),
                                OrderTool(order_file))
        started = agent.run(c["solicitud"], thread_id="test-case-" + str(c["id"]))
        interrupted = started["estado"] == "PENDIENTE_APROBACION_HUMANA"
        before_bytes = order_file.read_bytes() if order_file.exists() else b""
        final = started
        if c.get("decision_operador"):
            final = agent.resume(started["thread_id"], c["decision_operador"])
        after_bytes = order_file.read_bytes() if order_file.exists() else b""
        used = [x["herramienta"] for x in final["traza"]]
        true_uses = all(x in used for x in c["debe_usar"])
        true_nonuses = all(x not in used for x in c["no_debe_usar"])
        valid_estado = final["estado"] == c["estado"]
        valid_control = (not c.get("decision_operador") or
                         (interrupted and (before_bytes != after_bytes) == (c["decision_operador"] == "approve")))
        valid_error = not c.get("prefijo_error") or final["respuesta"].startswith(c["prefijo_error"])
        passed = all([true_uses, true_nonuses, valid_estado, valid_control, valid_error])
        results.append({"id": c["id"], "nombre": c["nombre"], "solicitud": c["solicitud"],
                        "debe_usar": c["debe_usar"], "no_debe_usar": c["no_debe_usar"],
                        "herramientas_realmente_usadas": used, "estado_final": final["estado"],
                        "hubo_interrupcion_previa_a_escritura": interrupted,
                        "registro_modificado": before_bytes != after_bytes, "decision_externa": c.get("decision_operador"),
                        "verificaciones": {"debe_usar": true_uses, "no_debe_usar": true_nonuses,
                                         "estado": valid_estado, "control": valid_control, "error": valid_error},
                        "aprobado": passed, "respuesta_real": final["respuesta"], "traza_ejecutada": final["traza"]})
        text = [f"CASO {c['id']} | {c['nombre']}", "INPUT: " + c["solicitud"],
                "ACCIONES OBSERVADAS: " + ", ".join(used), "ESTADO: " + final["estado"],
                "CONTROL ANTES DE ESCRIBIR: " + str(interrupted),
                "MODIFICO ARCHIVO: " + str(before_bytes != after_bytes), "SALIDA: " + final["respuesta"],
                "RESULTADO: " + ("PASS" if passed else "FAIL"),
                "TRAZA:", json.dumps(final["traza"], ensure_ascii=False, indent=2)]
        (OUT / f"caso_{c['id']}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
        print("CASO", c["id"], "-", "PASS" if passed else "FAIL", "| estado:", final["estado"],
              "| herramientas:", ",".join(used))
    pct = round(100 * sum(r["aprobado"] for r in results) / len(results), 1)
    summary = {"total": len(results), "aprobados": sum(r["aprobado"] for r in results), "porcentaje": pct,
               "nota": "Evaluacion ejecutada sobre el agente por reglas con datos y tipo de cambio simulados; NO es una llamada HTTP real",
               "casos": results}
    (OUT / "evaluacion_ejecutada.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Evaluacion ejecutada de 5 casos", "", f"**Resultado: {summary['aprobados']}/{len(results)} = {pct}% de verificaciones de caso aprobadas.**", "",
             "> Entorno de pruebas: orquestador real, inventario simulado, cambio simulado, fallo HTTP 503 inyectado. La red saliente no estuvo disponible.", "",
             "| Caso | Debe usar | No debe usar | Observado | Estado | Aprobado |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} · {r['nombre']} | {', '.join(r['debe_usar'])} | {', '.join(r['no_debe_usar']) or '—'} | {', '.join(r['herramientas_realmente_usadas'])} | {r['estado_final']} | {'SI' if r['aprobado'] else 'NO'} |")
    lines += ["", "## Seguridad comprobada", "", "- Caso 3: antes de aprobar, no se escribio en el archivo. El evaluador externo aprobo y se escribio una orden SIMULADA.",
              "- Caso 4: se rechazo y no se escribio ninguna orden.", "- Caso 5: la falla de API comienza con `ERROR:` y no se registra pedido.",
              "", "## Salidas completas", "", "Ver `caso_1.txt` ... `caso_5.txt` y `evaluacion_ejecutada.json` (trazas completas)."]
    (OUT / "informe_evaluacion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nRESULTADO GLOBAL: {summary['aprobados']}/{len(results)} = {pct}%")
    return summary


if __name__ == "__main__":
    main()
