import csv
import os
import sys
from agente import ejecutar_evaluacion, guardar_resultado, validar_parametros

CONFIGS = {
    "preliminares_tokens": {
        "modelos": ["gemma3:4b", "llama3.2:3b", "phi3:mini"],
        "posiciones": ["mitad"],
        "niveles": [4000, 8000, 12000],
        "replicas": 1,
    },
}

COLUMNAS = ["modelo", "posicion", "nivel_tokens", "replica", "estado_final", "acierto",
            "turnos_reales", "contexto_al_dato", "contexto_final", "contexto_decreciente",
            "tokens_totales", "tiempo_segundos", "errores", "tema", "dato_clave"]


def ya_hechas(ruta):
    """Combinaciones que ya están en el CSV (para retomar una corrida cortada)."""
    if not os.path.exists(ruta):
        return set()
    with open(ruta, encoding="utf-8") as f:
        return {(r["modelo"], r["posicion"], int(r["nivel_tokens"]), int(r["replica"]))
                for r in csv.DictReader(f)}


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
    if not os.path.exists(ruta):
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS)

    for modelo in cfg["modelos"]:
        for pos in cfg["posiciones"]:
            for nivel in cfg["niveles"]:
                for rep in range(1, cfg["replicas"] + 1):
                    if (modelo, pos, nivel, rep) in hechas:
                        continue
                    print(f">>> {modelo} | {pos} | {nivel} tokens | réplica {rep}", flush=True)
                    r = ejecutar_evaluacion(modelo, pos, nivel)
                    guardar_resultado(r)
                    fila = [modelo, pos, nivel, rep, r["estado_final"], r["acierto"],
                            r["turnos_reales"], r["contexto_al_dato"], r["contexto_final"],
                            r["contexto_decreciente"], r["tokens_totales"],
                            r["tiempo_segundos"], r["errores_por_tipo"],
                            r["tema"], r["dato_clave"]]
                    with open(ruta, "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow(fila)
                    print("   ", r["estado_final"], r["acierto"], r["contexto_final"],
                          r["tiempo_segundos"], "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preliminares_tokens")