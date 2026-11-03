from descriptivo import cargar_validas
from fisher import comparar
from permutaciones import prueba, FACTORES

RUTA = "resultados/final_D14.csv"


def main():
    filas = [x for x in cargar_validas(RUTA) if x["bloque"] != "4"]
    print("corridas sin el bloque 4:", len(filas))
    print("\n##### Fisher por pares con Holm")
    for factor in FACTORES:
        comparar(filas, factor)
    print("\n##### Permutacion estratificada")
    for factor in FACTORES:
        prueba(filas, factor)


if __name__ == "__main__":
    main()