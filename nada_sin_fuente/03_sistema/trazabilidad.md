# Tabla de trazabilidad del anteproyecto

Fuente de las afirmaciones: `docs/informes/Primera_Entrega_Consultoria.pdf`, sección 2 (estado del arte).
Una fila por cada afirmación sustantiva: toda frase que diga algo que no es opinión nuestra
(un resultado, una cifra, una definición, lo que hace o propone un autor).

**Clave del gestor** = la clave de cita de Zotero (la misma que aparece en `biblioteca.bib`).
**Ubicación** = página del PDF guardado en `docs/fuentes/` y, si se puede, una cita textual corta (menos de 15 palabras).

| # | Afirmación (cita textual del anteproyecto, con su §) | Fuente (clave del gestor) | Ubicación (página y cita corta) | Verificado por | Fecha |
|---|---|---|---|---|---|
| 1 | §2.1: «[...] no refleja su capacidad real de retención uniforme» | [clave de Liu et al.] | p. 2 y p. 5 — [cita corta] | | |
| 2 | | | | | |
| 3 | | | | | |

> La fila 1 es el ejemplo que dio el profesor en su informe (sección 6). Antes de dejarla, ábranla
> ustedes en el PDF y confirmen las páginas.

## Afirmaciones corregidas

Las que no tenían de dónde salir, o decían algo distinto a la fuente. Van también al apartado 5 de la memoria.

| Afirmación original | Problema | Corrección |
|---|---|---|
| Liu et al. citado como «(2023)» con el volumen 12 de *TACL* | Ese volumen es de 2024 (vol. 12, pp. 157–173, doi:10.1162/tacl_a_00638); 2023 es el preprint de arXiv | [elegir una versión y citarla completa] |
| «100 % localmente con Ollama, sin APIs de pago» y reproducible «en cualquier computador con 8 GB de RAM» | D-02 decidió pagar OpenRouter; D-10 registra 9,0 GB de phi3:mini con `num_ctx` 16.384 | [nueva redacción] |
| Objetivo específico 2: phi3:mini, llama3.2:3b y gemma2:2b con 5, 10 y 20 turnos | Hoy: phi4-mini, llama3.2:3b y gemma3:4b con niveles de 4.000, 8.000 y 12.000 tokens (D-01, D-06, D-13) | [nueva redacción] |
