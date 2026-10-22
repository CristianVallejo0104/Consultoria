# Experimento — diseño y consultas

## Diseño

- **Unidad:** una referencia devuelta por una herramienta.
- **Factor:** tratamiento, con tres niveles:
  - **A · control:** chat de IA sin fuentes y sin navegación web.
  - **B · búsqueda:** herramienta conectada a bases bibliográficas reales.
  - **C · anclaje:** contexto cerrado con nuestros 11 PDF (`docs/fuentes/`).
- **Consultas:** una por integrante (2 en total), cada una corrida en A, B y C.
- **Referencias por respuesta:** las primeras 5 que devuelve la herramienta, en el orden en que aparecen.
- **Respuesta:** cada referencia se clasifica como `U` (utilizable: existe y dice lo que se le atribuye),
  `E` (existe pero no dice eso) o `N` (no existe: no se encuentra por DOI ni por título).
- **Clasificación doble e independiente:** cada integrante clasifica las 30 referencias por separado,
  sin consultarse, y sube su CSV en su propio commit.

## Herramientas usadas en cada tratamiento

| Tratamiento | Herramienta | Versión / modelo | Configuración | Fecha |
|---|---|---|---|---|
| A | ChatGPT (plan gratis) | no visible en pantalla | chat nuevo, sin archivos. La búsqueda web no se pudo apagar con un interruptor: se pidió en un primer mensaje no usarla («No uses la búsqueda web ni navegues...»). Un primer intento sin ese mensaje usó búsqueda y se descartó como control | 21 oct 2026 |
| B | Consensus (plan gratis) | no aplica | consulta idéntica; la respuesta apareció marcada como «Pro» sin que lo pidiera | 21 oct 2026 |
| C | NotebookLM | plan indicado como «PLUS» en pantalla | cuaderno con los 11 PDF de `docs/fuentes/`, sin protocolo ni instrucciones personalizadas | 21 oct 2026 |


## Consulta 1 — Juan Pablo Tibamoso

**Texto exacto de la consulta** (el mismo en A, B y C):

> Dame 5 referencias académicas, con autores, año y DOI o enlace, sobre taxonomías de alucinaciones en modelos de lenguaje.

**Diferencias de configuración respecto a la consulta 2:** en A se usó chat temporal (sin memoria); en B, Consensus sin
iniciar sesión; en C, un cuaderno propio de NotebookLM con los mismos 11 PDF y sin instrucciones.

Respuestas completas guardadas en: `respuestas/c1_A.md`, `respuestas/c1_B.md`, `respuestas/c1_C.md`

## Consulta 2 — Cristian Vallejo

**Texto exacto de la consulta** (el mismo en A, B y C):

> Dame 5 referencias académicas, con autores, año y DOI o enlace, sobre cómo los modelos de lenguaje pierden información en conversaciones largas.

**Diferencias de configuración respecto a la consulta 1:** en A se usó un chat nuevo de ChatGPT con sesión iniciada (plan gratis); en B, la respuesta de Consensus apareció marcada como «Pro» sin que se pidiera; en C, el cuaderno de Cristian con los mismos 11 PDF y sin instrucciones.

Respuestas completas guardadas en: `respuestas/c2_A.md`, `respuestas/c2_B.md`, `respuestas/c2_C.md`

