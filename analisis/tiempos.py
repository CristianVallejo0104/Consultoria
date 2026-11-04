import statistics
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"
FACTORES = ("modelo", "nivel_tokens")


def resumen(tiempos):
    return (f"n = {len(tiempos):3d}  mediana {statistics.median(tiempos) / 60:5.1f} min  "
            f"min {min(tiempos) / 60:5.1f}  max {max(tiempos) / 60:5.1f}  "
            f"suma {sum(tiempos) / 3600:5.2f} h")


def main():
    filas = cargar_validas(RUTA)
    todos = [float(x["tiempo_segundos"]) for x in filas]
    print("corridas validas:", len(filas), "| tiempo total de las corridas validas:",
          f"{sum(todos) / 3600:.2f} h")
    for factor in FACTORES:
        print(f"\n== por {factor}")
        grupos = {}
        for x in filas:
            grupos.setdefault(x[factor], []).append(float(x["tiempo_segundos"]))
        for clave in sorted(grupos, key=lambda c: (len(c), c)):
            print(f"{clave:12s} {resumen(grupos[clave])}")
    print("\n== por modelo y nivel (mediana)")
    celdas = {}
    for x in filas:
        celdas.setdefault((x["modelo"], int(x["nivel_tokens"])), []).append(float(x["tiempo_segundos"]))
    for clave in sorted(celdas):
        print(f"{clave[0]:12s} {clave[1]:6d}  {statistics.median(celdas[clave]) / 60:5.1f} min")


if __name__ == "__main__":
    main()