"""
agente.py — Evaluador de confiabilidad de LLMs en conversaciones largas.

Flujo: se elige (modelo, posicion del dato, nivel de tokens). Se simula una
conversacion natural hasta que el contexto alcanza el nivel; en la posicion
indicada se inserta un dato inventado; al final se pregunta por el dato y se
verifica si el modelo lo retuvo.
"""
import json
import os
import random
import time
import traceback
from typing import Union

import requests
from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()  # lee .env: las claves de API nunca van en el codigo
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ============================================================
# 1. PARAMETROS FIJOS DEL EXPERIMENTO
# ============================================================
SEMILLA = 42
random.seed(SEMILLA)  # fija SOLO la eleccion de dato y tema; NO el muestreo del modelo (pendiente, D-07)

TEMPERATURA = 0.7              # modelos evaluados y generador de relleno
TEMPERATURA_ORQUESTADOR = 0.0  # el orquestador solo copia parametros: sin aleatoriedad

NIVELES_TOKENS = (4000, 8000, 12000)                    # contexto en la pregunta final
POSICIONES_TOKENS = {"inicio": None, "mitad": 0.50, "final": 0.85}  # fraccion del nivel donde va el dato
TURNO_DATO_INICIO = 2          # "inicio" = el dato va en el 2.o turno

NUM_CTX_OLLAMA = 16384         # holgura sobre el nivel maximo (12K) + pregunta final + respuesta
MAX_TOKENS_RESPUESTA = 300     # tope comun: un modelo verboso no llena el contexto solo
MAX_TURNOS = 60                # si no llega al nivel en 60 turnos, la corrida es invalida
TIMEOUT_SEGUNDOS = 600         # con contextos largos una llamada puede tardar minutos

MAX_CHARS_RELLENO = 400             # tope de caracteres del mensaje de relleno
MAX_CHARS_ENTRADA_GENERADOR = 500   # cuanto de la respuesta del modelo ve el generador

OLLAMA_URL = "http://localhost:11434"

# ============================================================
# 2. MODELOS
# Evaluados: una empresa distinta cada uno. Orquestador y generador de
# relleno: de una CUARTA empresa (Alibaba), para evitar sesgo de
# auto-preferencia hacia modelos de su propia familia.
# ============================================================
MODELOS_LOCALES = {
    "phi4-mini": "Microsoft",
    "llama3.2:3b": "Meta",
    "gemma3:4b": "Google",  # reemplazo a gemma2:2b (D-01)
}

# Diseño B (cloud, por cerrar, D-02): "alias": ("id exacto en OpenRouter", "Empresa")
MODELOS_CLOUD = {}

MODELOS_EVALUABLES = {
    **MODELOS_LOCALES,
    **{alias: empresa for alias, (_, empresa) in MODELOS_CLOUD.items()},
}

MODELO_GENERADOR_RELLENO = "qwen2.5:1.5b"
MODELO_CEREBRO = f"ollama/{MODELO_GENERADOR_RELLENO}"

llm = LLM(model=MODELO_CEREBRO, base_url=OLLAMA_URL, temperature=TEMPERATURA_ORQUESTADOR)

# ============================================================
# 3. MATERIALES DEL EXPERIMENTO (datos, temas y prompts versionados)
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

TEMAS_CONVERSACION = [
    {"tema": "geografia", "inicio": "Hola, quiero hablar sobre geografia mundial y datos interesantes de distintos paises. Que me puedes contar?"},
    {"tema": "matematicas", "inicio": "Hola, quiero hablar sobre calculo diferencial y sus aplicaciones en la vida real. Que me puedes contar?"},
    {"tema": "programacion", "inicio": "Hola, quiero hablar sobre Python y estructuras de datos. Que me puedes contar?"},
    {"tema": "historia", "inicio": "Hola, quiero hablar sobre la Segunda Guerra Mundial y sus consecuencias. Que me puedes contar?"},
    {"tema": "economia", "inicio": "Hola, quiero hablar sobre inflacion y politica monetaria. Que me puedes contar?"},
    {"tema": "ciencia", "inicio": "Hola, quiero hablar sobre fisica cuantica y sus aplicaciones. Que me puedes contar?"},
]

# Mensaje del "usuario" que inserta el dato. Cambia de tema a proposito.
MENSAJE_DATO_V1 = (
    "Ah, un dato interesante que lei hoy: {dato}. "
    "Pero bueno, cambiando de tema completamente, "
    "que opinas sobre los avances en inteligencia artificial?"
)

# Prompt del generador de relleno: rol, restricciones y formato de salida.
PROMPT_RELLENO_V1 = (
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
    "El asistente acaba de decir: {ultimo}"
)


def seleccionar_dato_clave():
    """Elige al azar un dato del banco (reproducible por la semilla)."""
    return random.choice(DATOS_CLAVE)


def seleccionar_tema():
    """Elige al azar un tema de conversacion del banco."""
    return random.choice(TEMAS_CONVERSACION)


# ============================================================
# 4. VALIDACION DE PARAMETROS (un solo punto de entrada)
# ============================================================
SINONIMOS_POSICION = {
    "inicio": "inicio", "inicial": "inicio", "principio": "inicio", "comienzo": "inicio",
    "mitad": "mitad", "medio": "mitad", "media": "mitad", "centro": "mitad", "center": "mitad",
    "final": "final", "fin": "final", "ultimo": "final", "end": "final",
}


def validar_parametros(modelo, posicion, nivel_tokens):
    """Normaliza y valida (modelo, posicion, nivel). Lanza ValueError si algo
    no esta en el diseño: mejor fallar antes que medir un tratamiento distinto
    al que se creia. Devuelve (modelo, posicion_canonica, nivel_int)."""
    modelo = str(modelo).strip()
    if modelo not in MODELOS_EVALUABLES:
        raise ValueError(
            f"'{modelo}' no está en la lista de modelos evaluables "
            f"({', '.join(MODELOS_EVALUABLES)}). Es intencional: el diseño "
            "experimental está fijado a estos modelos para que sea reproducible."
        )
    if modelo in MODELOS_CLOUD and not OPENROUTER_API_KEY:
        raise ValueError("Falta OPENROUTER_API_KEY en el archivo .env")

    pos = SINONIMOS_POSICION.get(str(posicion).strip().lower())
    if pos is None:
        raise ValueError(f"Posición '{posicion}' no válida. Usa: {', '.join(POSICIONES_TOKENS)}.")

    try:
        nivel = int(str(nivel_tokens).strip())
    except ValueError:
        raise ValueError(f"Nivel '{nivel_tokens}' no es un número. Usa uno de: {NIVELES_TOKENS}.") from None
    if nivel not in NIVELES_TOKENS:
        raise ValueError(f"Nivel {nivel} fuera del diseño. Usa uno de: {NIVELES_TOKENS}.")

    return modelo, pos, nivel


# ============================================================
# 5. CAPA DE MODELOS: consultar un LLM y devolver siempre el mismo formato
# ============================================================
def _invalida(estado, codigo_http, tipo_error):
    """Llamada que NO produjo respuesta utilizable."""
    return {"contenido": None, "tokens_prompt": 0, "tokens_respuesta": 0,
            "estado": estado, "codigo_http": codigo_http, "tipo_error": tipo_error}


def _valida(contenido, tokens_prompt, tokens_respuesta):
    """Llamada exitosa."""
    return {"contenido": contenido, "tokens_prompt": tokens_prompt,
            "tokens_respuesta": tokens_respuesta, "estado": "valida",
            "codigo_http": 200, "tipo_error": None}


def _procesar_openai_compat(resp):
    """Interpreta una respuesta con formato OpenAI (OpenRouter)."""
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


def _consultar_ollama(modelo, historial):
    """Modelo local vía Ollama. Los tokens los cuenta el propio modelo."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": modelo,
            "messages": historial,
            "stream": False,
            "options": {
                "temperature": TEMPERATURA,
                "num_ctx": NUM_CTX_OLLAMA,
                "num_predict": MAX_TOKENS_RESPUESTA,
            },
        },
        timeout=TIMEOUT_SEGUNDOS,
    )
    if resp.status_code != 200:
        return _invalida("invalida_tecnica", resp.status_code, "desconocido")
    data = resp.json()
    contenido = data.get("message", {}).get("content")
    if contenido is None:
        return _invalida("invalida_tecnica", 200, "respuesta_inesperada")
    return _valida(contenido, data.get("prompt_eval_count", 0), data.get("eval_count", 0))


def _consultar_openrouter(modelo, historial):
    """Modelo cloud vía OpenRouter (Diseño B). Con modelos de razonamiento,
    verificar que los tokens de razonamiento no consuman el tope."""
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={"model": MODELOS_CLOUD[modelo][0], "messages": historial,
              "temperature": TEMPERATURA, "max_tokens": MAX_TOKENS_RESPUESTA},
        timeout=TIMEOUT_SEGUNDOS,
    )
    return _procesar_openai_compat(resp)


def _despachar_modelo(modelo, historial):
    """Cloud si el modelo está en MODELOS_CLOUD; si no, local."""
    if modelo in MODELOS_CLOUD:
        return _consultar_openrouter(modelo, historial)
    return _consultar_ollama(modelo, historial)


def consultar_modelo(modelo, historial):
    """Punto de entrada único. Nunca lanza excepciones de red: las convierte
    en una llamada inválida con su tipo de error."""
    try:
        return _despachar_modelo(modelo, historial)
    except requests.exceptions.Timeout:
        return _invalida("invalida_tecnica", None, "timeout")
    except requests.exceptions.ConnectionError:
        return _invalida("invalida_tecnica", None, "conexion")
    except ValueError:  # JSON ilegible
        return _invalida("invalida_tecnica", 200, "respuesta_inesperada")
    except requests.exceptions.RequestException:
        return _invalida("invalida_tecnica", None, "error_red")


# ============================================================
# 6. PIEZAS DEL EXPERIMENTO
# ============================================================
def _generar_relleno(historial):
    """Pide al generador (local) el siguiente mensaje del 'usuario'.
    Devuelve el texto, o None si el generador falló. Corta en el último
    fin de oración para no dejar frases a medias."""
    prompt = PROMPT_RELLENO_V1.format(
        ultimo=historial[-1]["content"][:MAX_CHARS_ENTRADA_GENERADOR]
    )
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODELO_GENERADOR_RELLENO, "prompt": prompt, "stream": False,
                  "options": {"temperature": TEMPERATURA}},
            timeout=TIMEOUT_SEGUNDOS,
        )
        if resp.status_code != 200:
            return None
        texto = resp.json().get("response", "").strip()
    except (requests.exceptions.RequestException, ValueError):
        return None

    texto = texto[:MAX_CHARS_RELLENO]
    ultimo_fin = max(texto.rfind("."), texto.rfind("?"), texto.rfind("!"))
    if ultimo_fin > 40:
        texto = texto[:ultimo_fin + 1]
    return texto or None


def _resultado_vacio():
    """Estructura que devuelve simular_conversacion, con valores neutros."""
    return {
        "conversacion_texto": "",
        "tokens_prompt": 0,            # suma de todas las llamadas (el historial se reenvía cada turno)
        "tokens_respuesta": 0,
        "respuesta_final": "Sin respuesta",
        "estado_final": "valida",
        "errores_por_tipo": {},
        "turno_dato": None,            # turno (desde 1) en que se insertó el dato
        "contexto_al_dato": None,      # tokens de contexto en ese momento
        "contexto_final": None,        # tokens de prompt en la pregunta final
        "turnos_reales": 0,
        "contextos_por_turno": [],
        "contexto_decreciente": False, # True = la medición de tokens es sospechosa (¿caché?)
    }


def _contar_error(r, tipo):
    r["errores_por_tipo"][tipo] = r["errores_por_tipo"].get(tipo, 0) + 1


def _toca_insertar_dato(turno, fraccion, contexto, nivel_tokens):
    """inicio: en el turno fijo; mitad/final: al cruzar su fracción del nivel."""
    if fraccion is None:
        return turno == TURNO_DATO_INICIO
    return contexto >= fraccion * nivel_tokens


def simular_conversacion(modelo, nivel_tokens, posicion, dato_clave,
                         pregunta_final, tema, verbose=False):
    """Simula la conversación turno a turno hasta que el contexto alcanza
    nivel_tokens, insertando el dato en la posición indicada, y hace la
    pregunta final. Si cualquier paso falla, la corrida es inválida (una
    conversación con huecos no es el tratamiento que se quiere medir).
    Devuelve un dict con la forma de _resultado_vacio()."""
    fraccion = POSICIONES_TOKENS[posicion]
    mensaje_con_dato = MENSAJE_DATO_V1.format(dato=dato_clave)
    r = _resultado_vacio()
    historial = []
    contexto = 0  # tokens de prompt + respuesta de la última llamada
    dato_insertado = False
    nivel_alcanzado = False

    for turno in range(1, MAX_TURNOS + 1):
        # 1) ¿Qué dice el "usuario" en este turno?
        if turno == 1:
            msg_usuario = tema["inicio"]
        elif not dato_insertado and _toca_insertar_dato(turno, fraccion, contexto, nivel_tokens):
            msg_usuario = mensaje_con_dato
            dato_insertado = True
            r["turno_dato"] = turno
            r["contexto_al_dato"] = contexto
            if verbose:
                print(f"      >> dato insertado en turno {turno} con {contexto} tokens", flush=True)
        else:
            msg_usuario = _generar_relleno(historial)
            if msg_usuario is None:
                _contar_error(r, "generador_relleno")
                r["estado_final"] = "invalida_tecnica"
                r["conversacion_texto"] += (
                    f"\n[Turno {turno}] ERROR: el generador de relleno no respondió. CORRIDA ABORTADA\n")
                break

        historial.append({"role": "user", "content": msg_usuario})
        r["conversacion_texto"] += f"\n[Turno {turno}] Usuario: {msg_usuario}\n"

        # 2) Respuesta del modelo evaluado
        llamada = consultar_modelo(modelo, historial)
        if llamada["estado"] != "valida":
            _contar_error(r, llamada["tipo_error"])
            r["estado_final"] = llamada["estado"]
            r["conversacion_texto"] += (
                f"[Turno {turno}] ERROR ({llamada['estado']}, {llamada['tipo_error']}): "
                "no se pudo consultar el modelo. CORRIDA ABORTADA\n")
            break

        historial.append({"role": "assistant", "content": llamada["contenido"]})
        r["conversacion_texto"] += f"[Turno {turno}] Modelo: {llamada['contenido']}\n"
        r["tokens_prompt"] += llamada["tokens_prompt"]
        r["tokens_respuesta"] += llamada["tokens_respuesta"]

        # 3) Medir el contexto. Debe crecer siempre; si baja, la medición falló.
        contexto_previo = contexto
        contexto = llamada["tokens_prompt"] + llamada["tokens_respuesta"]
        r["turnos_reales"] = turno
        r["contextos_por_turno"].append(contexto)
        if contexto < contexto_previo:
            r["contexto_decreciente"] = True
        if verbose:
            print(f"      turno {turno}: contexto = {contexto} tokens", flush=True)

        # 4) ¿Ya llegamos al nivel (y el dato ya está insertado)?
        if dato_insertado and contexto >= nivel_tokens:
            nivel_alcanzado = True
            break

    if r["estado_final"] == "valida" and not nivel_alcanzado:
        _contar_error(r, "no_alcanzo_nivel")
        r["estado_final"] = "invalida_tecnica"
        r["conversacion_texto"] += (
            f"\n[ERROR] No se alcanzó el nivel de {nivel_tokens} tokens en "
            f"{MAX_TURNOS} turnos. CORRIDA ABORTADA\n")

    if r["estado_final"] != "valida":
        return r

    # Pregunta final
    historial.append({"role": "user", "content": pregunta_final})
    r["conversacion_texto"] += f"\n[PREGUNTA FINAL] Usuario: {pregunta_final}\n"
    final = consultar_modelo(modelo, historial)
    r["tokens_prompt"] += final["tokens_prompt"]
    r["tokens_respuesta"] += final["tokens_respuesta"]
    if final["estado"] != "valida":
        _contar_error(r, final["tipo_error"])
        r["estado_final"] = final["estado"]
    else:
        r["respuesta_final"] = final["contenido"]
        r["contexto_final"] = final["tokens_prompt"]
    r["conversacion_texto"] += f"[RESPUESTA FINAL] Modelo: {r['respuesta_final']}\n"
    return r


def verificar_acierto(respuesta_final, verificacion):
    """Verificación estricta: el dato debe aparecer sin estar negado por
    frases como 'no recuerdo', 'no estoy seguro', etc."""
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


# ============================================================
# 7. NUCLEO DEL EXPERIMENTO Y GUARDADO (sin CrewAI de por medio)
# ============================================================
def ejecutar_evaluacion(modelo, posicion, nivel_tokens, verbose=False):
    """Núcleo del experimento. Es lo que llama el runner en las corridas
    masivas (sin pasar por el LLM orquestador). Devuelve un dict completo."""
    inicio_tiempo = time.time()
    modelo, pos, nivel = validar_parametros(modelo, posicion, nivel_tokens)

    seleccion = seleccionar_dato_clave()
    pregunta_final = f"Por cierto, hace rato te mencione algo. {seleccion['pregunta']}"
    tema = seleccionar_tema()

    detalle_error = None
    try:
        sim = simular_conversacion(modelo, nivel, pos, seleccion["dato"],
                                   pregunta_final, tema, verbose)
    except Exception:
        detalle_error = traceback.format_exc()
        print(f"[ERROR INTERNO] {modelo} | {pos} | {nivel} tokens\n{detalle_error}")
        sim = _resultado_vacio()
        sim["estado_final"] = "invalida_tecnica"
        sim["errores_por_tipo"] = {"excepcion_interna": 1}
        sim["conversacion_texto"] = "\n[EXCEPCION INTERNA] La corrida se interrumpió por un error de código.\n"

    if sim["estado_final"] == "valida":
        acierto = verificar_acierto(sim["respuesta_final"], seleccion["verificacion"])
    else:
        acierto = None  # corrida inválida: no cuenta como fallo del modelo

    es_local = modelo in MODELOS_LOCALES
    return {
        "modelo": modelo,
        "empresa": MODELOS_EVALUABLES[modelo],
        "posicion": pos,
        "nivel_tokens": nivel,
        "tema": tema["tema"],
        "dato_clave": seleccion["dato"],
        "verificacion": seleccion["verificacion"],
        "turno_dato": sim["turno_dato"],
        "contexto_al_dato": sim["contexto_al_dato"],
        "contexto_final": sim["contexto_final"],
        "turnos_reales": sim["turnos_reales"],
        "contextos_por_turno": sim["contextos_por_turno"],
        "tokens_prompt": sim["tokens_prompt"],
        "tokens_respuesta": sim["tokens_respuesta"],
        "tokens_totales": sim["tokens_prompt"] + sim["tokens_respuesta"],
        "tiempo_segundos": round(time.time() - inicio_tiempo, 1),
        "acierto": acierto,
        "estado_final": sim["estado_final"],
        "errores_por_tipo": sim["errores_por_tipo"],
        "contexto_decreciente": sim["contexto_decreciente"],
        "respuesta_final": sim["respuesta_final"],
        "conversacion_texto": sim["conversacion_texto"],
        "detalle_error": detalle_error,
        "temperatura": TEMPERATURA,
        "max_tokens_respuesta": MAX_TOKENS_RESPUESTA,
        "num_ctx": NUM_CTX_OLLAMA if es_local else None,
    }


def texto_resultado(resultado):
    if resultado["acierto"] is None:
        return f"CORRIDA INVALIDA ({resultado['estado_final']})"
    return "ACIERTO" if resultado["acierto"] else "FALLO"


def generar_nombre_archivo(modelo, posicion, nivel_tokens):
    """Nombre único: modelo_posicion_NIVELtok_réplica (p. ej. gemma3_4b_mitad_4000tok_01)."""
    modelo_limpio = modelo.replace(":", "_").replace(".", "_")
    base = f"{modelo_limpio}_{posicion}_{nivel_tokens}tok"
    replica = 1
    while os.path.exists(f"resultados/txt/{base}_{replica:02d}.txt"):
        replica += 1
    return f"{base}_{replica:02d}"


def guardar_resultado(resultado):
    """Guarda en resultados/txt/ (legible) y resultados/json/ (para el análisis).
    Devuelve el nombre de archivo usado."""
    os.makedirs("resultados/txt", exist_ok=True)
    os.makedirs("resultados/json", exist_ok=True)
    nombre = generar_nombre_archivo(
        resultado["modelo"], resultado["posicion"], resultado["nivel_tokens"])

    reporte = f"""
{'='*60}
PRUEBA DE RETENCION - CONVERSACION NATURAL
{'='*60}
Modelo: {resultado['modelo']} ({resultado['empresa']})
Posicion del dato: {resultado['posicion']}
Nivel de tokens (nominal): {resultado['nivel_tokens']}
Dato insertado en el turno {resultado['turno_dato']} con {resultado['contexto_al_dato']} tokens de contexto
Contexto en la pregunta final: {resultado['contexto_final']} tokens ({resultado['turnos_reales']} turnos)
Tiempo de ejecucion: {resultado['tiempo_segundos']:.1f} s ({resultado['tiempo_segundos']/60:.1f} min)
Tokens de prompt acumulados (suma de todas las llamadas): {resultado['tokens_prompt']}
Tokens de respuesta acumulados: {resultado['tokens_respuesta']}
Tokens totales acumulados: {resultado['tokens_totales']}
{'='*60}
CONVERSACION COMPLETA:
{'-'*60}
{resultado['conversacion_texto']}
{'-'*60}
RESULTADO: {texto_resultado(resultado)}
{'='*60}
"""
    with open(f"resultados/txt/{nombre}.txt", "w", encoding="utf-8") as f:
        f.write(reporte)

    resultado_json = {k: v for k, v in resultado.items() if k != "conversacion_texto"}
    with open(f"resultados/json/{nombre}.json", "w", encoding="utf-8") as f:
        json.dump(resultado_json, f, indent=2, ensure_ascii=False)

    return nombre


# ============================================================
# 8. CAPA DE AGENTE (CrewAI): puerta de entrada, no controla el bucle
# ============================================================
@tool("evaluar_retencion")
def evaluar_retencion(modelo: str, posicion: str, nivel_tokens: Union[str, int]) -> str:
    """Evalua si un modelo local retiene un dato inventado dentro de una conversacion larga.
    modelo: nombre exacto, por ejemplo phi4-mini, llama3.2:3b o gemma3:4b
    posicion: inicio, mitad o final (donde se inserta el dato)
    nivel_tokens: 4000, 8000 o 12000 (tamano del contexto; numero o texto, ambos son validos)"""
    try:
        resultado = ejecutar_evaluacion(modelo, posicion, nivel_tokens)
        guardar_resultado(resultado)
        return (
            f"Modelo: {resultado['modelo']} ({resultado['empresa']}) | "
            f"Nivel: {resultado['nivel_tokens']} tokens | "
            f"Posicion: {resultado['posicion']} | "
            f"Contexto final: {resultado['contexto_final']} | "
            f"Resultado: {texto_resultado(resultado)} | "
            f"Respuesta final: {resultado['respuesta_final'][:100]} | "
            f"Tiempo: {resultado['tiempo_segundos']:.1f}s"
        )
    except Exception as e:
        return f"Error: {str(e)}"


agente_evaluador = Agent(
    role="Evaluador de confiabilidad de LLMs",
    goal="Evaluar si los modelos de lenguaje pierden informacion "
         "en conversaciones largas segun la posicion del dato y "
         "el nivel de tokens del contexto",
    backstory="Eres un investigador en evaluacion de modelos de lenguaje. "
              "REGLA CRITICA: cuando llames a la herramienta, usa EXACTAMENTE "
              "los parametros que el usuario escribio, sin modificarlos, "
              "sin agregar sufijos y sin cambiar el modelo por otro similar. "
              "Copia los valores tal cual aparecen en la tarea.",
    tools=[evaluar_retencion],
    llm=llm,
    verbose=True,
    max_iter=5,  # ojo: un reintento del orquestador vuelve a ejecutar la evaluación completa
)


if __name__ == "__main__":
    print("=" * 60)
    print("EVALUADOR DE CONFIABILIDAD DE LLMs")
    print("=" * 60)
    print("Modelos evaluables (fijos para reproducibilidad, uno por empresa):")
    for m, empresa in MODELOS_EVALUABLES.items():
        print(f"  - {m}  ({empresa})")
    print(f"Orquestador/generador de relleno: {MODELO_GENERADOR_RELLENO} (Alibaba)")
    print(f"Posiciones: {', '.join(POSICIONES_TOKENS)}")
    print(f"Niveles de tokens: {', '.join(str(n) for n in NIVELES_TOKENS)}")
    print("=" * 60)

    try:
        modelo, posicion, nivel = validar_parametros(
            input("Modelo a evaluar: "),
            input("Posicion del dato: "),
            input("Nivel de tokens: "),
        )
    except ValueError as e:
        print(f"\n{e}")
        raise SystemExit(1)

    tarea = Task(
        description=f"Llama la herramienta evaluar_retencion con estos "
                    f"parametros EXACTOS sin modificarlos: "
                    f"modelo='{modelo}', posicion='{posicion}', nivel_tokens={nivel}",
        expected_output="El resultado indicando modelo, nivel de tokens, "
                        "posicion y si acerto o no.",
        agent=agente_evaluador,
    )

    crew = Crew(agents=[agente_evaluador], tasks=[tarea], verbose=True)
    print(crew.kickoff())
    print("\nResultado guardado en resultados/txt/ y resultados/json/")