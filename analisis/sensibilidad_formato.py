import glob
import json
import re
from collections import defaultdict
from agente import verificar_acierto

CARPETA = "resultados/final_D14"
FACTORES = ("modelo", "posicion", "nivel_tokens")


def patron_con_separadores(verificacion):
    if not verificacion.isdigit() or len(verificacion) < 4:
        return None
    grupos = []
    resto = verificacion
    while len(resto) > 3:
        grupos.insert(0, resto[-3:])
        resto = resto[:-3]
    grupos.insert(0, resto)
    return r"(?<!\d)" + r"[., ]".join(grupos) + r"(?!\d)"


def acierto_ampliado(respuesta, verificacion):
    patron = patron_con_separadores(verificacion)
    if patron is not None:
        respuesta = re.sub(patron, verificacion, respuesta)
    return verificar_acierto(respuesta, verificacion)


def main():
    conteos = {f: defaultdict(lambda: [0, 0, 0]) for f in FACTORES}
    cambios = []
    inconsistentes = 0
    total = 0
    for ruta in sorted(glob.glob(f"{CARPETA}/*.json")):
        with open(ruta, encoding="utf-8") as f:
            r = json.load(f)
        if r.get("estado_final") != "valida":
            continue
        total += 1
        exacto = r["acierto"] is True
        if verificar_acierto(r["respuesta_final"], r["verificacion"]) != exacto:
            inconsistentes += 1
        ampliado = acierto_ampliado(r["respuesta_final"], r["verificacion"])
        if ampliado and not exacto:
            cambios.append(ruta)
        for factor in FACTORES:
            c = conteos[factor][str(r[factor])]
            c[0] += 1
            c[1] += exacto
            c[2] += ampliado
    print("corridas validas:", total)
    print("recalculo exacto distinto del guardado:", inconsistentes)
    print("fallos que pasan a acierto con el criterio ampliado:", len(cambios))
    for ruta in cambios:
        print("  ", ruta)
    for factor in FACTORES:
        print(f"\n== {factor}")
        for nivel in sorted(conteos[factor]):
            n, k_exacto, k_ampliado = conteos[factor][nivel]
            print(f"{nivel:14s} exacto {k_exacto:3d}/{n}   ampliado {k_ampliado:3d}/{n}")


if __name__ == "__main__":
    main()