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
load_dotenv()

MODELOS_NVIDIA = {
    "deepseek-v4-flash": "deepseek-ai/deepseek-v4-flash-0731",
}
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

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
    "llama3.2:3b": "Meta",
    "deepseek-v4-flash": "DeepSeek",
}

MODELO_CEREBRO = "ollama/qwen2.5:1.5b"        # Alibaba — orquestador del Agent de CrewAI
MODELO_GENERADOR_RELLENO = "qwen2.5:1.5b"     # Alibaba — genera los turnos de relleno de la conversación

llm = LLM(
    model=MODELO_CEREBRO,
    base_url="http://localhost:11434"
)


def consultar_modelo(modelo, historial):
    """Decide si consultar Ollama (local) o NVIDIA API (cloud) segun el modelo.
    Devuelve: contenido, tokens_prompt, tokens_respuesta"""
    if modelo in MODELOS_NVIDIA:
        resp = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={"model": MODELOS_NVIDIA[modelo], "messages": historial}
        )
        if resp.status_code != 200:
            return None, 0, 0
        data = resp.json()
        contenido = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_prompt = usage.get("prompt_tokens", 0)
        tokens_respuesta = usage.get("completion_tokens", 0)
        return contenido, tokens_prompt, tokens_respuesta
    else:
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": modelo, "messages": historial, "stream": False}
        )
        if resp.status_code != 200:
            return None, 0, 0
        data = resp.json()
        contenido = data.get("message", {}).get("content", "Sin respuesta")
        tokens_prompt = data.get("prompt_eval_count", 0)
        tokens_respuesta = data.get("eval_count", 0)
        return contenido, tokens_prompt, tokens_respuesta

def generar_nombre_archivo(modelo, posicion, turnos):
    """Genera un nombre unico basado en modelo, posicion, turnos y replica."""
    modelo_limpio = modelo.replace(":", "_").replace(".", "_")
    base = f"{modelo_limpio}_{posicion}_{turnos}turnos"
    replica = 1
    while os.path.exists(f"resultados/txt/{base}_{replica:02d}.txt"):
        replica += 1
    return f"{base}_{replica:02d}"


    
@tool("Evaluar retencion de informacion")
def evaluar_retencion(modelo: str, posicion: str, num_turnos: Union[str, int]) -> str:
    """Evalua si un modelo retiene informacion en una conversacion real.
    modelo: phi3:mini, gemma2:2b, llama3.2:3b o deepseek-v4-flash
    posicion: inicio, mitad o final
    num_turnos: 5, 10 o 20 (numero o texto, ambos son validos)"""
    try:
        inicio_tiempo = time.time()
        modelo = modelo.strip()
        if modelo not in MODELOS_EVALUABLES:
            return (
                f"Error: '{modelo}' no está en la lista de modelos evaluables "
                f"({', '.join(MODELOS_EVALUABLES.keys())}). "
                "Esto es intencional: el diseño experimental está fijado a "
                "estos modelos para que el experimento sea reproducible "
                "en cualquier máquina del equipo."
            )

        num = int(str(num_turnos).strip())
        datos_clave = [
            {"dato": "el codigo secreto del proyecto Fenix es 7492",
             "pregunta": "Recuerdas cual era el codigo del proyecto Fenix?",
             "verificacion": "7492"},
            {"dato": "el numero de expediente del caso Aurora es 3851",
             "pregunta": "Recuerdas el numero de expediente del caso Aurora?",
             "verificacion": "3851"},
            {"dato": "la clave de acceso del laboratorio Nexus es 6037",
             "pregunta": "Recuerdas la clave de acceso del laboratorio Nexus?",
             "verificacion": "6037"},
        ]
        seleccion = random.choice(datos_clave)
        dato_clave = seleccion["dato"]
        pregunta_final = f"Por cierto, hace rato te mencione algo. {seleccion['pregunta']}"
        verificacion = seleccion["verificacion"]

        pos = posicion.strip().lower()
        if pos in ["inicio", "inicial", "principio", "comienzo"]:
            turno_dato = 1
        elif pos in ["mitad", "medio", "media", "center", "centro"]:
            turno_dato = num // 2
        elif pos in ["final", "fin", "ultimo", "end"]:
            turno_dato = num - 2
        else:
            turno_dato = num // 2

        mensaje_con_dato = (
            f"Ah, un dato interesante que lei hoy: {dato_clave}. "
            "Pero bueno, cambiando de tema completamente, "
            "que opinas sobre los avances en inteligencia artificial?"
        )

        primer_mensaje = ("Hola, quiero hablar sobre geografia mundial "
                          "y datos interesantes de distintos paises. "
                          "Que me puedes contar?")

        historial = []
        conversacion_texto = ""
        tokens_prompt_totales = 0
        tokens_respuesta_totales = 0

        for i in range(num):
            if i == 0:
                msg_usuario = primer_mensaje
            elif i == turno_dato:
                msg_usuario = mensaje_con_dato
            else:
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
                resp_gen = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": MODELO_GENERADOR_RELLENO,
                        "prompt": prompt_generar,
                        "stream": False
                    }
                )
                msg_usuario = resp_gen.json().get("response", "Interesante, cuentame mas.")
                msg_usuario = msg_usuario.strip()[:200]

            historial.append({"role": "user", "content": msg_usuario})
            conversacion_texto += f"\n[Turno {i+1}] Usuario: {msg_usuario}\n"

            resp_modelo, tp, tr = consultar_modelo(modelo, historial)
            if resp_modelo is None:
                conversacion_texto += f"[Turno {i+1}] ERROR: no se pudo consultar el modelo\n"
                continue
            tokens_prompt_totales += tp
            tokens_respuesta_totales += tr
            historial.append({"role": "assistant", "content": resp_modelo})
            conversacion_texto += f"[Turno {i+1}] Modelo: {resp_modelo}\n"

        historial.append({"role": "user", "content": pregunta_final})
        conversacion_texto += f"\n[PREGUNTA FINAL] Usuario: {pregunta_final}\n"

        respuesta_modelo, tp_f, tr_f = consultar_modelo(modelo, historial)
        if respuesta_modelo is None:
            respuesta_modelo = "Sin respuesta"
        tokens_prompt_totales += tp_f
        tokens_respuesta_totales += tr_f

        acierto = verificacion in respuesta_modelo.lower()
        tiempo_total = time.time() - inicio_tiempo
        reporte = f"""
{'='*60}
PRUEBA DE RETENCION - CONVERSACION NATURAL
{'='*60}
Modelo: {modelo} ({MODELOS_EVALUABLES[modelo]})
Turnos de conversacion: {num}
Dato clave insertado en turno: {turno_dato + 1} de {num}
Posicion: {pos}
Tiempo de ejecucion: {tiempo_total:.1f} segundos ({tiempo_total/60:.1f} minutos)
Tokens del usuario (prompt): {tokens_prompt_totales}
Tokens del modelo (respuesta): {tokens_respuesta_totales}
Tokens totales: {tokens_prompt_totales + tokens_respuesta_totales}
{'='*60}
CONVERSACION COMPLETA:
{'-'*60}
{conversacion_texto}
{'-'*60}
RESULTADO: {'ACIERTO' if acierto else 'FALLO'}
{'='*60}
"""

        nombre_archivo = generar_nombre_archivo(modelo, pos, num)
        with open(f"resultados/txt/{nombre_archivo}.txt", "w") as f:
            f.write(reporte)

        resultado_json = {
            "modelo": modelo,
            "empresa": MODELOS_EVALUABLES[modelo],
            "turnos": num,
            "posicion": pos,
            "dato_clave": dato_clave,
            "turno_dato": turno_dato + 1,
            "tokens_prompt": tokens_prompt_totales,
            "tokens_respuesta": tokens_respuesta_totales,
            "tokens_totales": tokens_prompt_totales + tokens_respuesta_totales,
            "tiempo_segundos": round(tiempo_total, 1),
            "acierto": acierto,
            "respuesta_final": respuesta_modelo[:200],
            "verificacion": verificacion
        }

        
        with open(f"resultados/json/{nombre_archivo}.json", "w") as f:
            json.dump(resultado_json, f, indent=2, ensure_ascii=False)

        return (
            f"Modelo: {modelo} ({MODELOS_EVALUABLES[modelo]}) | "
            f"Turnos: {num} | "
            f"Posicion: {pos} | "
            f"Tokens totales: {tokens_prompt_totales + tokens_respuesta_totales} | "          
            f"Resultado: {'ACIERTO' if acierto else 'FALLO'} | "
            f"Respuesta final: {respuesta_modelo[:100]} | "
            f"Tiempo: {tiempo_total:.1f}s"
        )
    except Exception as e:
        return f"Error: {str(e)}"


agente_evaluador = Agent(
    role="Evaluador de confiabilidad de LLMs",
    goal="Evaluar si los modelos de lenguaje pierden informacion "
         "en conversaciones largas segun la posicion del dato y "
         "la longitud del contexto",
    backstory="Eres un investigador en evaluacion de modelos de lenguaje. "
              "Realizas pruebas sistematicas llamando a la herramienta "
              "de evaluacion con diferentes combinaciones de modelo, "
              "posicion y numero de turnos.",
    tools=[evaluar_retencion],
    llm=llm,
    verbose=True,
    max_iter=5
)

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
    description=f"Evalua el modelo {modelo} con posicion {posicion} y "
                f"{turnos} turnos. Usa la herramienta con esos parametros.",
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