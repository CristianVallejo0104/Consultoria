import statistics
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"
POSICIONES = ("inicio", "mitad", "final")


def resumen(valores):
    return f"min {min(valores):.3f}  mediana {statistics.median(valores):.3f}  max {max(valores):.3f}"


def main():
    filas = cargar_validas(RUTA)
    print("corridas validas:", len(filas))
    for campo in ("contexto_al_dato", "contexto_tras_dato"):
        print(f"\n== {campo} / nivel_tokens")
        for pos in POSICIONES:
            fracciones = [int(x[campo]) / int(x["nivel_tokens"])
                          for x in filas if x["posicion"] == pos]
            print(f"{pos:7s} n = {len(fracciones):3d}  {resumen(fracciones)}")
    print("\n== dato por encima del nivel (dato_sobre_nivel)")
    for pos in POSICIONES:
        arriba = sum(1 for x in filas if x["posicion"] == pos and x["dato_sobre_nivel"] == "True")
        total = sum(1 for x in filas if x["posicion"] == pos)
        print(f"{pos:7s} {arriba} de {total}")


if __name__ == "__main__":
    main()