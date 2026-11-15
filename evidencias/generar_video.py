"""Genera una presentacion de 3-5 min a partir de las trazas ejecutadas.
No simula pantalla en vivo: escenas son graficas de salidas verificadas.
"""
from pathlib import Path
import json
import math
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidencias"
TMP = OUT / "_frames_temporales"
TMP.mkdir(exist_ok=True)
SUMMARY = json.loads((ROOT / 'salidas/evaluacion_ejecutada.json').read_text(encoding='utf-8'))
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

def f(size=24,bold=False,mono=False):
    return ImageFont.truetype(MONO if mono else BOLD if bold else SANS, size)

NAVY = '#081528'
DARK = '#0e2034'
PANEL = '#152b43'
TINT = '#a4bfd1'
WHITE = '#f7fafc'
CYAN = '#51d9ea'
GREEN = '#7de0b5'
RED = '#ff968e'
AMBER = '#ffda85'

def round_rect(draw, xy, fill, rad=18, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=rad, fill=fill, outline=outline, width=width)

def lines(draw, text, x, y, font, color, max_width, spacing=12):
    words = str(text).split()
    ls=[]; cur=''
    for w in words:
        nxt = (cur+' '+w).strip()
        if draw.textbbox((0,0), nxt, font=font)[2] > max_width and cur:
            ls.append(cur);cur=w
        else:cur=nxt
    if cur:ls.append(cur)
    for line in ls:
        draw.text((x,y),line,font=font,fill=color);y+=font.size+spacing
    return y

def slide(title,kicker,blocks,index,total,duration,accent=CYAN):
    im=Image.new('RGB',(1280,720),NAVY);d=ImageDraw.Draw(im)
    d.rectangle((0,0,1280,10),fill=accent)
    d.text((64,37),'STOCKPILOT   /   ALKOSTO PLUS',font=f(19,True),fill=CYAN)
    d.text((1130,36),f'{index:02}/{total:02}',font=f(20,True),fill=TINT)
    d.text((64,98),title,font=f(40,True),fill=WHITE)
    d.text((66,159),kicker,font=f(19),fill=TINT)
    n=len(blocks)
    h=math.floor((465-(n-1)*16)/n)
    for i,b in enumerate(blocks):
        x1=64;y1=211+i*(h+16)
        x2=1216;y2=y1+h
        round_rect(d,(x1,y1,x2,y2),PANEL,rad=18)
        if b.get('tag'):
            d.text((x1+23,y1+20),b['tag'],font=f(17,True),fill=b.get('accent',accent));offset=54
        else:offset=27
        bs=b.get('size',27)
        lines(d,b['text'],x1+23,y1+offset,f(bs,mono=b.get('mono',False)),b.get('color',WHITE),1080,spacing=9)
    d.rectangle((0,702,int(1280*index/total),720),fill=accent)
    d.text((66,675),f'DEMOSTRACION DOCUMENTADA · {duration}s · DATOS DE NEGOCIO SIMULADOS',font=f(13),fill=TINT)
    return im

# Diagrama SVG-like construido con PIL usando la misma arquitectura del README.
def diagram():
    im=Image.new('RGB',(1600,900),'#f5f9fc');d=ImageDraw.Draw(im)
    d.text((64,38),'ARQUITECTURA · STOCKPILOT AI',font=f(43,True),fill='#0e2034')
    d.text((65,98),'Orquestacion observacional, herramientas y aprobacion humana',font=f(24),fill='#52677a')
    boxes=[
       ('Usuario / solicitud', (60,195,340,285),'#d4eafa'),
       ('Planificador y estado', (415,195,765,285),'#d4eafa'),
       ('Inventario JSON', (60,375,345,465),'#e5f1f9'),
       ('Calculo reposicion', (420,375,745,465),'#e5f1f9'),
       ('API publica USD/BOB', (820,375,1185,465),'#cceef0'),
       ('ERROR: detener', (1230,375,1540,465),'#fce0df'),
       ('Respuesta sin escritura', (55,615,405,725),'#def5e5'),
       ('APROBACION HUMANA', (500,615,920,725),'#fff0cb'),
       ('Orden simulada JSONL', (1040,615,1540,725),'#d7f0e1')
    ]
    for label,coords,fill in boxes:
        d.rounded_rectangle(coords,20,fill=fill,outline='#7e9bad',width=3)
        width=d.textbbox((0,0),label,font=f(24,True))[2]
        mid=(coords[0]+coords[2])/2
        d.text((mid-width/2,(coords[1]+coords[3])/2-16),label,font=f(24,True),fill=NAVY)
    def arrow(start,end,label=None,col='#3a718b'):
        d.line((start,end),fill=col,width=5,joint='curve')
        ang=math.atan2(end[1]-start[1],end[0]-start[0]);off=15
        tri=[end,(end[0]-off*math.cos(ang-.45),end[1]-off*math.sin(ang-.45)),(end[0]-off*math.cos(ang+.45),end[1]-off*math.sin(ang+.45))]
        d.polygon(tri,fill=col)
        if label:d.text((start[0]+10,start[1]+8),label,font=f(18),fill=col)
    arrow((340,240),(415,240))
    arrow((505,285),(195,375))
    arrow((345,425),(420,425))
    arrow((745,425),(820,425))
    arrow((1185,425),(1230,425),'error')
    arrow((595,465),(595,615),'registrar')
    arrow((920,665),(1040,665),'approve')
    arrow((500,665),(405,665))
    arrow((214,465),(214,615),'solo stock')
    d.text((75,807),'Control: en modo probado, pausa interna externa al agente; en modo LLM, HumanInTheLoopMiddleware.',font=f(19),fill='#334b5e')
    d.text((75,846),'Datos comerciales simulados · La API HTTPS real requiere conexion a Internet · No se crean compras reales',font=f(17),fill='#506b82')
    im.save(OUT/'arquitectura_stockpilot.png',quality=95)


diagram()
# Cada escena se sustenta en outputs guardados bajo salidas/.
slides = [
('Presentacion del agente','EVALUACION FINAL · ARQUITECTURA Y HERRAMIENTAS',[
 {'tag':'OBJETIVO','text':'Reducir errores de reposicion de accesorios tecnologicos de ALKOSTO PLUS.'},
 {'tag':'ALCANCE','text':'Inventario, costos y tasas del demo: SIMULADOS. Las ordenes son registros educativos.'}],
 'Presento StockPilot, un agente para sugerir reposiciones de accesorios tecnologicos. El problema se inspira en la gestion de inventario de ALKOSTO PLUS. Para respetar la privacidad, todos los movimientos, productos, ventas y costos del proyecto son simulados. No se compran productos reales.',19),
('Por que un agente','LAS ACCIONES CAMBIAN SEGUN CADA SOLICITUD',[
 {'tag':'PETICION 1','text':'Stock solamente  >  lee inventario  >  responde.'},
 {'tag':'PETICION 2','text':'Cotizacion  >  inventario  >  calculo  >  tipo de cambio.'},
 {'tag':'PETICION 3','text':'Registro  >  calculo  >  PAUSA  >  aprobacion humana.'}],
 'No es una cadena de operaciones unica. El agente selecciona herramientas dependiendo de la intencion y de los datos. Si hay stock suficiente, evita una compra. Si hay error externo, se detiene. Y si se propone una orden, exige autorizacion humana.',22),
('Los cinco primitivos','INSTRUCCIONES · HERRAMIENTAS · MEMORIA · ESTADO · CONTROL',[
 {'tag':'INSTRUCCIONES Y HERRAMIENTAS','text':'Planificar, consultar, calcular, verificar errores y registrar solo si hay permiso.'},
 {'tag':'MEMORIA Y ESTADO','text':'Inventario JSON, estados pendientes por hilo y trazas visibles de cada accion.'},
 {'tag':'CONTROL','text':'Interrupcion ANTES de escribir; aprobacion o rechazo externo al agente.'}],
 'Los cinco primitivos estan documentados en el README. Las instrucciones definen limites de seguridad. Las herramientas consultan y calculan. La memoria conserva inventario y solicitudes pendientes. El estado explica el progreso, y el control evita escrituras sin permiso. La version LLM incluye adaptador al middleware oficial de LangChain.',24),
('Herramientas y API publica','CUATRO HERRAMIENTAS: DOS LOCALES, UNA HTTP, UNA DE ESCRITURA',[
 {'tag':'FUNCIONES UTILIZADAS','text':'consultar_inventario  |  calcular_reposicion'},
 {'tag':'API PUBLICA REAL IMPLEMENTADA','text':'GET https://open.er-api.com/v6/latest/USD','size':23,'mono':True},
 {'tag':'ACCION PROTEGIDA','text':'registrar_orden_reposicion  |  archivo JSONL simulado'}],
 'El codigo contiene cuatro herramientas. La tercera realiza una llamada HTTPS al proveedor publico Exchange Rate API sin credenciales. Valida los campos y convierte los errores en mensajes que empiezan por ERROR. En este entorno no hay Internet, por eso la demostracion muestra una cotizacion artificial, no una consulta remota exitosa.',25),
('Calculo reproducible','REPOSICION BASADA EN CONSUMO DE CATORCE DIAS',[
 {'tag':'FORMULA','text':'max(0, ceil(ventas_14 / 14 × 21) − stock_actual)','size':28},
 {'tag':'EJEMPLO · CARGADOR 20 W','text':'42 / 14 × 21 = 63 objetivo; 63 − 8 = 55 unidades.'},
 {'tag':'COSTO SIMULADO','text':'55 × USD 5.50 = USD 302.50 · tasa del demo: 11.70'}],
 'El agente calcula un objetivo equivalente a veintiun dias de ventas. Por ejemplo, para el cargador de veinte watts, cuarenta y dos ventas en catorce dias equivalen a tres ventas diarias. El objetivo es sesenta y tres unidades, menos ocho actuales, por lo que sugiere cincuenta y cinco unidades. Todos los datos son simulados.',24),
('Caso normal · EJECUTADO','COTIZACION DEL CABLE C-L: SIN REGISTRO',[
 {'tag':'INPUT REAL DEL TEST','text':'Analiza reposicion del cable C-L'},
 {'tag':'HERRAMIENTAS OBSERVADAS','text':'inventario  →  reposicion  →  tipo de cambio'},
 {'tag':'SALIDA DEL AGENTE','text':SUMMARY['casos'][1]['respuesta_real'],'size':25}],
 'En el segundo caso real de pruebas, el usuario solicita analizar la reposicion del cable C a Lightning. La traza muestra tres herramientas ejecutadas. El agente calcula cantidades y costo estimado, pero no registra ninguna orden porque no lo pidieron. La cifra cambiaria mostrada es una tasa artificial para pruebas.',23),
('Caso de error · EJECUTADO','UN FALLO DE API NO CREA ORDEN NI INVENTA VALORES',[
 {'tag':'ENTRADA','text':'Cotiza reposicion de cargador 40W'},
 {'tag':'FALLO INYECTADO','text':'ERROR: HTTP 503 simulado; proveedor temporalmente no disponible','color':RED},
 {'tag':'RESPUESTA OBSERVADA','text':'Estado = error_api  |  Sin registro de pedido  |  PASS'}],
 'En el quinto caso, la herramienta recibe un error de servicio de tipo quinientos tres, inyectado deliberadamente. El agente devuelve un mensaje que comienza con ERROR y no inventa una cotizacion alternativa. La prueba comprobo que no se registro ninguna orden. El error fue simulado, no provocado en la API del proveedor.',21),
('Control · ANTES de aprobar','NO SE ESCRIBE NI UNA LINEA HASTA RECIBIR PERMISO',[
 {'tag':'PETICION','text':'Registra orden de cargador 20W'},
 {'tag':'ESTADO DESPUES DE CALCULAR','text':'PENDIENTE_APROBACION_HUMANA','color':AMBER},
 {'tag':'COMPROBACION','text':'Archivo SIN modificar · Herramienta de registro NO ejecutada'}],
 'Ahora el caso mas importante. El usuario pide registrar una orden. Primero se calculan cantidades y costos. Inmediatamente el agente queda en estado pendiente de aprobacion humana. En ese instante se verifico que el archivo no habia sido modificado y que la herramienta irreversible seguia sin ejecutarse.',24),
('Control · APROBAR','DECISION EXTERNA DEL SUPERVISOR: approve',[
 {'tag':'DECISION EXTERNA','text':'approve  →  se reanuda el mismo hilo','color':GREEN},
 {'tag':'ESTADO OBSERVADO','text':'APROBADO_Y_REGISTRADO_SIMULADO'},
 {'tag':'EVIDENCIA','text':'El archivo JSONL cambia SOLO DESPUES de approve. Caso 3: PASS'}],
 'En el tercer caso, el evaluador externo envia la palabra approve una vez que el agente ya esta pausado. Solo entonces se ejecuta registrar orden. La prueba compara el archivo antes y despues y observa una escritura. El registro es academico y no genera una compra real a proveedores.',22),
('Control · RECHAZAR','DECISION EXTERNA DEL SUPERVISOR: reject',[
 {'tag':'DECISION EXTERNA','text':'reject  →  fin de ejecucion; herramienta bloqueada','color':RED},
 {'tag':'ESTADO OBSERVADO','text':'RECHAZADO_POR_HUMANO'},
 {'tag':'EVIDENCIA','text':'El archivo JSONL no cambia. Caso 4: PASS'}],
 'En el cuarto caso, se ejecuta la misma secuencia de analisis, pero el supervisor rechaza el registro. El agente finaliza sin utilizar la herramienta de escritura. La evaluacion demuestra que el control no consiste en mostrar un mensaje decorativo: realmente evita la accion protegida.',21),
('Evaluacion ejecutada','5 CASOS · 10 PRUEBAS UNITARIAS · TRAZAS GUARDADAS',[
 {'tag':'EVALUACION REAL DEL ORQUESTADOR','text':f"{SUMMARY['aprobados']} / {SUMMARY['total']} = {SUMMARY['porcentaje']:.0f}% casos PASS",'color':GREEN,'size':36},
 {'tag':'PRUEBAS UNITARIAS','text':'10 / 10 superadas, incluidos rechazo, timeout y permisos invalidos.'},
 {'tag':'EVIDENCIAS','text':'salidas/evaluacion_ejecutada.json · salidas/caso_1.txt ... caso_5.txt','size':21}],
 'Finalmente se ejecutaron cinco casos sobre el agente, con herramientas que debe usar y no debe usar. Los cinco cumplieron sus criterios y las diez pruebas unitarias pasaron. La puntuacion de cien por ciento corresponde a estas pruebas, no a la rubrica. El repositorio incluye trazas reales y README detallado.',23),
('Entrega y limitaciones','CODIGO · README · SALIDAS · VIDEO',[
 {'tag':'PARA PRESENTAR','text':'Publicar repositorio en GitHub y subir el MP4 a Drive, YouTube no listado o Loom.'},
 {'tag':'VERIFICACIONES PENDIENTES DEL ALUMNO','text':'Ejecutar --live-api con Internet y --llm si desea demostrar middleware LangChain.'},
 {'tag':'ALCANCE REAL','text':'El video reconstruye los resultados obtenidos; no es una captura en vivo de escritorio.'}],
 'Para terminar, el archivo comprimido contiene codigo, datos simulados, README, diagrama, pruebas, resultados y este video. Antes de entregar, publique el repositorio y el video para obtener enlaces compartibles. La llamada HTTPS en vivo y la ejecucion del adaptador LangChain requieren un entorno conectado y deben verificarse por separado.',23)
]

frames=[]; audio_blocks=[]; sample_rate=22050
for i,(title,kicker,blocks,narration,duration) in enumerate(slides,1):
    path=TMP/f'scene_{i:02}.png'
    slide(title,kicker,blocks,i,len(slides),duration,accent=RED if 'error' in title.lower() or 'RECHAZAR' in title else GREEN if 'Evaluacion' in title or 'APROBAR' in title else CYAN).save(path)
    wav=TMP/f'voice_{i:02}.wav'
    subprocess.run(['espeak','-v','es-la','-s','173','-a','145','--stdout',narration],stdout=wav.open('wb'),check=True)
    with wave.open(str(wav),'rb') as w:
        rate=w.getframerate();num=w.getnframes();data=np.frombuffer(w.readframes(num),dtype='<i2')
    if rate != sample_rate:
        from scipy.signal import resample_poly
        from math import gcd
        g=gcd(rate,sample_rate)
        data=resample_poly(data,sample_rate//g,rate//g).astype(np.int16)
    duration=max(duration,math.ceil(len(data)/sample_rate)+1)
    frame_count=int(duration*sample_rate)
    sound=np.zeros(frame_count,dtype=np.int16)
    use=min(len(data),frame_count)
    sound[:use]=data[:use]
    audio_blocks.append(sound)
    frames.append((path,duration))

with wave.open(str(TMP/'full_narration.wav'),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sample_rate)
    w.writeframes(np.concatenate(audio_blocks).astype('<i2').tobytes())
with (TMP/'slides_concat.txt').open('w') as fout:
    for path,dur in frames:
        fout.write(f"file '{path}'\n")
        fout.write(f"duration {dur}\n")
    fout.write(f"file '{frames[-1][0]}'\n")

cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(TMP/'slides_concat.txt'),'-i',str(TMP/'full_narration.wav'),'-r','6','-c:v','libx264','-preset','ultrafast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-t',str(sum(x[1] for x in frames)),'-shortest',str(OUT/'video_demostracion_stockpilot.mp4')]
print('Rendering video',sum(x[1] for x in frames),'seconds...')
subprocess.run(cmd,check=True)
print('Produced',OUT/'video_demostracion_stockpilot.mp4')
