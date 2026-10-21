# Inventario de fallos — Cristian Vallejo

> Lo llena y lo sube Cristian, sin consultar el de Juan Pablo. Mínimo tres fallos.
> Escribe con tus palabras. Borra estas líneas de ayuda al terminar.

## Fallo 1

- **Herramienta:** Gemini (chat). 
- **Qué generó:** Una lista de tres surveys sobre alucinaciones con autores y arXiv. Al arXiv:2311.05232 le puso "Zhang et al., 2024" y a "Siren's Song" (arXiv:2309.01219) le puso "Huang et al., 2023".
- **Qué estaba mal:** Los autores estaban cruzados. El 2311.05232 es de Huang et al. y el 2309.01219 es de Zhang et al. (lo comprobé en la primera página de cada PDF). Los papers existían, pero la atribución era falsa.
- **Cómo lo detecté:** Con ayuda de Claude para contrastar si lo que me daba era cierto ya que creí que Gemini al tener el motor de busqueda de Google, me podría encontrar papers o documentos relevantes para el proyecto y apoyarnos con eso e igualmente revisar que decía el PDF, igualmente Claude lo contrastó con la busqueda y vio que los autores estaban cruzados.
- **Qué me costó:** Tokens y tiempo como varias horas buscando papers que se adecuen a mi proyecto y sirvan para apoyarnos con ellos y al menos varias horas verificando cada paper. 
- **Qué lo habría evitado:** Revisar el paper y abrir la pagina del arXiv o el pdf para corroborar el nombre de los autores de los papers.

## Fallo 2

- **Herramienta:** Claude
- **Qué generó:** En el chat del 29 de septiembre afirmó que Gemini había inventado los subtipos "Entity-error" y "Relation-error" de la taxonomía de Huang et al.
- **Qué estaba mal:** Están en el PDF de Huang como subcategorías de Factual Contradiction.
- **Cómo lo detecté:** No lo detecté yo al principio. Cuando pegué el texto de Gemini en un chat nuevo, Claude abrió el PDF y vio que los subtipos sí estaban. Yo lo confirmé buscándolos en el PDF.
- **Qué me costó:** Casi registro como cierta una afirmación falsa (que Gemini inventó esos subtipos) y tuve que rehacer la verificación.
- **Qué lo habría evitado:** Buscar el termino directo en el paper para corroborarlo.

## Fallo 3

- **Herramienta:** Claude (chat del 23 de septiembre, explicando G-Eval).
- **Qué generó:** Afirmó que G-Eval "es subjetivo" y "depende de una API de pago", y esas ideas pasaron a la §2.2 de nuestro anteproyecto.
- **Qué estaba mal:** El PDF de G-Eval no usa la palabra "subjetivo" ni dice que la API sea de pago. Lo más cercano es que muestrea 20 veces con GPT-4 (p. 3), pero eso no es lo que afirmábamos. Eran interpretaciones presentadas como si fueran del paper.
- **Cómo lo detecté:** Lo detecté al contrastar con Claude, que me pidió buscar la palabra 'subjective' en el PDF de G-Eval. La busqué y no apareció. Después Juan la marcó en la trazabilidad (filas 8 y 9).
- **Qué me costó:** Nuestro anteproyecto, ya entregado, tenía dos afirmaciones sin fuente (§2.2) que ahora hay que corregir y declarar en la memoria.
- **Qué lo habría evitado:** Antes de poner una afirmación sobre un paper en el anteproyecto, buscar esa idea en el PDF y anotar la página.

---

Firma: Cristian Vallejo — Fecha: 21/10/2026
