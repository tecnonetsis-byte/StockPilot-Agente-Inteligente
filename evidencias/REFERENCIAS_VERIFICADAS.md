# Fuentes consultadas el 15-11-2026

- API de tipos de cambio: `https://www.exchangerate-api.com/docs/free`. Documenta `GET https://open.er-api.com/v6/latest/USD`, acceso sin clave, limite de llamadas, atribucion requerida y errores.
- Endpoint JSON consultable por navegador web: `https://open.er-api.com/v6/latest/USD`. Verificado desde acceso web externo; la ejecucion de Python estuvo bloqueada por fallo de resolucion DNS. No se almacenan ni redistribuyen las cotizaciones del proveedor.
- Documentacion de middleware HITL de LangChain: `https://docs.langchain.com/oss/python/langchain/human-in-the-loop`. Explica `HumanInTheLoopMiddleware`, `interrupt_on`, checkpoint y `Command(resume=...)`.

**Diferencias de evidencia:** consulta por navegador web = acceso del analista al endpoint; intento HTTP desde Python = fallo con prefijo `ERROR:`; tests con mocks = ejecucion local sin Internet; demo con tasa simulada = demostracion reproductible. No son lo mismo.
