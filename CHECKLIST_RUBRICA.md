# Control de calidad frente al enunciado

| Criterio | Archivo o comando | Verificacion |
|---|---|---|
| Agente de inicio a fin, salidas visibles (30 pts) | `main.py --demo`, `salidas/demo_terminal_completa.txt` | **EJECUTADO** en modo orquestador por reglas |
| README + problema, usuario, arquitectura y 5 primitivos (20 pts) | `README.md`, `evidencias/arquitectura_stockpilot.png` | **COMPLETO** |
| Al menos 2 herramientas; 1 consulta API real; errores `ERROR:` (15 pts) | `stockpilot/tools.py`, `main.py --live-api`, `salidas/intento_api_real_sin_red.txt` | **CODIGO HTTP REAL IMPLEMENTADO; CONEXION EN VIVO NO VERIFICADA POR AUSENCIA DE RED**; manejo de errores probado |
| Control con `HumanInTheLoopMiddleware` o limite de llamadas (15 pts) | `stockpilot/agent.py`, `stockpilot/langchain_agent.py`, `salidas/caso_3.txt`, `caso_4.txt` | **PAUSA/APROBACION/RECHAZO EJECUTADOS EN MOTOR POR REGLAS; MIDDLEWARE LANGCHAIN ES OPCIONAL Y NO EJECUTADO AQUI** |
| 5 casos debe_usar/no_debe_usar y porcentaje (10 pts) | `evaluacion/casos.json`, `salidas/evaluacion_ejecutada.json` | **EJECUTADO: 5/5 PASS = 100% DE CRITERIOS DE CASO** |
| Video de 3 a 5 minutos, normal+error+control (10 pts) | `evidencias/video_demostracion_stockpilot.mp4` | **ARCHIVO CREADO, 4 min 36 s, video sin audio basado en resultados ejecutados; falta enlace externo** |
| Repositorio GitHub o Colab visible | carpeta ZIP lista para GitHub | **PENDIENTE PUBLICAR POR EL USUARIO / CONECTAR GITHUB** |

**Para maximizar cumplimiento antes de entregar:** 1) publicarlo en GitHub; 2) correr `python main.py --live-api` en computadora con Internet y adjuntar la salida; 3) instalar las dependencias opcionales y comprobar `python main.py --llm` con una clave propia y protegida, si el docente requiere que el middleware exacto se ejecute; 4) subir el MP4 y pegar enlace compartible. No afirmar que esos cuatro pasos estan completados sin haberlos efectuado.
