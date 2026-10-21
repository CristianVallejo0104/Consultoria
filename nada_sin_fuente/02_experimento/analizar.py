"""Analiza el experimento de «Nada sin fuente».

Lee las dos clasificaciones independientes y calcula:
  1. Por clasificador y tratamiento: cuántas referencias son U, E y N, y la
     proporción de utilizables (U) con su intervalo de Wilson al 95 %.
  2. El acuerdo entre los dos clasificadores: porcentaje de coincidencia y
     kappa de Cohen (tres categorías).
  3. La lista de referencias donde no coincidieron, para discutir por qué.

Uso (desde la carpeta 02_experimento):
    python3 analizar.py

Solo usa la biblioteca estándar de Python: no hay que instalar nada.
"""

import csv
import math
from collections import Counter

CATEGORIAS = ["U", "E", "N"]
TRATAMIENTOS = ["A", "B", "C"]
CLASIFICADORES = {
    "Juan Pablo": "clasificacion_juan_pablo.csv",
    "Cristian": "clasificacion_cristian.csv",
}


def leer_clasificacion(ruta):
    """Devuelve {id: categoría}. Avisa si hay celdas vacías o valores raros."""
    datos = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            cat = fila["categoria"].strip().upper()
            if cat not in CATEGORIAS:
                raise ValueError(
                    f"{ruta}, fila {fila['id']}: categoría '{fila['categoria']}' "
                    "no válida (debe ser U, E o N)"
                )
            datos[fila["id"]] = cat
    return datos


def wilson(exitos, n, z=1.96):
    """Intervalo de Wilson al 95 % para una proporción.

    Se prefiere al intervalo de Wald (p ± z·raíz(p(1-p)/n)) porque con n
    pequeño Wald puede salirse de [0, 1] o dar ancho cero cuando p = 0 o 1.
    """
    if n == 0:
        return float("nan"), float("nan")
    p = exitos / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margen = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return max(0.0, centro - margen), min(1.0, centro + margen)


def kappa_cohen(a, b):
    """Kappa de Cohen: acuerdo observado corregido por el acuerdo por azar."""
    n = len(a)
    observado = sum(x == y for x, y in zip(a, b)) / n
    frec_a, frec_b = Counter(a), Counter(b)
    azar = sum(frec_a[c] * frec_b[c] for c in CATEGORIAS) / n**2
    if azar == 1:
        return float("nan"), observado
    return (observado - azar) / (1 - azar), observado


def main():
    with open("referencias.csv", encoding="utf-8") as f:
        refs = {fila["id"]: fila for fila in csv.DictReader(f)}

    clasif = {quien: leer_clasificacion(ruta) for quien, ruta in CLASIFICADORES.items()}

    ids = sorted(refs)
    for quien, datos in clasif.items():
        faltan = set(ids) - set(datos)
        if faltan:
            raise ValueError(f"A {quien} le faltan estas referencias: {sorted(faltan)}")

    print("=" * 66)
    print("1. PROPORCIÓN DE REFERENCIAS UTILIZABLES, POR CLASIFICADOR")
    print("=" * 66)
    for quien, datos in clasif.items():
        print(f"\nClasificó: {quien}")
        print(f"{'Trat.':<6}{'U':>4}{'E':>4}{'N':>4}{'n':>5}   {'p(U)':>6}   IC Wilson 95 %")
        for t in TRATAMIENTOS:
            cats = [datos[i] for i in ids if refs[i]["tratamiento"] == t]
            cuenta = Counter(cats)
            n = len(cats)
            li, ls = wilson(cuenta["U"], n)
            print(f"{t:<6}{cuenta['U']:>4}{cuenta['E']:>4}{cuenta['N']:>4}{n:>5}   "
                  f"{cuenta['U'] / n:>6.2f}   [{li:.2f}, {ls:.2f}]")

    print("\n" + "=" * 66)
    print("2. ACUERDO ENTRE CLASIFICADORES")
    print("=" * 66)
    a = [clasif["Juan Pablo"][i] for i in ids]
    b = [clasif["Cristian"][i] for i in ids]
    k, obs = kappa_cohen(a, b)
    coinciden = sum(x == y for x, y in zip(a, b))
    print(f"Coincidieron en {coinciden} de {len(ids)} referencias ({obs:.0%}).")
    print(f"Kappa de Cohen: {k:.2f}")
    for t in TRATAMIENTOS:
        sub = [i for i in ids if refs[i]["tratamiento"] == t]
        dis = sum(clasif["Juan Pablo"][i] != clasif["Cristian"][i] for i in sub)
        print(f"  Tratamiento {t}: {dis} desacuerdos de {len(sub)}")

    print("\nTabla cruzada (filas: Juan Pablo, columnas: Cristian)")
    print("      " + "".join(f"{c:>5}" for c in CATEGORIAS))
    for ca in CATEGORIAS:
        fila = [sum(1 for x, y in zip(a, b) if x == ca and y == cb) for cb in CATEGORIAS]
        print(f"{ca:>6}" + "".join(f"{v:>5}" for v in fila))

    print("\n" + "=" * 66)
    print("3. REFERENCIAS DONDE NO COINCIDIERON (para discutir por qué)")
    print("=" * 66)
    hubo = False
    for i in ids:
        if clasif["Juan Pablo"][i] != clasif["Cristian"][i]:
            hubo = True
            print(f"{i}: Juan Pablo={clasif['Juan Pablo'][i]}  "
                  f"Cristian={clasif['Cristian'][i]}  | {refs[i]['referencia'][:60]}")
    if not hubo:
        print("Ninguna.")


if __name__ == "__main__":
    main()
