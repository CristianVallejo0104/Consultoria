from collections import defaultdict
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"


def tabla(filas, clave_fn, titulo):
    grupos = defaultdict(lambda: [0, 0])
    for x in filas:
        clave = clave_fn(x)
        grupos[clave][0] += 1
        if x["acierto"] == "False":
            grupos[clave][1] += 1
    print(f"\n== {titulo}")
    for clave in sorted(grupos):
        n, fallos = grupos[clave]
        print(f"{str(clave):28s} {fallos:3d} fallos de {n:3d}")


def tercio(x):
    orden = int(x["orden_en_bloque"])
    if orden <= 9:
        return "1 (ordenes 1-9)"
    if orden <= 18:
        return "2 (ordenes 10-18)"
    return "3 (ordenes 19-27)"


def main():
    filas = cargar_validas(RUTA)
    print("corridas validas:", len(filas))
    tabla(filas, lambda x: int(x["bloque"]), "fallos por bloque")
    tabla(filas, tercio, "fallos por tercio del orden en el bloque")
    tabla(filas, lambda x: (int(x["bloque"]), x["modelo"]), "fallos por bloque y modelo")
    tabla(filas, lambda x: x["tema"], "fallos por tema")


if __name__ == "__main__":
    main()