# Evaluacion ejecutada de 5 casos

**Resultado: 5/5 = 100.0% de verificaciones de caso aprobadas.**

> Entorno de pruebas: orquestador real, inventario simulado, cambio simulado, fallo HTTP 503 inyectado. La red saliente no estuvo disponible.

| Caso | Debe usar | No debe usar | Observado | Estado | Aprobado |
|---|---|---|---|---|---|
| 1 · Consulta simple sin API | consultar_inventario | calcular_reposicion, consultar_tipo_cambio_publico, registrar_orden_reposicion | consultar_inventario | finalizado | SI |
| 2 · Cotizacion inteligente | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico | registrar_orden_reposicion | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico | finalizado | SI |
| 3 · Escritura aprobada externamente | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico, registrar_orden_reposicion | — | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico, registrar_orden_reposicion | APROBADO_Y_REGISTRADO_SIMULADO | SI |
| 4 · Escritura rechazada externamente | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico | registrar_orden_reposicion | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico, control_humano | RECHAZADO_POR_HUMANO | SI |
| 5 · Error de API 503 simulado | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico | registrar_orden_reposicion | consultar_inventario, calcular_reposicion, consultar_tipo_cambio_publico | error_api | SI |

## Seguridad comprobada

- Caso 3: antes de aprobar, no se escribio en el archivo. El evaluador externo aprobo y se escribio una orden SIMULADA.
- Caso 4: se rechazo y no se escribio ninguna orden.
- Caso 5: la falla de API comienza con `ERROR:` y no se registra pedido.

## Salidas completas

Ver `caso_1.txt` ... `caso_5.txt` y `evaluacion_ejecutada.json` (trazas completas).
