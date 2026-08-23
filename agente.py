from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai import LLM
import requests
import json

llm = LLM(
    model="ollama/qwen2.5",
    base_url="http://localhost:11434"
)

@tool("Evaluar retencion de informacion")
def evaluar_retencion(modelo: str, posicion: str, num_turnos: str) -> str:
    """Evalua si un modelo retiene informacion en una conversacion real.
    modelo: llama3.1, phi3:mini o gemma2:2b
    posicion: inicio, mitad o final
    num_turnos: 5, 10 o 20"""
    try:
        num = int(num_turnos.strip())
        dato_clave = "la capital de Australia es Canberra"
        pregunta_final = ("Por cierto, hace rato mencioné un dato sobre "
                          "Australia. Recuerdas cual es su capital?")

        pos = posicion.strip()
        if pos == "inicio":
            turno_dato = 1
        elif pos == "mitad":
            turno_dato = num // 2
        elif pos == "final":
            turno_dato = num - 2
        else:
            turno_dato = num // 2

        mensaje_con_dato = (
            f"Ah, un dato interesante que lei hoy: {dato_clave}. "
            "Pero bueno, sigamos con lo que hablabamos."
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
                    "Eres un usuario curioso hablando con un asistente. "
                    "Responde de forma natural a lo que te acaban de decir. "
                    "Puedes hacer preguntas de seguimiento, comentar algo, "
                    "o cambiar de tema. Se breve, 1 o 2 oraciones maximo. "
                    "NO repitas lo que dijo el asistente. "
                    f"El asistente acaba de decir: {historial[-1]['content'][:300]}"
                )
                resp_gen = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "qwen2.5",
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
                    "model": modelo.strip(),
                    "messages": historial,
                    "stream": False
                }
            )

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
                "model": modelo.strip(),
                "messages": historial,
                "stream": False
            }
        )

        resp_f = resp_final.json()
        respuesta_modelo = resp_f.get("message", {}).get("content", "Sin respuesta")
        tokens_totales += resp_f.get("eval_count", 0)
        conversacion_texto += f"[RESPUESTA FINAL] Modelo: {respuesta_modelo}\n"

        acierto = "canberra" in respuesta_modelo.lower()

        reporte = f"""
{'='*60}
PRUEBA DE RETENCION - CONVERSACION NATURAL
{'='*60}
Modelo: {modelo.strip()}
Turnos de conversacion: {num}
Dato clave insertado en turno: {turno_dato + 1} de {num}
Posicion: {pos}
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

        return (
            f"Modelo: {modelo.strip()} | "
            f"Turnos: {num} | "
            f"Posicion: {pos} | "
            f"Tokens: {tokens_totales} | "
            f"Resultado: {'ACIERTO' if acierto else 'FALLO'} | "
            f"Respuesta final: {respuesta_modelo[:100]}"
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
print("Modelos disponibles: llama3.1, phi3:mini, gemma2:2b")
print("Posiciones: inicio, mitad, final")
print("Turnos: 5, 10, 20")
print("="*60)

modelo = input("Modelo a evaluar: ")
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