import csv
from collections import defaultdict
from scipy.stats import binomtest

RUTA = "resultados/final_D14.csv"


def cargar_validas(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [x for x in csv.DictReader(f) if x["estado_final"] == "valida"]


def intervalo(k, n):
    ic = binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return ic.low, ic.high


def resumen(filas, campos):
    grupos = defaultdict(lambda: [0, 0])
    for x in filas:
        clave = tuple(x[c] for c in campos)
        grupos[clave][0] += 1
        if x["acierto"] == "True":
            grupos[clave][1] += 1
    for clave in sorted(grupos):
        n, k = grupos[clave]
        bajo, alto = intervalo(k, n)
        etiqueta = " | ".join(clave)
        print(f"{etiqueta:38s} {k:3d} de {n:3d} = {k / n:.3f}  IC95% [{bajo:.3f}, {alto:.3f}]")


def main():
    filas = cargar_validas(RUTA)
    print("corridas validas:", len(filas))
    for campos in (("modelo",), ("posicion",), ("nivel_tokens",),
                   ("modelo", "posicion", "nivel_tokens")):
        print("\n== por", " x ".join(campos))
        resumen(filas, campos)


if __name__ == "__main__":
    main()