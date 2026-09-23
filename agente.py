from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai import LLM
from typing import Union
import requests
import json
import time
import os
import random
from dotenv import load_dotenv
import traceback


load_dotenv()
random.seed(42)  # Semilla fija para reproducibilidad del experimento


MODELOS_NVIDIA = {
    "deepseek-v4-flash": "deepseek-ai/deepseek-v4-flash-0731",
    "kimi-k3": "moonshotai/kimi-k3",
}

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

MODELOS_GROQ = {
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "qwen-27b": "qwen/qwen3.8-27b",
}
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


MODELOS_GEMINI = {
    "google-gemini": "gemini-3.6-flash",
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODELOS_OPENROUTER = {
    "nemotron-3-super": "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere-north-mini": "cohere/north-mini-code:free",
    "gemma4-31b": "google/gemma-4-31b-it:free",
    "gemma4-26b": "google/gemma-4-26b-a4b-it:free",  # ajustar con el nombre exacto que confirmes
}
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

TIMEOUT_SEGUNDOS = 180  # tiempo maximo de espera por llamada a un modelo
TEMPERATURA = 0.7              # igual para todos los modelos evaluados y el generador de relleno
TEMPERATURA_ORQUESTADOR = 0.0  # el orquestador solo copia parametros: sin aleatoriedad
NUM_CTX_OLLAMA = 8192          # provisional: se ajusta al definir los niveles de tokens


# ============================================================
# DISEÑO DE MODELOS
# ------------------------------------------------------------
# Modelos evaluados: uno por empresa distinta, para que las
# comparaciones no queden sesgadas por familia/arquitectura.
# El orquestador (cerebro del agente + generador de relleno)
# es de una CUARTA empresa, distinta a las tres evaluadas, para
# evitar sesgo de auto-preferencia del "juez" hacia modelos de
# su propia familia.
#
# Se agrega deepseek-v4-flash (NVIDIA API, cloud) como cuarto
# modelo evaluado para comparar retención local vs cloud.
# ============================================================

MODELOS_EVALUABLES = {
    "phi3:mini": "Microsoft",
    "gemma2:2b": "Google",
    "gemma3:4b": "Google",
    "llama3.2:3b": "Meta",
    "deepseek-v4-flash": "DeepSeek",
    "gpt-oss-20b": "OpenAI",
    "gpt-oss-120b": "OpenAI",
    "qwen-27b": "Alibaba",
    "google-gemini": "Google",
    "nemotron-3-super": "NVIDIA",
    "cohere-north-mini": "Cohere",
    "gemma4-31b": "Google",
    "gemma4-26b": "Google",
}

MODELO_CEREBRO = "ollama/qwen2.5:1.5b"        # Alibaba — orquestador del Agent de CrewAI
MODELO_GENERADOR_RELLENO = "qwen2.5:1.5b"     # Alibaba — genera los turnos de relleno de la conversación

llm = LLM(
    model=MODELO_CEREBRO,
    base_url="http://localhost:11434",
    temperature=TEMPERATURA_ORQUESTADOR
)

# ============================================================
# BANCO DE DATOS CLAVE (rotativo)
# ============================================================

DATOS_CLAVE = [
    {"dato": "el numero de expediente del caso Aurora es 3851",
     "pregunta": "Recuerdas el numero de expediente del caso Aurora?",
     "verificacion": "3851"},
    {"dato": "el codigo de referencia del proyecto Fenix es F-7492-X",
     "pregunta": "Recuerdas cual era el codigo de referencia del proyecto Fenix?",
     "verificacion": "7492"},
    {"dato": "el numero de registro del laboratorio Nexus es 6037",
     "pregunta": "Recuerdas el numero de registro del laboratorio Nexus?",
     "verificacion": "6037"},
    {"dato": "el resultado del experimento Delta-7 fue exactamente 44295",
     "pregunta": "Recuerdas cual fue el resultado exacto del experimento Delta-7?",
     "verificacion": "44295"},
    {"dato": "la version del algoritmo Centinela que se implemento fue la 9.15.6",
     "pregunta": "Recuerdas que version del algoritmo Centinela se implemento?",
     "verificacion": "9.15.6"},
]

def seleccionar_dato_clave():
    """Selecciona aleatoriamente un dato clave del banco rotativo."""
    return random.choice(DATOS_CLAVE)


def resolver_turno_dato(posicion, num_turnos):
    """Traduce la posicion (con sinonimos) al indice de turno donde se
    inserta el dato clave."""
    pos = posicion.strip().lower()
    if pos in ["inicio", "inicial", "principio", "comienzo"]:
        return 1
    elif pos in ["mitad", "medio", "media", "center", "centro"]:
        return num_turnos // 2
    elif pos in ["final", "fin", "ultimo", "end"]:
        return num_turnos - 2
    else:
        return num_turnos // 2


def _invalida(estado, codigo_http, tipo_error):
    """Diccionario estandar de una llamada que NO produjo respuesta utilizable."""
    return {"contenido": None, "tokens_prompt": 0, "tokens_respuesta": 0,
            "estado": estado, "codigo_http": codigo_http, "tipo_error": tipo_error}


def _valida(contenido, tokens_prompt, tokens_respuesta):
    """Diccionario estandar de una llamada exitosa."""
    return {"contenido": contenido, "tokens_prompt": tokens_prompt,
            "tokens_respuesta": tokens_respuesta, "estado": "valida",
            "codigo_http": 200, "tipo_error": None}


def _procesar_openai_compat(resp):
    """Interpreta la respuesta de APIs con formato OpenAI (NVIDIA, Groq, OpenRouter)."""
    if resp.status_code == 429:
        return _invalida("invalida_tecnica", 429, "rate_limit")
    if resp.status_code == 503:
        return _invalida("invalida_tecnica", 503, "sobrecarga")
    if resp.status_code != 200:
        return _invalida("invalida_tecnica", resp.status_code, "desconocido")

    data = resp.json()
    try:
        eleccion = data["choices"][0]
    except (KeyError, IndexError, TypeError):
        return _invalida("invalida_tecnica", 200, "respuesta_inesperada")

    mensaje = eleccion.get("message") or {}
    if eleccion.get("finish_reason") == "content_filter" or mensaje.get("refusal"):
        return _invalida("rechazo_seguridad", 200, "bloqueo_seguridad")

    contenido = mensaje.get("content")
    if contenido is None:
        return _invalida("invalida_tecnica", 200, "respuesta_inesperada")

    usage = data.get("usage", {})
    return _valida(contenido, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def _despachar_modelo(modelo, historial):
    """Decide si consultar Ollama (local) o NVIDIA API (cloud) o GROQ API (cloud) o GEMINI API (cloud) segun el modelo.
    Devuelve: contenido, tokens_prompt, tokens_respuesta"""
    if modelo in MODELOS_NVIDIA:
        resp = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={"model": MODELOS_NVIDIA[modelo], "messages": historial, "temperature": TEMPERATURA},
            timeout=TIMEOUT_SEGUNDOS
        )
        return _procesar_openai_compat(resp)
    elif modelo in MODELOS_GROQ:
        limite_tokens = 150 if "qwen" in modelo else 300
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": MODELOS_GROQ[modelo], "messages": historial,"max_tokens": limite_tokens, "temperature": TEMPERATURA},
            timeout=TIMEOUT_SEGUNDOS
        )
        return _procesar_openai_compat(resp)
    elif modelo in MODELOS_GEMINI:
        # Gemini usa "model" en vez de "assistant" como rol
        contenido_gemini = []
        for msg in historial:
            rol = "model" if msg["role"] == "assistant" else "user"
            contenido_gemini.append({
                "role": rol,
                "parts": [{"text": msg["content"]}]
            })
        
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODELOS_GEMINI[modelo]}:generateContent?key={GEMINI_API_KEY}",
            json={"contents": contenido_gemini, "generationConfig": {"temperature": TEMPERATURA}},
            timeout=TIMEOUT_SEGUNDOS
        )
        if resp.status_code == 429:
            return _invalida("invalida_tecnica", 429, "rate_limit")
        if resp.status_code == 503:
            return _invalida("invalida_tecnica", 503, "sobrecarga")
        if resp.status_code != 200:
            return _invalida("invalida_tecnica", resp.status_code, "desconocido")
        data = resp.json()

        # Gemini puede bloquear la respuesta por seguridad sin dar error HTTP
        finish_reason = data.get("candidates", [{}])[0].get("finishReason", "")
        if finish_reason == "SAFETY":
            return _invalida("rechazo_seguridad", 200, "bloqueo_seguridad")

        try:
            contenido = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return _invalida("invalida_tecnica", 200, "respuesta_inesperada")
        usage = data.get("usageMetadata", {})
        tokens_prompt = usage.get("promptTokenCount", 0)
        tokens_respuesta = usage.get("candidatesTokenCount", 0)
        return _valida(contenido, tokens_prompt, tokens_respuesta)
    elif modelo in MODELOS_OPENROUTER:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": MODELOS_OPENROUTER[modelo], "messages": historial, "temperature": TEMPERATURA},
            timeout=TIMEOUT_SEGUNDOS
        )
        return _procesar_openai_compat(resp)
    else:
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": modelo, "messages": historial, "stream": False,"options": {"temperature": TEMPERATURA, "num_ctx": NUM_CTX_OLLAMA}},
            timeout=TIMEOUT_SEGUNDOS
        )
        if resp.status_code != 200:
            return _invalida("invalida_tecnica", resp.status_code, "desconocido")
        data = resp.json()
        contenido = data.get("message", {}).get("content", "Sin respuesta")
        tokens_prompt = data.get("prompt_eval_count", 0)
        tokens_respuesta = data.get("eval_count", 0)
        return _valida(contenido, tokens_prompt, tokens_respuesta)

def consultar_modelo(modelo, historial):
    """Punto de entrada unico para consultar un modelo. Nunca lanza excepciones
    de red: las convierte en una corrida invalida con su tipo de error."""
    try:
        return _despachar_modelo(modelo, historial)
    except requests.exceptions.Timeout:
        return _invalida("invalida_tecnica", None, "timeout")
    except requests.exceptions.ConnectionError:
        return _invalida("invalida_tecnica", None, "conexion")
    except ValueError:
        return _invalida("invalida_tecnica", 200, "respuesta_inesperada")
    except requests.exceptions.RequestException:
        return _invalida("invalida_tecnica", None, "error_red")

def generar_nombre_archivo(modelo, posicion, turnos):
    """Genera un nombre unico basado en modelo, posicion, turnos y replica."""
    modelo_limpio = modelo.replace(":", "_").replace(".", "_")
    base = f"{modelo_limpio}_{posicion}_{turnos}turnos"
    replica = 1
    while os.path.exists(f"resultados/txt/{base}_{replica:02d}.txt"):
        replica += 1
    return f"{base}_{replica:02d}"

def _generar_relleno(historial):
    """Pide al modelo generador (local) el siguiente mensaje del 'usuario'.
    Devuelve el texto, o None si el generador fallo."""
    prompt_generar = (
        "Eres una persona curiosa que disfruta conversar sobre "
        "cualquier tema. Responde de forma natural a lo que te "
        "acaban de decir: puedes opinar, compartir algo que sabes, "
        "hacer una pregunta sobre un detalle especifico que "
        "mencionaron, contar algo relacionado, o llevar la "
        "conversacion hacia otro tema que te interese. "
        "Habla como en una conversacion real entre amigos. "
        "Escribe 2 a 4 oraciones. No seas repetitivo ni uses "
        "frases como 'eso suena interesante' o 'cuentame mas'. "
        "Responde en español. "
        f"El asistente acaba de decir: {historial[-1]['content'][:500]}"
    )
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODELO_GENERADOR_RELLENO, "prompt": prompt_generar, "stream": False,
                  "options": {"temperature": TEMPERATURA}},
            timeout=TIMEOUT_SEGUNDOS
        )
        if resp.status_code != 200:
            return None
        texto = resp.json().get("response", "").strip()
    except (requests.exceptions.RequestException, ValueError):
        return None
    return texto[:200] or None


def simular_conversacion(modelo, num_turnos, turno_dato, dato_clave, pregunta_final, tema_seleccionado=None):
    """Simula la conversacion completa turno a turno e inserta el dato clave
    en el turno indicado. Si cualquier turno falla, la corrida se aborta como
    invalida (una conversacion con huecos no es el tratamiento que se quiere medir).
    Devuelve: conversacion_texto, tokens_prompt_totales, tokens_respuesta_totales,
    respuesta_final, estado_final, errores_por_tipo"""
    if tema_seleccionado is None:
        tema_seleccionado = seleccionar_tema()
    primer_mensaje = tema_seleccionado["inicio"]
    mensaje_con_dato = (
        f"Ah, un dato interesante que lei hoy: {dato_clave}. "
        "Pero bueno, cambiando de tema completamente, "
        "que opinas sobre los avances en inteligencia artificial?"
    )

    historial = []
    conversacion_texto = ""
    tokens_prompt_totales = 0
    tokens_respuesta_totales = 0
    errores_por_tipo = {}

    for i in range(num_turnos):
        if i == 0:
            msg_usuario = primer_mensaje
        elif i == turno_dato:
            msg_usuario = mensaje_con_dato
        else:
            msg_usuario = _generar_relleno(historial)
            if msg_usuario is None:
                errores_por_tipo["generador_relleno"] = 1
                conversacion_texto += (
                    f"\n[Turno {i+1}] ERROR: el generador de relleno no respondio. "
                    "CORRIDA ABORTADA\n"
                )
                return (conversacion_texto, tokens_prompt_totales, tokens_respuesta_totales,
                        "Sin respuesta", "invalida_tecnica", errores_por_tipo)

        historial.append({"role": "user", "content": msg_usuario})
        conversacion_texto += f"\n[Turno {i+1}] Usuario: {msg_usuario}\n"

        resultado_llamada = consultar_modelo(modelo, historial)
        if resultado_llamada["estado"] != "valida":
            tipo = resultado_llamada["tipo_error"]
            errores_por_tipo[tipo] = errores_por_tipo.get(tipo, 0) + 1
            conversacion_texto += (
                f"[Turno {i+1}] ERROR ({resultado_llamada['estado']}, {tipo}): "
                "no se pudo consultar el modelo. CORRIDA ABORTADA\n"
            )
            return (conversacion_texto, tokens_prompt_totales, tokens_respuesta_totales,
                    "Sin respuesta", resultado_llamada["estado"], errores_por_tipo)

        resp_modelo = resultado_llamada["contenido"]
        tokens_prompt_totales += resultado_llamada["tokens_prompt"]
        tokens_respuesta_totales += resultado_llamada["tokens_respuesta"]
        historial.append({"role": "assistant", "content": resp_modelo})
        conversacion_texto += f"[Turno {i+1}] Modelo: {resp_modelo}\n"

    historial.append({"role": "user", "content": pregunta_final})
    conversacion_texto += f"\n[PREGUNTA FINAL] Usuario: {pregunta_final}\n"

    resultado_final = consultar_modelo(modelo, historial)
    if resultado_final["estado"] != "valida":
        respuesta_final = "Sin respuesta"
        estado_final = resultado_final["estado"]
        tipo = resultado_final["tipo_error"]
        errores_por_tipo[tipo] = errores_por_tipo.get(tipo, 0) + 1
    else:
        respuesta_final = resultado_final["contenido"]
        estado_final = "valida"
    tokens_prompt_totales += resultado_final["tokens_prompt"]
    tokens_respuesta_totales += resultado_final["tokens_respuesta"]
    conversacion_texto += f"[RESPUESTA FINAL] Modelo: {respuesta_final}\n"

    return conversacion_texto, tokens_prompt_totales, tokens_respuesta_totales, respuesta_final, estado_final, errores_por_tipo

TEMAS_CONVERSACION = [
    {"tema": "geografia", "inicio": "Hola, quiero hablar sobre geografia mundial y datos interesantes de distintos paises. Que me puedes contar?"},
    {"tema": "matematicas", "inicio": "Hola, quiero hablar sobre calculo diferencial y sus aplicaciones en la vida real. Que me puedes contar?"},
    {"tema": "programacion", "inicio": "Hola, quiero hablar sobre Python y estructuras de datos. Que me puedes contar?"},
    {"tema": "historia", "inicio": "Hola, quiero hablar sobre la Segunda Guerra Mundial y sus consecuencias. Que me puedes contar?"},
    {"tema": "economia", "inicio": "Hola, quiero hablar sobre inflacion y politica monetaria. Que me puedes contar?"},
    {"tema": "ciencia", "inicio": "Hola, quiero hablar sobre fisica cuantica y sus aplicaciones. Que me puedes contar?"},
]

def seleccionar_tema():
    """Selecciona aleatoriamente un tema de conversacion del banco."""
    return random.choice(TEMAS_CONVERSACION)


def verificar_acierto(respuesta_final, verificacion):
    """Verificacion mas estricta: el dato debe aparecer sin estar
    negado por frases como 'no recuerdo', 'no estoy seguro', etc."""
    respuesta_lower = respuesta_final.lower()
    if verificacion not in respuesta_lower:
        return False
    
    frases_negacion = [
        "no recuerdo", "no estoy seguro", "no tengo esa información",
        "no mencionaste", "no creo haber", "no logro recordar",
        "no puedo confirmar", "no sé si"
    ]
    for frase in frases_negacion:
        if frase in respuesta_lower:
            return False
    return True


def guardar_resultado(resultado):
    """Guarda el resultado en resultados/txt/ (legible) y resultados/json/
    (estructurado, para el analisis estadistico). Devuelve el nombre de archivo usado."""
    nombre_archivo = generar_nombre_archivo(
        resultado["modelo"], resultado["posicion"], resultado["turnos"]
    )

    reporte = f"""
{'='*60}
PRUEBA DE RETENCION - CONVERSACION NATURAL
{'='*60}
Modelo: {resultado['modelo']} ({resultado['empresa']})
Turnos de conversacion: {resultado['turnos']}
Dato clave insertado en turno: {resultado['turno_dato']} de {resultado['turnos']}
Posicion: {resultado['posicion']}
Tiempo de ejecucion: {resultado['tiempo_segundos']:.1f} segundos ({resultado['tiempo_segundos']/60:.1f} minutos)
Tokens del usuario (prompt): {resultado['tokens_prompt']}
Tokens del modelo (respuesta): {resultado['tokens_respuesta']}
Tokens totales: {resultado['tokens_totales']}
{'='*60}
CONVERSACION COMPLETA:
{'-'*60}
{resultado['conversacion_texto']}
{'-'*60}
RESULTADO: {'CORRIDA INVALIDA (' + resultado['estado_final'] + ')' if resultado['acierto'] is None else ('ACIERTO' if resultado['acierto'] else 'FALLO')}
{'='*60}
"""
    with open(f"resultados/txt/{nombre_archivo}.txt", "w") as f:
        f.write(reporte)

    resultado_json = {k: v for k, v in resultado.items() if k != "conversacion_texto"}
    with open(f"resultados/json/{nombre_archivo}.json", "w") as f:
        json.dump(resultado_json, f, indent=2, ensure_ascii=False)

    return nombre_archivo


def ejecutar_evaluacion(modelo, posicion, num_turnos):
    """Nucleo del experimento, sin CrewAI de por medio.
    Esta es la funcion que debe llamar el loop de automatizacion
    directamente en Python (fase 2), evitando la capa de LLM
    orquestador para las corridas masivas.
    Devuelve un diccionario con el resultado completo."""
    inicio_tiempo = time.time()
    modelo = modelo.strip()

    if modelo not in MODELOS_EVALUABLES:
        raise ValueError(
            f"'{modelo}' no está en la lista de modelos evaluables "
            f"({', '.join(MODELOS_EVALUABLES.keys())}). "
            "Esto es intencional: el diseño experimental está fijado a "
            "estos modelos para que el experimento sea reproducible "
            "en cualquier máquina del equipo."
        )

    num = int(str(num_turnos).strip())

    seleccion = seleccionar_dato_clave()
    dato_clave = seleccion["dato"]
    verificacion = seleccion["verificacion"]
    pregunta_final = f"Por cierto, hace rato te mencione algo. {seleccion['pregunta']}"

    pos = posicion.strip().lower()
    turno_dato = resolver_turno_dato(pos, num)
    
    tema_seleccionado = seleccionar_tema()
    detalle_error = None
    try:
        (conversacion_texto, tokens_prompt, tokens_respuesta,
         respuesta_final, estado_final, errores_por_tipo) = simular_conversacion(
            modelo, num, turno_dato, dato_clave, pregunta_final, tema_seleccionado
        )
    except Exception:
        detalle_error = traceback.format_exc()
        print(f"[ERROR INTERNO] {modelo} | {pos} | {num} turnos\n{detalle_error}")
        conversacion_texto = "\n[EXCEPCION INTERNA] La corrida se interrumpio por un error de codigo.\n"
        tokens_prompt = tokens_respuesta = 0
        respuesta_final = "Sin respuesta"
        estado_final = "invalida_tecnica"
        errores_por_tipo = {"excepcion_interna": 1}

    if estado_final == "valida":
        acierto = verificar_acierto(respuesta_final, verificacion)
    else:
        acierto = None  # no es un fallo real, es una corrida invalida/rechazada

    tiempo_total = time.time() - inicio_tiempo
    es_local = modelo not in (MODELOS_NVIDIA | MODELOS_GROQ | MODELOS_GEMINI | MODELOS_OPENROUTER)
    resultado = {
        "modelo": modelo,
        "empresa": MODELOS_EVALUABLES[modelo],
        "turnos": num,
        "posicion": pos,
        "tema": tema_seleccionado["tema"],
        "dato_clave": dato_clave,
        "turno_dato": turno_dato + 1,
        "tokens_prompt": tokens_prompt,
        "tokens_respuesta": tokens_respuesta,
        "tokens_totales": tokens_prompt + tokens_respuesta,
        "tiempo_segundos": round(tiempo_total, 1),
        "acierto": acierto,
        "estado_final": estado_final,
        "errores_por_tipo": errores_por_tipo,
        "respuesta_final": respuesta_final[:200],
        "verificacion": verificacion,
        "conversacion_texto": conversacion_texto,
        "detalle_error": detalle_error,
        "temperatura": TEMPERATURA,
        "num_ctx": NUM_CTX_OLLAMA if es_local else None,
    }
    return resultado


@tool("Evaluar retencion de informacion")
def evaluar_retencion(modelo: str, posicion: str, num_turnos: Union[str, int]) -> str:
    """Evalua si un modelo retiene informacion en una conversacion real.
    modelo: phi3:mini, gemma2:2b, llama3.2:3b o deepseek-v4-flash
    posicion: inicio, mitad o final
    num_turnos: 5, 10 o 20 (numero o texto, ambos son validos)"""
    try:
        resultado = ejecutar_evaluacion(modelo, posicion, num_turnos)
        guardar_resultado(resultado)

        if resultado['acierto'] is None:
            resultado_texto = f"CORRIDA INVALIDA ({resultado['estado_final']})"
        else:
            resultado_texto = 'ACIERTO' if resultado['acierto'] else 'FALLO'

        return (
            f"Modelo: {resultado['modelo']} ({resultado['empresa']}) | "
            f"Turnos: {resultado['turnos']} | "
            f"Posicion: {resultado['posicion']} | "
            f"Tokens totales: {resultado['tokens_totales']} | "
            f"Resultado: {resultado_texto} | "
            f"Respuesta final: {resultado['respuesta_final'][:100]} | "
            f"Tiempo: {resultado['tiempo_segundos']:.1f}s"
        )
    except Exception as e:
        return f"Error: {str(e)}"

agente_evaluador = Agent(
    role="Evaluador de confiabilidad de LLMs",
    goal="Evaluar si los modelos de lenguaje pierden informacion "
         "en conversaciones largas segun la posicion del dato y "
         "la longitud del contexto",
    backstory="Eres un investigador en evaluacion de modelos de lenguaje. "
              "REGLA CRITICA: cuando llames a la herramienta, usa EXACTAMENTE "
              "el nombre del modelo que el usuario escribio, sin modificarlo, "
              "sin agregarle sufijos, y sin cambiarlo por otro modelo similar. "
              "Copia el nombre tal cual aparece en la tarea. "
              "Realizas pruebas sistematicas llamando a la herramienta "
              "de evaluacion con diferentes combinaciones de modelo, "
              "posicion y numero de turnos.",
    tools=[evaluar_retencion],
    llm=llm,
    verbose=True,
    max_iter=5
)

if __name__ == "__main__":
    print("="*60)
    print("EVALUADOR DE CONFIABILIDAD DE LLMs")
    print("="*60)
    print("Modelos evaluables (fijos para reproducibilidad, uno por empresa):")
    for m, empresa in MODELOS_EVALUABLES.items():
        print(f"  - {m}  ({empresa})")
    print(f"Orquestador/generador de relleno: {MODELO_GENERADOR_RELLENO} (Alibaba)")
    print("Posiciones: inicio, mitad, final")
    print("Turnos: 5, 10, 20")
    print("="*60)

    modelo = input("Modelo a evaluar: ").strip()
    if modelo not in MODELOS_EVALUABLES:
        print(f"\nModelo no válido. Debe ser uno de: {', '.join(MODELOS_EVALUABLES.keys())}")
        raise SystemExit(1)

    posicion = input("Posicion del dato: ")
    turnos = input("Numero de turnos: ")

    tarea = Task(
        description=f"Llama la herramienta evaluar_retencion_de_informacion con "
                f"estos parametros EXACTOS sin modificarlos: "
                f"modelo='{modelo}', posicion='{posicion}', num_turnos={turnos}",
        expected_output="El resultado indicando modelo, turnos, posicion, "
                    "tokens y si acerto o no.",
        agent=agente_evaluador
    )

    crew = Crew(
        agents=[agente_evaluador],
        tasks=[tarea],
        verbose=True
    )

    resultado = crew.kickoff()
    print(resultado)
    print("\nResultado guardado en resultados/txt/ y resultados/json/")