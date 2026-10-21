# Banco de evaluación

- Entre 15 y 20 preguntas en total.
- Al menos 3 cuya respuesta **no** está en el corpus (marcadas «Fuera»): miden si el sistema se abstiene o inventa.
- La respuesta conocida y su ubicación se escriben **antes** de preguntarle al sistema.
- Cada pregunta se hace **dos veces**: en `A` (chat sin fuentes, el control) y en `C-v1` (el sistema con
  protocolo v1). Si hay v2, repetir en `C-v2`. Sin `A` no se puede decir cuánto mejoró el sistema.

## Resumen

| | A · control | C-v1 · sistema |
|---|---|---|
| Dentro del corpus: correctas y sostenidas por fragmento real | __ de __ (IC exacto 95 % [__, __]) | __ de __ (IC exacto 95 % [__, __]) |
| Fuera del corpus: se abstuvo | __ de __ | __ de __ |
| Fuera del corpus: inventó | __ de __ | __ de __ |

En A no hay fragmento que citar: ahí «correcta» es que coincida con la respuesta conocida.
Los intervalos se calculan en R con `binom.test(k, n)$conf.int`.

## Preguntas

| # | Pregunta | Respuesta conocida | Dónde está (documento, página) | A: respuesta obtenida | A: ¿correcta? | C-v1: respuesta obtenida | C-v1: ¿sostenida por un fragmento real? |
|---|---|---|---|---|---|---|---|
| 1 | | | | | sí / no | | sí / no |
| 2 | | | | | sí / no | | sí / no |
| 3 | | | | | sí / no | | sí / no |
| 4 | | | | | sí / no | | sí / no |
| 5 | | | | | sí / no | | sí / no |
| 6 | | | | | sí / no | | sí / no |
| 7 | | | | | sí / no | | sí / no |
| 8 | | | | | sí / no | | sí / no |
| 9 | | | | | sí / no | | sí / no |
| 10 | | | | | sí / no | | sí / no |
| 11 | | | | | sí / no | | sí / no |
| 12 | | | | | sí / no | | sí / no |
| 13 | | | | | sí / no | | sí / no |
| 14 | | | | | sí / no | | sí / no |
| 15 | | | | | sí / no | | sí / no |
| 16 | [Fuera] | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |
| 17 | [Fuera] | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |
| 18 | [Fuera] | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |
