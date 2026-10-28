from itertools import combinations
from scipy.stats import fisher_exact
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"
FACTORES = ("modelo", "posicion", "nivel_tokens")


def contar(filas, factor):
    conteo = {}
    for x in filas:
        nivel = x[factor]
        if nivel not in conteo:
            conteo[nivel] = [0, 0]
        if x["acierto"] == "True":
            conteo[nivel][0] += 1
        else:
            conteo[nivel][1] += 1
    return conteo


def holm(pvalores):
    m = len(pvalores)
    orden = sorted(range(m), key=lambda i: pvalores[i])
    ajustados = [0.0] * m
    maximo = 0.0
    for rango, i in enumerate(orden):
        valor = min(1.0, (m - rango) * pvalores[i])
        maximo = max(maximo, valor)
        ajustados[i] = maximo
    return ajustados


def comparar(filas, factor):
    conteo = contar(filas, factor)
    pares = list(combinations(sorted(conteo), 2))
    pvalores = [fisher_exact([conteo[a], conteo[b]]).pvalue for a, b in pares]
    ajustados = holm(pvalores)
    print(f"\n== {factor}")
    for (a, b), p, pa in zip(pares, pvalores, ajustados):
        print(f"{a} vs {b}: p = {p:.4f}   p ajustado (Holm) = {pa:.4f}")


def main():
    filas = cargar_validas(RUTA)
    print("corridas validas:", len(filas))
    for factor in FACTORES:
        comparar(filas, factor)


if __name__ == "__main__":
    main()