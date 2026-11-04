import csv
from collections import Counter, defaultdict

CLAVE = "etiquetado/clave.csv"
HOJA = "etiquetado/hoja_cristian.csv"
NOMBRES = {"1": "alucinacion", "2": "admision", "3": "negacion de capacidad",
           "4": "alucinacion narrativa", "5": "desvio", "6": "otra/duda"}


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    modelos = {x["id"]: x["modelo"] for x in leer(CLAVE)}
    conteo = defaultdict(Counter)
    for x in leer(HOJA):
        conteo[modelos[x["id"]]][x["categoria"]] += 1
    print("tipos de fallo por modelo (etiquetas de un solo evaluador)")
    for modelo in sorted(conteo):
        total = sum(conteo[modelo].values())
        print(f"\n{modelo}: {total} fallos")
        for cat in sorted(conteo[modelo]):
            print(f"  {cat} {NOMBRES[cat]:24s} {conteo[modelo][cat]}")


if __name__ == "__main__":
    main()