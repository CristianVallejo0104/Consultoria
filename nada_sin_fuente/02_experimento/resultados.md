# Experimento — resultados

## Procedimiento de clasificación

Las 30 referencias se clasificaron una sola vez, en **consenso**: Cristian clasificó las 30 (archivo
`clasificacion_consenso.csv`, copia de `clasificacion_cristian.csv`) y Juan Pablo declara estar de acuerdo con esa
clasificación. **No hubo dos clasificaciones independientes**: la de Juan Pablo se hizo después de que la de Cristian
estuviera publicada en el repositorio (el historial de Git muestra el orden de los commits). Por eso **no se reporta
acuerdo entre clasificadores ni kappa de Cohen**. Es un límite del experimento.

## Conteos y proporción de utilizables por tratamiento (clasificación de consenso)

| Tratamiento | U | E | N | n | Proporción U | IC exacto 95 % |
|---|---|---|---|---|---|---|
| A · control | 8 | 2 | 0 | 10 | 0.80 | [0.44, 0.97] |
| B · búsqueda | 6 | 4 | 0 | 10 | 0.60 | [0.26, 0.88] |
| C · anclaje | 9 | 1 | 0 | 10 | 0.90 | [0.55, 1.00] |

Total: 23 U, 7 E y 0 N de 30 referencias.

**Intervalo usado: exacto de Clopper-Pearson**, el mismo del proyecto (D-14). Con n = 10 la aproximación normal
(Wald) puede salirse de [0, 1] o dar ancho cero cuando la proporción es 0 o 1; el exacto sale directamente de la
distribución binomial. Comprobación en R: `binom.test(8, 10)$conf.int`, `binom.test(6, 10)$conf.int` y
`binom.test(9, 10)$conf.int`.

## Interpretación

- **Ninguna referencia fue inexistente (0 N).** Los errores fueron de tipo E: autor equivocado, o un identificador
  de arXiv que lleva a otro artículo (las notas de `clasificacion_consenso.csv` dicen cuál).
- **Los tres intervalos se solapan ampliamente** (A [0,44; 0,97], B [0,26; 0,88], C [0,55; 1,00]). Con n = 10 por
  tratamiento no se puede afirmar que un tratamiento sea mejor que otro; las diferencias observadas son compatibles
  con el azar.
- **B (búsqueda) tuvo la proporción más baja** en esta muestra, sobre todo por identificadores de arXiv que no
  corresponden al artículo citado. Que una herramienta conectada a bases reales devuelva un identificador equivocado
  es un hallazgo, no un dato a esconder.
- **C (anclaje) no se limitó a los 11 PDF.** Varias referencias de C no son documentos del cuaderno, sino trabajos
  citados en la bibliografía de esos PDF (ver las notas de c1C3, c1C4, c1C5 y c2C5). Es lo que advierte la lámina 5:
  el contexto cerrado no impide que la herramienta traiga referencias que no le dimos.
- **A (control) salió alto** porque las consultas pedían artículos muy conocidos del tema. No se debe generalizar a
  temas menos citados. Además, el control no quedó del todo limpio (ver `consultas.md`: memoria activa en la
  consulta 2 y miniaturas de sitios web en la consulta 1).
