import csv
from collections import Counter

from preparar_etiquetado import kappa_cohen

HOJA_A = "etiquetado/hoja_cristian.csv"
HOJA_B = "etiquetado/hoja_juan.csv"
CATEGORIAS = ("1", "2", "3", "4", "5", "6")


def leer(ruta):
    # utf-8-sig: LibreOffice puede guardar el CSV con BOM al inicio
    with open(ruta, encoding="utf-8-sig") as f:
        return {x["id"]: x["categoria"].strip() for x in csv.DictReader(f)}


def revisar(etiquetas, ruta):
    malas = [id_ for id_, cat in etiquetas.items() if cat not in CATEGORIAS]
    if malas:
        raise SystemExit(f"{ruta}: falta categoria valida (1 a 6) en {', '.join(malas)}")


def main():
    # primero la hoja B, para que un error en ella no muestre nada de la hoja A
    b = leer(HOJA_B)
    revisar(b, HOJA_B)
    a = leer(HOJA_A)
    revisar(a, HOJA_A)
    if set(a) != set(b):
        raise SystemExit("las dos hojas no tienen los mismos id")

    ids = sorted(a)
    etiquetas_a = [a[i] for i in ids]
    etiquetas_b = [b[i] for i in ids]
    coinciden = sum(x == y for x, y in zip(etiquetas_a, etiquetas_b))
    print(f"casos: {len(ids)} | coincidencias: {coinciden} ({coinciden / len(ids):.3f})")
    print(f"kappa de Cohen: {kappa_cohen(etiquetas_a, etiquetas_b):.3f}")

    print(f"\n== tabla cruzada (filas {HOJA_A}, columnas {HOJA_B})")
    cruce = Counter(zip(etiquetas_a, etiquetas_b))
    print("    " + "".join(f"{c:>4}" for c in CATEGORIAS))
    for fila in CATEGORIAS:
        print(f"{fila:>4}" + "".join(f"{cruce[(fila, col)]:>4}" for col in CATEGORIAS))

    print("\n== desacuerdos (se discuten despues del calculo)")
    for i in ids:
        if a[i] != b[i]:
            print(f"{i}: {a[i]} frente a {b[i]}")


if __name__ == "__main__":
    main()
