# Diseño experimental

Estado al 2026-10-21. Cada decisión, con su alternativa descartada, está en `docs/decisiones.md`; aquí se resume el diseño completo.

## 1. Pregunta
¿A partir de qué longitud de conversación y en qué posición deja un LLM local de retener un dato inventado, y cambia según el modelo?

## 2. Diseño

| Elemento | Definición | Registro |
|---|---|---|
| Modelo (factor fijo) | `phi4-mini`, `llama3.2:3b`, `gemma3:4b` (un modelo por empresa) | D-10, D-13, D-01 |
| Posición del dato | inicio (2.º turno), mitad (al cruzar el 50 % del nivel), final (al cruzar el 85 %) | D-06 |
| Nivel de tokens | 4,000, 8,000, 12,000: contexto en la pregunta final | D-06 |
| Tratamientos | 3 × 3 × 3 = 27 | D-14 |
| Réplicas y bloques | 5 réplicas = 5 bloques completos; 135 corridas | D-14 |
| Bloque | El dato inventado (5 datos) | D-14, D-15 |
| Tema | 6 temas, por rotación; covariable, no bloque | D-14, D-15 |
| Unidad experimental | Una conversación | D-14 |
| Respuesta | Acierto binario por cadena exacta, sin negación | D-11 |
| Constantes | Temperatura 0.7; `num_ctx` 16,384; timeout 600 s; tope de 300 tokens por respuesta; máximo 60 turnos | D-06 y `agente.py` |

## 3. Cómo se asigna cada cosa
- **Orden.** En cada bloque se baraja el orden de los 27 tratamientos con una semilla derivada de (`SEMILLA_EXPERIMENTO` = 42, bloque). Por qué: causas que no se controlan (temperatura de la GPU, estado de Ollama) se reparten al azar entre tratamientos y no se confunden con el modelo o el nivel.
- **Dato.** El bloque determina el dato. Por qué: la dificultad del dato es una fuente de variabilidad conocida (cifras de 4 y 5 dígitos y una versión), y lo conocido se controla en lugar de dejarlo al azar.
- **Tema.** (posición del tratamiento en el orden del bloque + bloque) mod 6, sin sorteo. Queda casi parejo pero no exacto (27 no se reparte en 6 temas): ver límites.
- **Alcance de la reproducibilidad.** El diseño (orden, dato, tema) es reproducible. Las salidas de los modelos no se prometen reproducibles bit a bit; esa variabilidad es la que capturan las réplicas (D-15).

## 4. Qué se mide y qué se registra
- **Acierto.** La cadena de verificación del dato aparece en la respuesta final y no está negada (`verificar_acierto`). Sin LLM juez (D-11).
- **Estados de corrida.** `valida`, `invalida_tecnica` (fallos de red o API, `acierto` nulo), `rechazo_seguridad`. Una corrida inválida no cuenta como «el modelo olvidó» (D-11).
- **Posición lograda.** Se registran `contexto_al_dato`, `contexto_tras_dato`, `contexto_antes_pregunta`, `turnos_dato_a_pregunta` y `dato_sobre_nivel`, porque el dato entra en el primer turno que cruza la fracción y el contexto real se aparta del nominal (D-16).
- **Calidad de la respuesta final.** `done_reason_final` y `respuesta_final_vacia`; `turnos_relleno_cortados` cuenta respuestas cortadas por el tope de tokens (D-16).
- **Salida.** Una fila por corrida en `resultados/<config>.csv` (26 columnas) y un JSON y un TXT por corrida en `resultados/<config>/`.

## 5. Diseños no convencionales y por qué

| Decisión | Por qué | Alternativa descartada | Registro |
|---|---|---|---|
| Dato dentro de la conversación | La pregunta es sobre memoria de trabajo conversacional; Liu et al. insertan el dato en documentos recuperados | Reproducir el esquema con documentos recuperados | D-05, D-09 |
| Niveles en tokens, no en turnos | «5 turnos» no es comparable: `phi3:mini` procesó 10,259 tokens y `gemma2:2b` 1,903 (primer corte) | Seguir en turnos | D-06 |
| Bloque por dato | Dificultad desigual de los datos | Completamente aleatorizado | D-14 |
| Dato inventado | Los datos reales se acertaban por conocimiento previo | Datos de conocimiento general | D-11 |
| Evaluación determinista | Un juez LLM añade ruido y circularidad donde la respuesta es conocida | LLM juez para retención | D-09, D-11 |
| Relleno generado por un LLM pequeño (`qwen2.5:1.5b`) | Conversaciones naturales y variadas a escala | Texto estático o preguntas fijas (versiones 1 y 2 del README) | D-04 |
| Agente CrewAI solo interactivo | Lo determinista va en código; el orquestador de 1.5B omitió parámetros | Que el agente dirija las corridas | D-08 |

## 6. Contraste con el estado del arte (D-09)
- **G-Eval** evalúa la calidad de un texto con un LLM juez; no mide retención. Su mecanismo se adaptó solo a la calidad del texto de relleno.
- **RAGAS** evalúa sistemas RAG sobre (pregunta, contexto recuperado, respuesta); aquí no hay documentos recuperados.
- **RAG** genera con documentos recuperados; no evalúa y no aplica.
- **Liu et al. (2023)** varían posición y longitud sistemáticamente; este diseño formaliza ese esquema como factorial en bloques y añade verificación estadística.

## 7. Taxonomía de fallos (D-03)
Categorías observadas en el primer corte: alucinación, admisión, negación de capacidad y alucinación narrativa; además `rechazo_seguridad`, que no es un fallo de retención. «Admisión» y «negación de capacidad» son observación propia: la literatura (Huang et al. 2023, Zhang et al. 2023, Wen et al. 2025) da el marco, pero no las nombra. El clasificador (Laya) está pospuesto por falta de fallos reales etiquetados.

## 8. Calidad del texto de relleno (D-04)
Se evalúan naturalidad, coherencia e interés de los turnos del «usuario» con un LLM juez pequeño. Es exploratorio y **no está validado contra criterio humano**: no se usan esas notas en el análisis final hasta validarlas.

## 9. Análisis previsto (no decidido)
Intervalos exactos por celda, modelo para respuesta binaria con efecto de bloque, y manejo de la separación (Firth o enfoque bayesiano; prueba exacta de Fisher en lugar de chi-cuadrado). Qué interacciones son estimables con 135 corridas y cómo tratar el tema y `contexto_final` (covariable o sensibilidad) queda para una entrada posterior. [Texto de diseño de experimentos por citar: elegir de la bibliografía del curso y verificar edición y páginas antes de citar.]

## 10. Límites
- Cinco réplicas por celda dan poca potencia; la interacción triple probablemente no es estimable.
- Las corridas inválidas rompen el balance de los bloques.
- La posición lograda se aparta de la nominal; se reporta y se analiza como sensibilidad.
- El tema no queda perfectamente balanceado (D-14).
- El tope de 300 tokens puede truncar muchas respuestas en algunos modelos (D-16).
- Cada modelo usa su tokenizador, y las conclusiones se limitan a estos tres modelos y a niveles de hasta 12K.
- El nivel de tokens es nominal; «inicio» es una posición absoluta (turno 2).

## 11. Pendiente
- Política de reintentos y tratamiento de `no_alcanzo_nivel`.
- Entrada de medida de respuesta y análisis.
- Ejecutar las 135 corridas y etiquetar fallos (kappa entre los dos integrantes).
- Verificar las constantes de `agente.py` contra D-06.