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
| A | [p. ej. ChatGPT / Claude / Gemini] | | chat nuevo, sin búsqueda web, sin archivos | |
| B | [p. ej. Consensus / Elicit / Semantic Scholar] | | | |
| C | NotebookLM | | cuaderno con los 11 PDF de `docs/fuentes/` | |

## Consulta 1 — Juan Pablo Tibamoso

**Texto exacto de la consulta** (el mismo en A, B y C):

> [escribir aquí]

Respuestas completas guardadas en: `respuestas/c1_A.md`, `respuestas/c1_B.md`, `respuestas/c1_C.md`

## Consulta 2 — Cristian Vallejo

**Texto exacto de la consulta** (el mismo en A, B y C):

> [escribir aquí]

Respuestas completas guardadas en: `respuestas/c2_A.md`, `respuestas/c2_B.md`, `respuestas/c2_C.md`
