# Diseño experimental

Estado al 2026-10-28. Cada decisión, con su alternativa descartada, está en `docs/decisiones.md`; aquí se resume el diseño completo.

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
| Respuesta | Acierto binario por cadena exacta, sin negación | D-11, D-19 |
| Constantes | Temperatura 0.7; `num_ctx` 16,384; timeout 600 s; tope de 300 tokens por respuesta; máximo 60 turnos | D-06 y `agente.py` |

## 3. Cómo se asigna cada cosa
- **Orden.** En cada bloque se baraja el orden de los 27 tratamientos con una semilla derivada de (`SEMILLA_EXPERIMENTO` = 42, bloque) mediante `crc32` (el `hash()` de Python cambia entre ejecuciones). Por qué: causas que no se controlan (temperatura de la GPU, estado de Ollama) se reparten al azar entre tratamientos y no se confunden con el modelo o el nivel.
- **Dato.** El bloque determina el dato. Por qué: la dificultad del dato es una fuente de variabilidad conocida (cifras de 4 y 5 dígitos y una versión), y lo conocido se controla en lugar de dejarlo al azar.
- **Tema.** (posición del tratamiento en el orden del bloque + bloque) mod 6, sin sorteo. Queda casi parejo pero no exacto (27 no se reparte en 6 temas): ver límites.
- **Alcance de la reproducibilidad.** El diseño (orden, dato, tema) es reproducible. Las salidas de los modelos no se prometen reproducibles bit a bit; esa variabilidad es la que capturan las réplicas (D-15).

## 4. Qué se mide y qué se registra
- **Acierto.** La cadena de verificación del dato aparece en la respuesta final y no está negada (`verificar_acierto`). Sin LLM juez (D-11). El criterio no se modifica; las variantes de formato numérico se tratan aparte como sensibilidad (D-20).
- **Estados de corrida.** `valida`, `invalida_tecnica` (fallos de red o API, `acierto` nulo), `rechazo_seguridad`. Una corrida inválida no cuenta como «el modelo olvidó» (D-11). Una falla técnica externa se reintenta al relanzar; `no_alcanzo_nivel` (que figura como `invalida_tecnica`) no se reintenta porque es resultado del tratamiento; el runner se detiene tras 3 fallas reintentables seguidas (D-18).
- **Posición lograda.** Se registran `contexto_al_dato`, `contexto_tras_dato`, `contexto_antes_pregunta`, `turnos_dato_a_pregunta` y `dato_sobre_nivel`, porque el dato entra en el primer turno que cruza la fracción y el contexto real se aparta del nominal (D-16).
- **Calidad de la respuesta final.** `done_reason_final` y `respuesta_final_vacia`; `turnos_relleno_cortados` cuenta respuestas cortadas por el tope de tokens (D-16).
- **Salida.** Una fila por corrida o intento en `resultados/<config>.csv` (27 columnas, con `intento`, D-18) y un JSON y un TXT por corrida en `resultados/<config>/`. En el análisis, cada celda se toma de la fila que la cierra.

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
| Reintento manual acotado | Las fallas externas no miden retención, pero reintentar sin tope sesga | Reintentar hasta obtener una corrida válida; no reintentar nunca | D-18 |

## 6. Contraste con el estado del arte (D-09)
- **G-Eval** evalúa la calidad de un texto con un LLM juez; no mide retención. Su mecanismo se adaptó solo a la calidad del texto de relleno.
- **RAGAS** evalúa sistemas RAG sobre (pregunta, contexto recuperado, respuesta); aquí no hay documentos recuperados.
- **RAG** genera con documentos recuperados; no evalúa y no aplica.
- **Liu et al. (2023)** varían posición y longitud sistemáticamente; este diseño formaliza ese esquema como factorial en bloques y añade verificación estadística.

## 7. Taxonomía de fallos (D-03)
Categorías observadas en el primer corte: alucinación, admisión, negación de capacidad y alucinación narrativa; además `rechazo_seguridad`, que no es un fallo de retención. «Admisión» y «negación de capacidad» son observación propia: la literatura (Huang et al. 2023, Zhang et al. 2023, Wen et al. 2025) da el marco, pero no las nombra. Los fallos de `final_D14` se etiquetan a mano por los dos integrantes por separado con `docs/guia_etiquetado.md` (seis categorías) y el acuerdo se mide con kappa de Cohen. El clasificador (Laya) sigue pospuesto; su alcance se decide con el número real de fallos etiquetados.

## 8. Calidad del texto de relleno (D-04)
Se evalúan naturalidad, coherencia e interés de los turnos del «usuario» con un LLM juez pequeño. Es exploratorio y **no está validado contra criterio humano**: no se usan esas notas en el análisis final hasta validarlas.

## 9. Análisis (D-19 y D-20)
Plan fijado antes del análisis; cualquier cambio posterior se registra como entrada nueva.
- **Descriptivo:** acierto por celda con intervalo exacto de Clopper-Pearson al 95 %.
- **Modelo:** regresión logística con modelo, posición, nivel, interacción posición × nivel y bloque. Con separación probable, enfoque bayesiano con previas débilmente informativas o regresión penalizada de Firth.
- **Tablas marginales:** prueba exacta de Fisher en lugar de chi-cuadrado.
- **Cobertura:** por celda, cuántas corridas son válidas, `no_alcanzo_nivel` o `rechazo_seguridad`.
- **Sensibilidad:** con y sin respuestas vacías o cortadas; posición lograda del dato; tema; `contexto_final` (solo aquí, porque es posterior al tratamiento); y criterio ampliado a variantes de formato numérico (D-20).
- **Descartado:** ANOVA sobre el acierto 0/1, chi-cuadrado como prueba principal, modelo sin bloque, interacción triple e imputación de corridas inválidas.
- **Verificación de supuestos:** antes del ajuste, cuántos fallos hay y si hay celdas sin fallos (separación); después, convergencia y ajuste.
[Texto de diseño de experimentos por citar: elegir de la bibliografía del curso y verificar edición y páginas antes de citar.]

## 10. Límites
- Cinco réplicas por celda dan poca potencia; la interacción triple probablemente no es estimable.
- Con 19 fallos en total y ninguno de `gemma3:4b`, el modelo completo de D-19 tiene muchos más parámetros de los que los fallos permiten estimar con holgura; puede requerir simplificarse, y se registraría como decisión nueva.
- Las corridas inválidas rompen el balance de los bloques; en `final_D14` todas las celdas cerraron con resultado válido.
- La posición lograda se aparta de la nominal; se reporta y se analiza como sensibilidad.
- El tema no queda perfectamente balanceado (D-14).
- El tope de 300 tokens puede truncar muchas respuestas en algunos modelos (D-16).
- Cada modelo usa su tokenizador, y las conclusiones se limitan a estos tres modelos y a niveles de hasta 12K.
- El nivel de tokens es nominal; «inicio» es una posición absoluta (turno 2).
- El criterio exacto cuenta como fallo el número correcto con otro formato (2 casos); D-20 lo trata como sensibilidad.
- 4 filas `invalida_tecnica` por `generador_relleno` (todas de `gemma3:4b`) tienen causa no determinada, porque el error no se guarda (D-18).

## 11. Estado de la ejecución (2026-10-28)
`final_D14` está completo: 135 celdas con resultado válido y 139 filas en el CSV (4 filas técnicas inválidas conservadas como historial). Hay 19 fallos: `llama3.2:3b` 7, `phi4-mini` 12, `gemma3:4b` 0. Son conteos descriptivos, sin inferencia.

## 12. Pendiente
- Etiquetado del segundo integrante y kappa entre los dos.
- Ejecutar el análisis de D-19 y D-20 y verificar sus supuestos.
- Decidir el alcance de Laya y de los agentes de D-08 con el número real de fallos.
- Verificar las constantes de `agente.py` contra D-06.