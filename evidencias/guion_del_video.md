# Guion del video demostrativo StockPilot

Contenido: presentacion SIN AUDIO con visualizaciones de trazas y mensajes extraidos de ejecuciones comprobadas de `python main.py --demo`, `python main.py --eval` y `python -m unittest discover`. No es screencast nativo; cada captura de salida representada en el video es trazable al repositorio.

1. Inicio: problema real del comercio minorista, datos simulados y alcance educativo.
2. Arquitectura y rutas segun intencion.
3. Herramientas, API publica y control de fallos.
4. Formula de reposicion y fuente de calculos.
5. Caso normal: consulta y cotizacion sin registro.
6. Caso de error: API 503 simulada; resultado `ERROR:` sin registrar.
7. Caso de control: la orden se pausa, sin escritura antes de aprobar.
8. Aprobacion externa: se registra una orden simulada, no una compra real.
9. Rechazo externo: nunca ejecuta la herramienta de escritura.
10. Evaluacion ejecutada: 5/5 casos y 10/10 tests; limitaciones y pasos de entrega.

**Para reemplazar este video por una grabacion de pantalla directa:** abrir terminal en carpeta del proyecto, correr `python main.py --demo`, `python main.py --eval`, mostrar README/diagrama; grabar 3-5 minutos y subirlo a Drive, YouTube no listado o Loom. Asi se puede mostrar tambien una prueba `--live-api` desde su propia conexion.
