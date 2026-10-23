# Experimento — resultados

> Se llena después de correr `python3 analizar.py`. Copiar aquí sus tablas y escribir la interpretación.

## Conteos y proporción de utilizables por tratamiento

### Clasificación de Juan Pablo

| Tratamiento | U | E | N | n | Proporción U | IC exacto 95 % |
|---|---|---|---|---|---|---|
| A · control | 8 | 2 | 0 | 10 | 0,80 | [0,44; 0,97] |
| B · búsqueda | 6 | 4 | 0 | 10 | 0,60 | [0,26; 0,88] |
| C · anclaje | 9 | 1 | 0 | 10 | 0,90 | [0,55; 1,00] |

### Clasificación de Cristian

| Tratamiento | U | E | N | n | Proporción U | IC exacto 95 % |
|---|---|---|---|---|---|---|
| A · control | 8 | 2 | 0 | 10 | 0,80 | [0,44; 0,97] |
| B · búsqueda | 6 | 4 | 0 | 10 | 0,60 | [0,26; 0,88] |
| C · anclaje | 9 | 1 | 0 | 10 | 0,90 | [0,55; 1,00] |

**Intervalo usado: exacto de Clopper-Pearson**, el mismo del proyecto (D-14). Con n = 10 la aproximación
normal (Wald) puede salirse de [0, 1] o dar ancho cero cuando la proporción es 0 o 1; el exacto sale directamente
de la distribución binomial. Es conservador: algo más ancho que el de Wilson. Comprobación en R:
`binom.test(k, 10)$conf.int` debe dar los mismos límites.

## Acuerdo entre clasificadores

- Coincidencia: 30 de 30 (100 %).
- Kappa de Cohen: 1,00.
- Desacuerdos por tratamiento: A 0, B 0, C 0.

### Dónde no coincidimos y por qué

| Referencia | Juan Pablo | Cristian | Por qué creemos que pasó |
|---|---|---|---|
| Ninguna | — | — | Coincidimos en las 30 categorías. |

## Interpretación

- **C tuvo más utilizables (9 de 10), luego A (8) y B (6), pero los tres intervalos se solapan casi por completo**
  ([0,55; 1,00], [0,44; 0,97] y [0,26; 0,88]). Con n = 10 por tratamiento no se puede afirmar que una herramienta
  sea mejor que otra; el orden C > A > B es solo una tendencia.
- **No hubo ninguna N.** Ninguna herramienta inventó un artículo inexistente en estas dos consultas. Todos los errores
  fueron E: el artículo existe, pero algún dato atribuido no es correcto.
- **Cada tratamiento falló de forma distinta:**
  - A (ChatGPT): primer autor equivocado en las dos E (c1A2, c2A2).
  - B (Consensus): las cuatro E son el artículo correcto con un identificador de arXiv que pertenece a otro trabajo
    (c1B4, c2B2, c2B3, c2B5). Que una herramienta conectada a bases reales sea la única que falle en el identificador
    es el hallazgo más llamativo, y es justo el dato que un lector usaría para llegar a la fuente.
  - C (NotebookLM): una E por contenido mal atribuido (c1C5: le atribuye una taxonomía por etapas a un artículo
    sobre técnicas de mitigación).
- **Advertencia sobre C:** con contexto cerrado la herramienta solo debería citar los 11 PDF, así que un porcentaje
  alto de U no significa que "busque mejor". Además el contexto no quedó del todo cerrado: c1C3, c1C4, c1C5 y c2C5
  no son de los 11 PDF, sino de su bibliografía. La única E de C está justo en ese grupo.
- **Tipo de alucinación:** los errores de A y B son de búsqueda (metadatos de la referencia: autor, identificador);
  el de C es de anclaje (el artículo es real, pero se le atribuye un contenido que no tiene).
- **Acuerdo:** coincidimos en las 30 categorías (kappa = 1,00). Las notas de los dos archivos son casi idénticas en
  redacción y el CSV de Juan Pablo se subió después del de Cristian (ver `../README.md`), así que este acuerdo no
  debe leerse como prueba de una clasificación independiente.
