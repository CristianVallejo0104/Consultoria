import os
from collections import defaultdict
import matplotlib.pyplot as plt
from descriptivo import cargar_validas, intervalo

RUTA = "resultados/final_D14.csv"
CARPETA = "analisis/figuras"


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


def main():
    filas = cargar_validas(RUTA)
    grafica_modelo(filas)
    print("figura guardada en", CARPETA)


if __name__ == "__main__":
    main()