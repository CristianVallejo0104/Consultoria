import random
from collections import defaultdict
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"
FACTORES = ("modelo", "posicion", "nivel_tokens")
N_PERM = 20000
SEMILLA = 42


def rango_aciertos(etiquetas, aciertos):
    conteo = defaultdict(lambda: [0, 0])
    for e, a in zip(etiquetas, aciertos):
        conteo[e][0] += 1
        conteo[e][1] += a
    props = [k / n for n, k in conteo.values()]
    return max(props) - min(props)


def prueba(filas, factor):
    otros = [f for f in FACTORES if f != factor]
    etiquetas = [x[factor] for x in filas]
    aciertos = [1 if x["acierto"] == "True" else 0 for x in filas]
    estratos = defaultdict(list)
    for i, x in enumerate(filas):
        estratos[(x["bloque"],) + tuple(x[o] for o in otros)].append(i)
    observado = rango_aciertos(etiquetas, aciertos)
    gen = random.Random(SEMILLA)
    extremos = 0
    for _ in range(N_PERM):
        barajado = list(aciertos)
        for indices in estratos.values():
            valores = [aciertos[i] for i in indices]
            gen.shuffle(valores)
            for i, v in zip(indices, valores):
                barajado[i] = v
        if rango_aciertos(etiquetas, barajado) >= observado:
            extremos += 1
    p = (extremos + 1) / (N_PERM + 1)
    print(f"{factor:14s} grupos = {len(estratos):3d}  rango = {observado:.3f}  p = {p:.5f}")


def main():
    filas = cargar_validas(RUTA)
    print("corridas validas:", len(filas), "| permutaciones:", N_PERM)
    for factor in FACTORES:
        prueba(filas, factor)


if __name__ == "__main__":
    main()