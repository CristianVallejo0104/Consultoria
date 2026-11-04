import math
import pandas as pd
from sklearn.linear_model import LogisticRegression
from descriptivo import cargar_validas

RUTA = "resultados/final_D14.csv"
REFERENCIAS = {"modelo": "phi4-mini", "posicion": "inicio",
               "nivel_tokens": "4000", "bloque": "1"}
PENALIZACIONES = (0.1, 1.0, 10.0, 1000.0)


def armar_datos(filas):
    df = pd.DataFrame(filas)[list(REFERENCIAS)]
    X = pd.get_dummies(df, dtype=int)
    X = X.drop(columns=[f"{c}_{r}" for c, r in REFERENCIAS.items()])
    y = [1 if x["acierto"] == "True" else 0 for x in filas]
    return X, y


def razones_de_momios(X, y, C):
    modelo = LogisticRegression(C=C, max_iter=5000)
    modelo.fit(X, y)
    return {col: math.exp(b) for col, b in zip(X.columns, modelo.coef_[0])}


def main():
    filas = cargar_validas(RUTA)
    X, y = armar_datos(filas)
    print("corridas:", len(y), "| fallos:", y.count(0),
          "| parametros (sin intercepto):", X.shape[1])
    tablas = {C: razones_de_momios(X, y, C) for C in PENALIZACIONES}
    print("\nRazones de momios de ACIERTO frente a la referencia")
    print("(modelo: phi4-mini, posicion: inicio, nivel: 4000, bloque: 1)")
    print(f"{'variable':28s}" + "".join(f"C={C:<8g}" for C in PENALIZACIONES))
    for col in X.columns:
        print(f"{col:28s}" + "".join(f"{tablas[C][col]:<10.2f}" for C in PENALIZACIONES))


if __name__ == "__main__":
    main()