from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai import LLM
from typing import Union
import requests
import json
import time
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
# Elegidos para correr cómodo en 8GB de RAM (el hardware más
# restrictivo del equipo): solo se carga el modelo evaluado del
# turno actual + el orquestador liviano a la vez, nunca los
# cuatro simultáneamente. Pico de memoria real: ~3-3.5GB.
# ============================================================

MODELOS_EVALUABLES = {
    "phi3:mini": "Microsoft",
    "gemma2:2b": "Google",
    "llama3.2:3b": "Meta",
}

MODELO_CEREBRO = "ollama/qwen2.5:1.5b"        # Alibaba — orquestador del Agent de CrewAI
MODELO_GENERADOR_RELLENO = "qwen2.5:1.5b"     # Alibaba — genera los turnos de relleno de la conversación

llm = LLM(
    model=MODELO_CEREBRO,
    base_url="http://localhost:11434"
)

@tool("Evaluar retencion de informacion")
def evaluar_retencion(modelo: str, posicion: str, num_turnos: Union[str, int]) -> str:
    """Evalua si un modelo retiene informacion en una conversacion real.
    modelo: phi3:mini, gemma2:2b o llama3.2:3b
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
                "estos tres modelos para que el experimento sea reproducible "
                "en cualquier máquina del equipo."
            )

        num = int(str(num_turnos).strip())
        import random
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
        tokens_totales = 0

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

            respuesta = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": modelo,
                    "messages": historial,
                    "stream": False
                }
            )
            if respuesta.status_code != 200:
                conversacion_texto += f"[Turno {i+1}] ERROR HTTP: {respuesta.status_code}\n"
                continue
            resp = respuesta.json()
            resp_modelo = resp.get("message", {}).get("content", "Sin respuesta")
            tokens_totales += resp.get("eval_count", 0)
            historial.append({"role": "assistant", "content": resp_modelo})
            conversacion_texto += f"[Turno {i+1}] Modelo: {resp_modelo}\n"

        historial.append({"role": "user", "content": pregunta_final})
        conversacion_texto += f"\n[PREGUNTA FINAL] Usuario: {pregunta_final}\n"

        resp_final = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": modelo,
                "messages": historial,
                "stream": False
            }
        )

        resp_f = resp_final.json()
        respuesta_modelo = resp_f.get("message", {}).get("content", "Sin respuesta")
        tokens_totales += resp_f.get("eval_count", 0)
        conversacion_texto += f"[RESPUESTA FINAL] Modelo: {respuesta_modelo}\n"

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
Tokens generados: {tokens_totales}
{'='*60}
CONVERSACION COMPLETA:
{'-'*60}
{conversacion_texto}
{'-'*60}
RESULTADO: {'ACIERTO' if acierto else 'FALLO'}
{'='*60}
"""

        with open("resultados.txt", "a") as f:
            f.write(reporte)

        resultado_json = {
            "modelo": modelo,
            "empresa": MODELOS_EVALUABLES[modelo],
            "turnos": num,
            "posicion": pos,
            "dato_clave": dato_clave,
            "turno_dato": turno_dato + 1,
            "tokens": tokens_totales,
            "tiempo_segundos": round(tiempo_total, 1),
            "acierto": acierto,
            "respuesta_final": respuesta_modelo[:200],
            "verificacion": verificacion
        }

        import os
        resultados_previos = []
        if os.path.exists("resultados.json"):
            with open("resultados.json", "r") as f:
                resultados_previos = json.load(f)
        resultados_previos.append(resultado_json)
        with open("resultados.json", "w") as f:
            json.dump(resultados_previos, f, indent=2, ensure_ascii=False)
        return (
            f"Modelo: {modelo} ({MODELOS_EVALUABLES[modelo]}) | "
            f"Turnos: {num} | "
            f"Posicion: {pos} | "
            f"Tokens: {tokens_totales} | "
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
print("\nResultado guardado en resultados.txt")