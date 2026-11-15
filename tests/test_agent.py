import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import requests
from stockpilot.agent import StockPilotAgent
from stockpilot.tools import InventoryTools, SimulatedCurrency, FailingCurrency, OrderTool, CurrencyAPI

ROOT = Path(__file__).resolve().parents[1]


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.order_file = Path(self.temp.name) / "ordenes.jsonl"
        self.agent = StockPilotAgent(InventoryTools(ROOT / "data/inventario_simulado.json"), SimulatedCurrency(), OrderTool(self.order_file))

    def tearDown(self):
        self.temp.cleanup()

    def test_stock_only_no_api(self):
        r = self.agent.run("Cuantos cargadores 20W quedan?")
        self.assertEqual([x["herramienta"] for x in r["traza"]], ["consultar_inventario"])

    def test_cotizacion(self):
        r = self.agent.run("Analiza reposicion del cable C-L")
        self.assertEqual(r["estado"], "finalizado")
        self.assertIn("consultar_tipo_cambio_publico", [x["herramienta"] for x in r["traza"]])

    def test_control_approves_only_after_pause(self):
        before = self.agent.run("Registra orden C20W", "tid-approving")
        self.assertEqual(before["estado"], "PENDIENTE_APROBACION_HUMANA")
        self.assertFalse(self.order_file.exists())
        after = self.agent.resume("tid-approving", "approve")
        self.assertEqual(after["estado"], "APROBADO_Y_REGISTRADO_SIMULADO")
        self.assertEqual(len(self.order_file.read_text().splitlines()), 1)

    def test_rejection_no_order(self):
        self.agent.run("Registra orden CBLC", "tid-reject")
        r = self.agent.resume("tid-reject", "reject")
        self.assertEqual(r["estado"], "RECHAZADO_POR_HUMANO")
        self.assertFalse(self.order_file.exists())

    def test_api_error_prefix_and_no_order(self):
        self.agent.currency = FailingCurrency()
        r = self.agent.run("Cotiza reposicion C40W")
        self.assertEqual(r["estado"], "error_api")
        self.assertTrue(r["respuesta"].startswith("ERROR:"))
        self.assertFalse(self.order_file.exists())

    def test_no_reorder_if_stock_sufficient(self):
        r = self.agent.run("Registra orden CBCC")
        self.assertEqual(r["estado"], "finalizado")
        self.assertEqual([x["herramienta"] for x in r["traza"]], ["consultar_inventario", "calcular_reposicion"])
        self.assertFalse(self.order_file.exists())

    def test_api_timeout_error(self):
        s = Mock()
        s.get.side_effect = requests.exceptions.Timeout("simulado")
        self.assertTrue(CurrencyAPI(s).consultar_usd_bob().startswith("ERROR:"))

    def test_api_response_parsing_with_mock_http(self):
        s = Mock()
        s.get.return_value.json.return_value = {"result": "success", "base_code": "USD", "rates": {"BOB": 11.8}, "time_last_update_utc": "simulado"}
        s.get.return_value.raise_for_status.return_value = None
        r = CurrencyAPI(s).consultar_usd_bob()
        self.assertEqual(r["modo"], "API_REAL")  # La etiqueta indica metodo HTTP; respuesta HTTP simulada por Mock
        self.assertEqual(r["usd_bob"], 11.8)
        s.get.assert_called_once()

    def test_invalid_approval_cannot_write(self):
        self.agent.run("Registra orden CBLC", "tid-invalid")
        r = self.agent.resume("tid-invalid", "sure")
        self.assertEqual(r["estado"], "PENDIENTE_APROBACION_HUMANA")
        self.assertFalse(self.order_file.exists())

    def test_unknown_request_no_tool(self):
        r = self.agent.run("Buenos dias")
        self.assertEqual(r["estado"], "sin_herramientas")
        self.assertEqual(r["traza"], [])


if __name__ == "__main__":
    unittest.main()
