import glob
import json
import csv 
import os 
import random 



def cargar_fallos(carpeta):
    fallos = []
    for ruta in sorted(glob.glob(f"{carpeta}/*.json")):
        with open(ruta, encoding="utf-8") as f:
            r = json.load(f)
        if r.get("estado_final") == "valida" and r.get("acierto") is False:
            fallos.append({
                "archivo": ruta,
                "modelo": r.get("modelo"),
                "posicion": r.get("posicion"),
                "nivel_tokens": r.get("nivel_tokens"),
                "respuesta_final": r["respuesta_final"],
            })
    return fallos

    
SEMILLA_ETIQUETADO = 42


def escribir_hojas(fallos, carpeta_salida):
    generador = random.Random(SEMILLA_ETIQUETADO)
    orden = list(fallos)
    generador.shuffle(orden)

    os.makedirs(carpeta_salida, exist_ok=True)
    with open(f"{carpeta_salida}/hoja_ciega.csv", "w", newline="", encoding="utf-8") as f_hoja:
        with open(f"{carpeta_salida}/clave.csv", "w", newline="", encoding="utf-8") as f_clave:
            hoja = csv.writer(f_hoja)
            clave = csv.writer(f_clave)
            hoja.writerow(["id", "respuesta_final", "categoria", "duda"])
            clave.writerow(["id", "archivo", "modelo", "posicion", "nivel_tokens"])
            for i, x in enumerate(orden, start=1):
                id_ = f"F{i:03d}"
                hoja.writerow([id_, x["respuesta_final"], "", ""])
                clave.writerow([id_, x["archivo"], x["modelo"], x["posicion"], x["nivel_tokens"]])