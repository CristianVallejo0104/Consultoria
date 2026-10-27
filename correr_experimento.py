import csv
import os
import sys
import zlib
import random
import itertools
from collections import Counter
import traceback
from agente import (ejecutar_evaluacion, guardar_resultado, validar_parametros,
                    TEMAS_CONVERSACION)

SEMILLA_EXPERIMENTO = 42
MAX_INVALIDAS_SEGUIDAS = 3

CONFIGS = {
    "preliminares_tokens": {
        "modelos": ["gemma3:4b", "llama3.2:3b", "phi3:mini"],
        "posiciones": ["mitad"],
        "niveles": [4000, 8000, 12000],
        "replicas": 1,
    },
    "piloto_phi4": {
        "modelos": ["phi4-mini"],
        "posiciones": ["mitad"],
        "niveles": [4000, 8000, 12000],
        "replicas": 1,
    },
    "final_D14": {
        "modelos": ["phi4-mini", "llama3.2:3b", "gemma3:4b"],
        "posiciones": ["inicio", "mitad", "final"],
        "niveles": [4000, 8000, 12000],
        "replicas": 5,
    },
}

COLUMNAS = ["modelo", "posicion", "nivel_tokens", "replica", "estado_final", "acierto",
            "turnos_reales", "contexto_al_dato", "contexto_final", "contexto_decreciente",
            "tokens_totales", "tiempo_segundos", "errores", "tema", "dato_clave",
            "bloque", "orden_en_bloque", "indice_dato", "indice_tema",
            "done_reason_final", "respuesta_final_vacia", "contexto_tras_dato",
            "contexto_antes_pregunta", "turnos_dato_a_pregunta", "dato_sobre_nivel",
            "turnos_relleno_cortados", "intento"]


def orden_del_bloque(bloque, tratamientos):
    """Devuelve los tratamientos en orden aleatorio, siempre el mismo para el mismo bloque."""
    texto = f"orden|{SEMILLA_EXPERIMENTO}|{bloque}"
    entero = zlib.crc32(texto.encode())
    generador = random.Random(entero)
    copia = list(tratamientos)
    generador.shuffle(copia)
    return copia

def es_reintentable(estado_final, errores):
    """Falla técnica externa (no es resultado del tratamiento): se repite al relanzar."""
    return estado_final == "invalida_tecnica" and "no_alcanzo_nivel" not in str(errores)


def _clave(r):
    return (r["modelo"], r["posicion"], int(r["nivel_tokens"]), int(r["replica"]))


def ya_hechas(ruta):
    """Combinaciones ya resueltas en el CSV (para retomar una corrida cortada).
    Una clave cuenta como hecha si alguna de sus filas no es reintentable."""
    if not os.path.exists(ruta):
        return set()
    with open(ruta, encoding="utf-8") as f:
        return {_clave(r) for r in csv.DictReader(f)
                if not es_reintentable(r["estado_final"], r["errores"])}


def intentos_previos(ruta):
    """Cuántas filas hay en el CSV por clave (modelo, posicion, nivel, replica)."""
    if not os.path.exists(ruta):
        return Counter()
    with open(ruta, encoding="utf-8") as f:
        return Counter(_clave(r) for r in csv.DictReader(f))


def main(nombre):
    cfg = CONFIGS[nombre]
    ruta = f"resultados/{nombre}.csv"

    # Falla YA si algo no está en el diseño, no horas después
    for modelo in cfg["modelos"]:
        for pos in cfg["posiciones"]:
            for nivel in cfg["niveles"]:
                validar_parametros(modelo, pos, nivel)

    os.makedirs("resultados/txt", exist_ok=True)
    os.makedirs("resultados/json", exist_ok=True)
    hechas = ya_hechas(ruta)
    intentos = intentos_previos(ruta)
    seguidas = 0
    if not os.path.exists(ruta):
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS)

    for bloque in range(1, cfg["replicas"] + 1):
        tratamientos = list(itertools.product(cfg["modelos"], cfg["posiciones"],
                                              cfg["niveles"]))
        for i, (modelo, pos, nivel) in enumerate(orden_del_bloque(bloque, tratamientos)):
            rep = bloque
            if (modelo, pos, nivel, rep) in hechas:
                continue
            indice_dato = bloque - 1
            indice_tema = (i + bloque) % len(TEMAS_CONVERSACION)
            print(f">>> bloque {bloque} | {modelo} | {pos} | {nivel} tokens", flush=True)
            r = ejecutar_evaluacion(modelo, pos, nivel,
                                    indice_dato=indice_dato, indice_tema=indice_tema)
            try:
                guardar_resultado(r, carpeta_salida=f"resultados/{nombre}", replica=rep)
                fila = [modelo, pos, nivel, rep, r["estado_final"], r["acierto"],
                        r["turnos_reales"], r["contexto_al_dato"], r["contexto_final"],
                        r["contexto_decreciente"], r["tokens_totales"],
                        r["tiempo_segundos"], r["errores_por_tipo"],
                        r["tema"], r["dato_clave"],
                        bloque, i + 1, indice_dato, indice_tema,
                        r["done_reason_final"], r["respuesta_final_vacia"],
                        r["contexto_tras_dato"], r["contexto_antes_pregunta"],
                        r["turnos_dato_a_pregunta"], r["dato_sobre_nivel"],
                        r["turnos_relleno_cortados"],
                        intentos[(modelo, pos, nivel, rep)] + 1]
                with open(ruta, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow(fila)
            except Exception:
                detalle = traceback.format_exc()
                print(f"[ERROR AL GUARDAR] {modelo} | {pos} | {nivel} | bloque {bloque}\n{detalle}",
                      flush=True)
                with open(f"resultados/{nombre}_errores.log", "a", encoding="utf-8") as f:
                    f.write(f"--- {modelo} | {pos} | {nivel} | bloque {bloque}\n{detalle}\n")
                continue
            intentos[(modelo, pos, nivel, rep)] += 1
            print("   ", r["estado_final"], r["acierto"], r["contexto_final"],
                  r["tiempo_segundos"], "s", flush=True)
            if es_reintentable(r["estado_final"], r["errores_por_tipo"]):
                seguidas += 1
            else:
                seguidas = 0
            if seguidas >= MAX_INVALIDAS_SEGUIDAS:
                print(f"\n[DETENIDO] {seguidas} corridas reintentables seguidas. "
                      f"Último estado: {r['estado_final']} | error: {r['errores_por_tipo']}.\n"
                      "Basta relanzar el mismo comando cuando se arregle la causa: "
                      "las reintentables se repiten y las demás se omiten.", flush=True)
                sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIGS:
        print("Uso: python correr_experimento.py <config>")
        print("Configs disponibles:", ", ".join(CONFIGS))
        sys.exit(1)
    main(sys.argv[1])