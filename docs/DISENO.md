# Diseño experimental

Estado al 2026-11-05.


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
- **Tema.** ((orden_en_bloque − 1) + bloque) mod 6, sin sorteo. Queda casi parejo pero no exacto (27 no se reparte en 6 temas): ver límites.
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
Categorías observadas en el primer corte: alucinación, admisión, negación de capacidad y alucinación narrativa; además `rechazo_seguridad`, que no es un fallo de retención. «Admisión» y «negación de capacidad» son observación propia: la literatura (Huang et al. 2023, Zhang et al. 2023, Wen et al. 2025) da el marco, pero no las nombra. Los fallos de `final_D14` se etiquetan a mano por los dos integrantes por separado con `docs/guia_etiquetado.md` (seis categorías) y el acuerdo se mide con kappa de Cohen. Laya no se entrena ni se evalúa: con 19 fallos no alcanza (D-22).

## 8. Calidad del texto de relleno (D-04)
Se evalúan naturalidad, coherencia e interés de los turnos del «usuario» con un LLM juez pequeño. Es exploratorio y **no está validado contra criterio humano**: no se usan esas notas en el análisis final hasta validarlas.

## 9. Análisis (D-19, D-20 y D-21)
El plan se fijó en D-19 y D-20. D-21 cambió parte de D-19 después de ver los resultados descriptivos, y lo registra como entrada nueva.
- **Respuesta:** binaria, por cadena exacta (D-11). Sin medida cuantitativa (D-21).
- **Descriptivo:** acierto por celda y por factor con intervalo exacto de Clopper-Pearson al 95 %.
- **Pruebas principales, no paramétricas:** Fisher por pares con corrección de Holm (3 comparaciones por factor) y permutación estratificada (se baraja el acierto dentro de grupos de 3 corridas con el mismo bloque y los mismos otros dos factores; 20,000 permutaciones; semilla 42). Suponen intercambiabilidad bajo la hipótesis nula. No hay asignación aleatoria de tratamientos, porque todos se aplican en todos los bloques; lo aleatorizado fue el orden de las corridas.
- **Modelo:** regresión logística con one-hot y penalización L2, **exploratoria y descriptiva** (D-21, `analisis/logistica.py`): los tres modelos, términos modelo, posición, nivel y bloque sin interacción, referencias `phi4-mini`, inicio, 4,000 y bloque 1, y C = 1 como principal con 0.1, 10 y 1000 como sensibilidad. Sustituye el plan bayesiano o de Firth de D-19.
- **Cobertura:** por celda, cuántas corridas son válidas, `no_alcanzo_nivel` o `rechazo_seguridad`.
- **Sensibilidad hecha:** formato numérico (D-20) y sin el bloque 4; la posición lograda se verificó de forma descriptiva. Respuestas finales vacías o cortadas: ninguna en las 135 válidas. **No hechas (D-23):** tema y `contexto_final`
- **Descartado:** ANOVA y pruebas paramétricas, medida cuantitativa, chi-cuadrado como prueba principal, interacción triple, imputación de corridas inválidas y el enfoque bayesiano o Firth como análisis principal (D-19 y D-21).
- **Verificación de supuestos:** del diseño: balance (5 por celda), orden sin deriva evidente (5, 6 y 8 fallos por tercio), posición lograda (inicio, mitad y final no se solapan), independencia solo en parte (11 de los 19 fallos están en el bloque 4) y medición (2 de 19 fallos pasan a acierto con el criterio ampliado). Los supuestos paramétricos no se pueden comprobar con respuesta binaria y 19 fallos, y esa es la razón de usar pruebas no paramétricas.
Fuentes del diseño: factorial completo con réplicas, Montgomery y Runger (2018, p. 378) y el «Capítulo 6: Diseños factoriales con tres factores» del material del curso (sin autor indicado, pp. 1 a 3 y 6 a 7); aleatorización y bloques completos, Montgomery y Runger (2018, pp. 353 y 368 a 369); los supuestos del ANOVA que se descartan (normalidad, independencia y varianza constante) están en las pp. 361 a 363.

### Tabla de supuestos

| Supuesto | Cómo se verificó | Resultado | Qué se hizo |
|---|---|---|---|
| Balance | Conteo por celda (`descriptivo.py`) | 5 corridas válidas en cada una de las 27 celdas (135 de 135) | Nada |
| Medición válida | Estado de cada corrida (`final_D14.csv`) | 4 filas `invalida_tecnica`, reintentadas; todas las celdas cerraron como válidas | Reintento acotado (D-18) |
| Aleatorización, sin deriva de la máquina | Fallos por tercio del orden en el bloque (`eda.py`) | 5, 6 y 8 fallos de 45; sin deriva evidente, sin prueba formal por falta de potencia | Se declara como límite |
| El tratamiento se aplicó como se planeó | Fracción del nivel en que quedó el dato (`posicion_lograda.py`) | Inicio 0.01 a 0.09, mitad 0.50 a 0.59 y final 0.85 a 0.94: no se solapan; en 2 de 45 corridas de "final" el dato superó el nivel | Se declara; no se usó como covariable (D-23) |
| Independencia entre corridas | Fallos por bloque (`eda.py`) | 1, 1, 1, 11 y 5: las corridas de un mismo dato se parecen; se cumple en parte | Permutación estratificada por bloque; análisis sin el bloque 4 |
| Bloque sin interacción con el modelo | Fallos por bloque y modelo (`eda.py`) | En el bloque 4 fallaron llama (5 de 9) y phi4-mini (6 de 9); gemma 0 | Descriptivo: con una observación por celda y bloque no hay prueba formal |
| Tema sin confundirse con la posición | Fallos por tema (`eda.py`) | Geografía 6 de 22; el tema no quedó parejo entre posiciones (D-14) | No se hizo (D-23): tema como covariable |
| Criterio de acierto consistente | Criterio ampliado de formato (`sensibilidad_formato.py`, `sensibilidad_ampliado.py`) | 2 de 19 fallos pasan a acierto; gemma frente a llama pasa de p ajustado 0.024 a 0.052 | Se reporta como sensibilidad (D-20, D-21) |
| Sin separación completa | Celdas con 0 fallos | `gemma3:4b` no falla en ninguna de sus 9 celdas | Pruebas exactas y de permutación; la logística exploratoria con penalización L2 (D-21) |
| Normalidad y varianza constante | No se pueden comprobar | La respuesta es 0/1: su varianza es p(1 - p) y depende de la media (0 en gemma, 0.13 en llama, 0.20 en phi4-mini) | Se descartan las pruebas paramétricas (D-21) |
| Intercambiabilidad dentro de cada grupo de 3 corridas (la exige la permutación) | No verificable | Se supone bajo la hipótesis nula; todos los tratamientos están en todos los bloques y el orden fue aleatorio | Se declara en D-21 |
| Potencia suficiente | Intervalos de Clopper-Pearson | Con 17 a 19 fallos solo se detectan diferencias grandes | "No se detecta efecto" no equivale a "no hay efecto" |


## 10. Límites
- Cinco réplicas por celda dan poca potencia; la interacción triple probablemente no es estimable.
- Con 19 fallos en total y ninguno de `gemma3:4b`, el modelo completo de D-19 tiene muchos más parámetros de los que los fallos permiten estimar con holgura; por eso D-21 lo simplifica (sin interacción, con penalización L2) y lo declara exploratorio.
- Las corridas inválidas rompen el balance de los bloques; en `final_D14` todas las celdas cerraron con resultado válido.
- La posición lograda se aparta de la nominal; se reporta de forma descriptiva y no se usó como covariable (D-23).
- El tema no queda perfectamente balanceado (D-14).
- El tope de 300 tokens puede truncar muchas respuestas en algunos modelos (D-16).
- Cada modelo usa su tokenizador, y las conclusiones se limitan a estos tres modelos y a niveles de hasta 12K.
- El nivel de tokens es nominal; «inicio» es una posición absoluta (turno 2).
- El criterio exacto cuenta como fallo el número correcto con otro formato (2 casos); D-20 lo trata como sensibilidad.
- 4 filas `invalida_tecnica` por `generador_relleno` (todas de `gemma3:4b`) tienen causa no determinada, porque el error no se guarda (D-18).

## 11. Estado de la ejecución (2026-11-05)
`final_D14` está completo: 135 celdas con resultado válido y 139 filas en el CSV (4 filas técnicas inválidas conservadas como historial). Hay 19 fallos: `llama3.2:3b` 7, `phi4-mini` 12, `gemma3:4b` 0. Las pruebas (Fisher por pares con Holm, permutación estratificada y sensibilidades) y sus resultados están en el README, sección "Análisis estadístico", y en D-21. Resumen: el modelo parece importar, pero la evidencia depende en buena parte del bloque 4; la posición y el nivel no muestran efecto detectable hasta 12K tokens, con poca potencia.

## 12. Pendiente
- Etiquetado terminado por los dos; kappa de Cohen 0.089 (4 de 19 coincidencias, 2 de ellas fijadas por la regla de F003 y F004): acuerdo apenas por encima del azar. Falta acordar la etiqueta de los 15 desacuerdos (`etiquetado/consenso.csv`) y registrar la decisión (D-24).
- Sensibilidades de D-19 no hechas (D-23): tema y `contexto_final`.