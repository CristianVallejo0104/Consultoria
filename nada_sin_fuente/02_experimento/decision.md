# Tabla de decisión

> Se llena después del experimento. Cada celda debe poder defenderse: si es una
> observación propia, decir cómo se comprobó; si es una afirmación del proveedor,
> poner de dónde sale (página oficial y fecha de consulta).
> Fecha de consulta de todas las fuentes externas: 22 de octubre de 2026.

## Herramientas comparadas

| Criterio | NotebookLM (ahora «Gemini Notebook») | Proyecto con archivos: ChatGPT | Vía propia (Ollama + embeddings + Chroma) |
|---|---|---|---|
| **Contexto cerrado:** ¿responde solo sobre lo que le dimos? | Solo en parte. Observado: 4 de las 10 referencias de C no eran uno de los 11 PDF, sino trabajos citados en sus bibliografías (c1C3, c1C4, c1C5, c2C5). Sin protocolo. La ayuda oficial dice que está diseñado para responder según las fuentes subidas (support.google.com/notebooklm/answer/16164461) | No probado: el plan gratuito limita a 5 archivos por proyecto y el corpus tiene 11 | No probado: depende de cómo se implemente la recuperación |
| **Cita con localización:** ¿documento y página, o solo «según los archivos»? | Observado, sin protocolo: citas con números entre corchetes, sin página (`c1_C.md`, `c2_C.md`). PENDIENTE: probar con el protocolo v1 | No probado (ver fila anterior) | No probado: habría que construirlo |
| **Privacidad:** ¿dónde quedan los documentos? | En la nube de Google. Según la ayuda oficial, no se usan para entrenar salvo retroalimentación (support.google.com/notebooklm/answer/16164461). El corpus es público, así que no es decisivo | En la cuenta de OpenAI. El uso del contenido para mejorar modelos depende de la configuración de la cuenta (help.openai.com/en/articles/8555545). No probado | local |
| **Costo:** ¿lo podemos sostener hasta diciembre? | Sí con el plan gratuito: permite 50 fuentes por cuaderno según una comparativa de terceros (elephas.app/blog/notebooklm-free-vs-plus; verificar en la ayuda oficial) y el corpus tiene 11. La cuenta de Cristian muestra «PLUS» | El plan gratuito no alcanza (límite oficial de 5 archivos por proyecto, help.openai.com/en/articles/8555545). Con plan de pago, 25 archivos según la página oficial (otra versión dice 20) | gratis (cómputo propio) |
| **Exportación a APA 7:** ¿o hay que rehacer referencias a mano? | No aplica: las referencias salen de Zotero (`biblioteca.bib`, 11 entradas). PENDIENTE: probar «Create Bibliography» en APA 7 | No aplica: se usa Zotero | No aplica: se usa Zotero |
| **Reproducibilidad:** ¿otra persona rehace el índice y obtiene lo mismo? | No probado: Juan Pablo creó su propio cuaderno con los mismos 11 PDF, pero no se corrió la misma consulta en ambos | No probado | No probado: en principio sí, si se fijan el modelo de embeddings y el tamaño de los fragmentos |

Gestor de referencias (pieza aparte del sistema): **Zotero**, comparado con **Mendeley**.

| Criterio | Zotero | Mendeley |
|---|---|---|
| Costo | Programa gratuito; 300 MB gratis de almacenamiento en la nube para adjuntos, y pago desde 2 GB por $20 al año (casrai.org/compare/zotero-vs-mendeley; verificar en zotero.org/storage) | Gratuito, con 2 GB de almacenamiento (ponder.ing/blog/zotero-vs-mendeley; verificar en la página oficial) |
| Exportación a APA 7 | Estilos CSL, APA incluido (library.yorku.ca/web/?p=3450). PENDIENTE: probar en nuestras 11 referencias | Estilos CSL, APA incluido (misma fuente) |
| Guarda el PDF con la referencia | Observado: cada referencia quedó con su PDF adjunto (11 PDF, menos de 10 MB en total; no se sincronizan, así que no usan los 300 MB) | No probado |

## Elegida

**Propuesta, a confirmar entre los dos:** NotebookLM, porque (fila de costo) el plan gratuito alcanza para las 11
fuentes, mientras que ChatGPT con archivos no, y la vía propia pierde por tiempo (ver abajo). Reservas honestas:
(1) en el experimento C tuvo la proporción más alta de utilizables (0,90), pero los intervalos de A, B y C se
solapan, así que **esa diferencia no es la razón de la elección**; (2) sin protocolo no cita la página, y eso se
prueba con el protocolo v1. Gestor de referencias: **Zotero** (gratuito, funciona en Linux, exportó el `.bib`).

## Descartadas y en qué criterio perdieron

- **ChatGPT con archivos:** perdió en costo: el plan gratuito limita los proyectos a 5 archivos y el corpus tiene 11.
- **Vía propia:** el montaje (embeddings, base de datos vectorial, citas con página) toma entre 1 y 2 semanas
  y el plazo es de pocos días; el corpus es público, así que la privacidad, su principal ventaja, no es decisiva
  aquí. Consecuencia aceptada: el techo de C3 queda en Competente (nota global máxima 4,8).
- **Mendeley:** no se probó; se elige Zotero porque ya funciona en el equipo y exporta a `.bib`.