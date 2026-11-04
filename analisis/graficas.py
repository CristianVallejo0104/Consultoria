import os
from collections import defaultdict
import matplotlib.pyplot as plt
from descriptivo import cargar_validas, intervalo

RUTA = "resultados/final_D14.csv"
CARPETA = "analisis/figuras"
ORDEN_POSICION = ["inicio", "mitad", "final"]
ORDEN_NIVEL = ["4000", "8000", "12000"]


def aciertos_por(filas, campo):
    grupos = defaultdict(lambda: [0, 0])
    for x in filas:
        grupos[x[campo]][0] += 1
        if x["acierto"] == "True":
            grupos[x[campo]][1] += 1
    return grupos


def grafica_modelo(filas):
    grupos = aciertos_por(filas, "modelo")
    nombres = sorted(grupos)
    props, err_bajo, err_alto = [], [], []
    for nombre in nombres:
        n, k = grupos[nombre]
        p = k / n
        bajo, alto = intervalo(k, n)
        props.append(p)
        err_bajo.append(p - bajo)
        err_alto.append(alto - p)
    plt.figure(figsize=(6, 4))
    plt.errorbar(nombres, props, yerr=[err_bajo, err_alto], fmt="o", capsize=6)
    plt.ylim(0, 1.05)
    plt.ylabel("Proporción de aciertos")
    plt.title("Acierto por modelo (IC 95 %, Clopper-Pearson)")
    plt.tight_layout()
    os.makedirs(CARPETA, exist_ok=True)
    plt.savefig(f"{CARPETA}/acierto_por_modelo.png", dpi=150)
    plt.close()


def proporciones(filas, modelo, campo, orden):
    resultado = []
    for nivel in orden:
        n = 0
        k = 0
        for x in filas:
            if x["modelo"] == modelo and x[campo] == nivel:
                n += 1
                if x["acierto"] == "True":
                    k += 1
        bajo, alto = intervalo(k, n)
        resultado.append((k / n, bajo, alto))
    return resultado


def grafica_posicion_nivel(filas):
    modelos = sorted({x["modelo"] for x in filas})
    figura, ejes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    paneles = ((ejes[0], "posicion", ORDEN_POSICION, "Posición del dato"),
               (ejes[1], "nivel_tokens", ORDEN_NIVEL, "Nivel de tokens"))
    for eje, campo, orden, titulo in paneles:
        for i, modelo in enumerate(modelos):
            datos = proporciones(filas, modelo, campo, orden)
            props = [d[0] for d in datos]
            err_bajo = [d[0] - d[1] for d in datos]
            err_alto = [d[2] - d[0] for d in datos]
            xs = [j + (i - 1) * 0.08 for j in range(len(orden))]
            eje.errorbar(xs, props, yerr=[err_bajo, err_alto],
                         marker="o", capsize=4, label=modelo)
        eje.set_xticks(range(len(orden)))
        eje.set_xticklabels(orden)
        eje.set_xlabel(titulo)
        eje.set_ylim(0, 1.05)
    ejes[0].set_ylabel("Proporción de aciertos")
    ejes[1].legend()
    figura.suptitle("Acierto por posición y nivel, por modelo (IC 95 %, Clopper-Pearson; n = 15 por punto)")
    figura.tight_layout()
    os.makedirs(CARPETA, exist_ok=True)
    figura.savefig(f"{CARPETA}/acierto_posicion_nivel.png", dpi=150)
    plt.close(figura)


def grafica_bloques(filas):
    modelos = sorted({x["modelo"] for x in filas})
    bloques = sorted({x["bloque"] for x in filas}, key=int)
    base = [0] * len(bloques)
    plt.figure(figsize=(6, 4))
    for modelo in modelos:
        fallos = [sum(1 for x in filas
                      if x["bloque"] == b and x["modelo"] == modelo and x["acierto"] == "False")
                  for b in bloques]
        plt.bar(bloques, fallos, bottom=base, label=modelo)
        base = [a + f for a, f in zip(base, fallos)]
    plt.xlabel("Bloque (dato inventado)")
    plt.ylabel("Fallos (de 27 corridas por bloque)")
    plt.title("Fallos por bloque y modelo")
    plt.legend()
    plt.tight_layout()
    os.makedirs(CARPETA, exist_ok=True)
    plt.savefig(f"{CARPETA}/fallos_por_bloque.png", dpi=150)
    plt.close()


def main():
    filas = cargar_validas(RUTA)
    grafica_modelo(filas)
    grafica_posicion_nivel(filas)
    grafica_bloques(filas)
    print("figuras guardadas en", CARPETA)


if __name__ == "__main__":
    main()