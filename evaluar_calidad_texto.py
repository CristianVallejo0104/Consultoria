import requests
import glob
import re
import json
import os


def extraer_turnos_usuario(texto_conversacion):
    """Extrae solo los mensajes del generador de relleno ('Usuario'),
    uniéndolos en un solo bloque para evaluar su calidad."""
    turnos = re.findall(r"\[Turno \d+\] Usuario: (.+?)(?=\n\[Turno|\Z)", texto_conversacion, re.DOTALL)
    return "\n\n".join(t.strip() for t in turnos)

def extraer_notas(respuesta_llm):
    """Extrae las tres notas numéricas del texto de respuesta, tolerando
    variaciones de formato del LLM juez (mayúsculas, tildes, asteriscos de
    markdown, palabras intermedias)."""
    notas = {"NATURALIDAD": None, "COHERENCIA": None, "INTERES": None}
    patrones = {
        "NATURALIDAD": r"naturalidad",
        "COHERENCIA": r"coherencia",
        "INTERES": r"inter[eé]s",
    }
    for clave, patron in patrones.items():
        match = re.search(rf"{patron}[\*\s]*:?[\*\s]*(\d)", respuesta_llm, re.IGNORECASE)
        if match:
            notas[clave] = int(match.group(1))
    return notas

def evaluar_calidad(fragmento_conversacion, modelo="qwen2.5:1.5b"):
    """Evalúa naturalidad, coherencia e interés de un fragmento de conversación,
    siguiendo las dimensiones de Mehri y Eskenazi (2020) con el mecanismo de
    razonamiento paso a paso de G-Eval (Liu et al., 2023)."""
    prompt = f"""Evalúa el siguiente fragmento de una conversación simulada según tres criterios, cada uno en escala de 1 a 5:

1. Naturalidad: ¿suena como algo que diría una persona real?
2. Coherencia: ¿es una continuación lógica del contexto previo?
3. Interés: ¿es interesante o se siente repetitivo/vacío?

Primero razona brevemente sobre cada criterio, luego da las notas en el formato:
NATURALIDAD: X
COHERENCIA: X
INTERES: X

Fragmento:
{fragmento_conversacion}
"""
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": modelo, "prompt": prompt, "stream": False},
        timeout=180
    )
    return resp.json().get("response", "")


# --- Configuración ---
CARPETA_RESULTADOS = "resultados/txt"
CARPETA_SALIDA = "resultados/calidad_texto"
MUESTRA = 5  # cuántos archivos evaluar; None para todos

os.makedirs(CARPETA_SALIDA, exist_ok=True)

archivos = glob.glob(f"{CARPETA_RESULTADOS}/*.txt")
if MUESTRA:
    archivos = archivos[:MUESTRA]

for ruta in archivos:
    nombre_base = os.path.basename(ruta).replace(".txt", "")
    ruta_salida = f"{CARPETA_SALIDA}/{nombre_base}_calidad.json"

    with open(ruta, encoding="utf-8") as f:
        texto = f.read()

    solo_usuario = extraer_turnos_usuario(texto)
    respuesta_completa = evaluar_calidad(solo_usuario)
    notas = extraer_notas(respuesta_completa)

    registro = {
        "archivo_origen": ruta,
        "texto_evaluado": solo_usuario,
        "notas": notas,
        "razonamiento_completo": respuesta_completa,
        "modelo_juez": "qwen2.5:1.5b",
        "metodo": "G-Eval (Liu et al., 2023) sobre dimensiones de Mehri y Eskenazi (2020) — solo turnos de Usuario",
    }

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    print(f"{nombre_base}: {notas} -> guardado en {ruta_salida}")

print(f"\nListo. {len(archivos)} archivos evaluados, guardados en {CARPETA_SALIDA}/")