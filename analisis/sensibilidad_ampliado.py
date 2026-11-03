import glob
import json
from fisher import comparar
from permutaciones import prueba, FACTORES
from sensibilidad_formato import acierto_ampliado, CARPETA


def cargar_ampliado():
    filas = []
    for ruta in sorted(glob.glob(f"{CARPETA}/*.json")):
        with open(ruta, encoding="utf-8") as f:
            r = json.load(f)
        if r.get("estado_final") != "valida":
            continue
        bloque = str(int(ruta.rsplit("_", 1)[1].split(".")[0]))
        ampliado = acierto_ampliado(r["respuesta_final"], r["verificacion"])
        filas.append({
            "modelo": r["modelo"],
            "posicion": r["posicion"],
            "nivel_tokens": str(r["nivel_tokens"]),
            "bloque": bloque,
            "acierto": "True" if ampliado else "False",
        })
    return filas


def main():
    filas = cargar_ampliado()
    fallos = sum(1 for x in filas if x["acierto"] == "False")
    print("corridas validas:", len(filas), "| fallos con criterio ampliado:", fallos)
    print("\n##### Fisher por pares con Holm")
    for factor in FACTORES:
        comparar(filas, factor)
    print("\n##### Permutacion estratificada")
    for factor in FACTORES:
        prueba(filas, factor)


if __name__ == "__main__":
    main()