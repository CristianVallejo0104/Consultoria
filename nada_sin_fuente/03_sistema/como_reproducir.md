# Cómo reproducir el sistema desde cero

Cualquiera de los dos integrantes (u otra persona) debe poder montarlo siguiendo estos pasos.
Objetivo: que arranque en menos de 60 segundos el día de la sustentación (dejar el cuaderno ya creado
y abierto; estos pasos son para rehacerlo si hiciera falta).

## Piezas

1. **Gestor de referencias:** Zotero, colección «Consultoria – fuentes». Exportación: `biblioteca.bib`.
2. **Corpus:** los 11 PDF de `docs/fuentes/` (procedencia en `procedencia.md`).
3. **Sistema que responde con cita:** NotebookLM, cuaderno «Evaluación Automatizada de Generación Aumentada por Recuperación» (el de Cristian, usado en `02_experimento/respuestas/c2_C.md`).
4. **Protocolo:** `protocolo/v1.md` (y `v2.md` si existe).

## Pasos

1. Entrar a NotebookLM (notebooklm.google.com) con una cuenta de Google.
2. Crear un cuaderno nuevo llamado «Evaluación Automatizada de Generación Aumentada por Recuperación».
3. Agregar como fuentes los 11 PDF de `docs/fuentes/` (no otros).
4. PENDIENTE: definir si el texto del protocolo vigente va en las instrucciones del cuaderno o se pega al inicio de cada consulta (ver `protocolo/v1.md`, «Dónde se configura»).
5. Prueba de humo: hacer la pregunta 1 del banco y comprobar que responde con cita al documento y página esperados.
6. Prueba de abstención: hacer una de las preguntas fuera del corpus y comprobar que responde
   «No está en las fuentes cargadas.»

## Acceso

- Dueño del cuaderno: Cristian Vallejo. Compartido con: Juan Pablo Tibamoso, como editor. Ambos pueden operarlo.
- Fecha de la última reconstrucción: no se ha reconstruido. El cuaderno se usó el 21 de octubre de 2026 (`c2_C.md`).

## Límites conocidos

- Sin protocolo, NotebookLM cita con números entre corchetes y sin página (`c1_C.md`, `c2_C.md`). Falta comprobar si con el protocolo v1 da la página.
- Sin protocolo, trajo referencias que no son de los 11 PDF, sino trabajos citados en sus bibliografías (`02_experimento/resultados.md`).
