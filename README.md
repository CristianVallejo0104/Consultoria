# Evaluador de Confiabilidad de LLMs en Conversaciones Largas

Sistema que evalúa en qué punto los modelos de lenguaje locales dejan de retener un dato inventado, según la posición del dato, el nivel de longitud en tokens y el modelo (fenómeno "lost in the middle"). Proyecto de Consultoría e Investigación, Universidad Santo Tomás.

**Estado (3 de noviembre de 2026):**
El análisis estadístico principal es no paramétrico y ya está ejecutado (D-21, sección "Análisis estadístico"). **Pendiente:** el etiquetado de Juan Pablo y el kappa. La regresión logística exploratoria con one-hot ya está ajustada (D-21, `analisis/logistica.py`). Laya y los agentes planeados en D-08 quedaron fuera del alcance (D-22), y el Diseño B con modelos en la nube no se ejecutó (D-23).

## Problema y contraparte

### Problema

Estudiantes y profesionales de estadística usan modelos de lenguaje locales (Ollama) como apoyo en análisis de datos, cálculos y consultas técnicas. Hoy no existe una forma sistemática de saber en qué punto de una conversación larga el modelo deja de ser confiable, lo que puede llevar a decisiones basadas en respuestas que el modelo ya olvidó o inventó.

### Contraparte metodológica

Como contraparte, el equipo eligió una IA de gran capacidad que revisa si los procedimientos y los prompts del proyecto tienen sentido (D-12). Se usó Claude Opus 5.5 en un chat sin memoria, sin conectores y con la búsqueda web desactivada, cargando el código y el registro de decisiones sin los resultados del piloto. Los hallazgos se contrastaron con los del equipo: de 10 hallazgos, 4 ya se conocían, 1 en parte, 4 eran nuevos y 1 era incorrecto. Alternativas descartadas: contraparte recomendadora (necesita resultados con más réplicas) y una segunda contraparte de otra familia de modelos (aplazada por costo y tiempo). Límite: la IA es de la misma familia que el asistente que ayudó a desarrollar el proyecto, así que su coincidencia no equivale a verificación independiente. Registro en `docs/contraparte/`.

### Por qué no usar herramientas de evaluación existentes

G-Eval (Liu et al., 2023) usa un modelo de lenguaje como juez para calificar la calidad de un texto, y RAGAS (Es et al., 2023) evalúa sistemas RAG sobre tripletas (pregunta, contexto recuperado, respuesta). Ninguno mide la **retención de información a lo largo de una conversación de varios turnos**, y RAG genera con documentos recuperados, algo que aquí no existe porque el dato viene de la propia conversación (D-09). Este proyecto mide retención con datos inventados que el modelo no puede conocer de su entrenamiento, evaluación determinista (sin modelo juez) y ejecución local reproducible en cuanto al diseño.

*(Nota: para verificar la calidad del texto del generador de relleno se usa un LLM juez de forma exploratoria, ver "Calidad del texto de relleno". La medición de retención sigue siendo 100 % determinista.)*

## Línea base: cómo se hace sin el agente

Sin esta herramienta, una persona tendría que:
1. Abrir Ollama y escribir una conversación larga a mano.
2. Insertar un dato en algún punto.
3. Seguir conversando y, al final, preguntar por el dato.
4. Anotar si acertó.
5. Repetir para cada modelo, posición y longitud.

El equipo estimó entre 2 y 3 horas por combinación, sin registros sistemáticos. Con el sistema, las 9 pruebas del primer corte (3 modelos × 3 longitudes) tomaron unos 45 minutos y generaron reportes automáticos.

## Cómo funciona

Hay tres piezas distintas:

1. **Agente CrewAI (orquestador).** Modelo `qwen2.5:1.5b`, temperatura 0.0. Es la entrada interactiva: el modo interactivo pide modelo, posición y nivel por consola, los valida en Python y arma una tarea literal con esos valores; el agente llama a la herramienta `evaluar_retencion` con los parámetros exactos y redacta la respuesta final. No interpreta lenguaje libre. No escribe la conversación ni dirige las corridas masivas (D-08).
2. **Núcleo en Python.** La función `ejecutar_evaluacion()` ejecuta la conversación turno a turno y verifica el resultado de forma determinista. Las corridas masivas la llaman directamente desde `correr_experimento.py`, sin pasar por el agente.
3. **Generador de relleno.** El mismo `qwen2.5:1.5b`, vía Ollama, escribe los mensajes del "usuario" en los turnos que no llevan el dato clave. Los modelos evaluados son de empresas distintas a la del orquestador para evitar sesgo de autopreferencia.

Flujo de una corrida:
1. El runner toma un bloque y los 27 tratamientos (modelo × posición × nivel) en un orden aleatorio reproducible.
2. Se inicia una conversación con el modelo evaluado.
3. En cada turno, el generador de relleno escribe el mensaje del usuario.
4. En el turno que indica la posición (inicio: 2.º turno; mitad: al cruzar el 50 % del nivel; final: al cruzar el 85 %) se inserta un dato inventado y la conversación cambia de tema. El dato lo determina el bloque (banco de 5 datos) y el tema se asigna por rotación (6 temas).
5. La conversación sigue hasta que el contexto alcanza el nivel (4,000, 8,000 o 12,000 tokens); luego se pregunta por el dato.
6. Se verifica si la cadena exacta aparece en la respuesta, sin negación.
7. Se guardan el JSON y el TXT de la corrida en `resultados/<config>/` y una fila en `resultados/<config>.csv`.

## Modelos

Datos verificados con `ollama show` (D-01, D-13).

| Modelo | Empresa | Parámetros | Ventana | Cuantización | Rol |
|---|---|---|---|---|---|
| `phi4-mini` | Microsoft | 3.8B | 131,072 | Q4_K_M | Evaluado (local) |
| `llama3.2:3b` | Meta | 3.2B | 131,072 | Q4_K_M | Evaluado (local) |
| `gemma3:4b` | Google | 4.3B | 131,072 | Q4_K_M | Evaluado (local) |
| `qwen2.5:1.5b` | Alibaba | 1.5B | 32,768 | Q4_K_M | Orquestador y generador de relleno |
| `phi3:mini` | Microsoft | 3.8B | 131,072 | Q4_0 | Solo primer corte (preliminar) |
| `gemma2:2b` | Google | 2.6B | 8,192 | Q4_0 | Solo primer corte (preliminar) |

Un modelo por empresa. `gemma2:2b` se reemplazó por `gemma3:4b` (D-01: su ventana de 8,192 no llega a 12K) y `phi3:mini` por `phi4-mini` (D-13: memoria, tiempo y paridad de cuantización, razón operativa registrada antes de correr datos con el modelo nuevo). Los resultados de los dos modelos reemplazados quedan como preliminares y no entran al análisis final.

**Modelos en la nube (Diseño B, no ejecutado; D-23).** `agente.py` conserva solo Ollama y OpenRouter; se retiraron las ramas de NVIDIA, Groq y Gemini (D-07) tras comprobar que sus planes gratuitos producían corridas inválidas (D-02). `MODELOS_CLOUD` está vacío porque el Diseño B no se ejecutó.

## Parámetros controlados

Constantes al inicio de `agente.py`:

| Constante | Valor | Razón |
|---|---|---|
| `TEMPERATURA` | 0.7 | Igual en todos los modelos evaluados y en el generador de relleno. Sin fijarla, cada proveedor usa la suya (Ollama 0.8, nube ~1.0) y se confunde con el efecto del modelo. Con 0 las réplicas serían casi idénticas. |
| `TEMPERATURA_ORQUESTADOR` | 0.0 | El orquestador solo copia parámetros. |
| `NUM_CTX_OLLAMA` | 16,384 | Evita el truncamiento silencioso de Ollama; debe superar el nivel más alto (12,000). |
| `TIMEOUT_SEGUNDOS` | 600 s | Aplica a todas las llamadas. Sin timeout, `requests` espera indefinidamente. |
| Tope de respuesta | 300 tokens | Común a todos los modelos (D-06). Puede truncar respuestas largas; se registra `done_reason` (D-16). |
| Máximo de turnos | 60 | Si no se alcanza el nivel en 60 turnos, la corrida queda `no_alcanzo_nivel`. |
| `SEMILLA_EXPERIMENTO` | 42 (en `correr_experimento.py`) | Fija el diseño: orden de los tratamientos por bloque, dato y tema. No fija la generación del modelo, a propósito: las réplicas necesitan variabilidad natural (D-15). |

`random.seed(42)` sigue en `agente.py` solo para el modo interactivo; no interviene en las corridas `final_D14`. `top_k` y `top_p` no se fijan: cada modelo usa los suyos.

## Clasificación de las corridas

| Estado | Significado | `acierto` |
|---|---|---|
| `valida` | El modelo respondió | `true` / `false` |
| `invalida_tecnica` | Fallo de API o red (`rate_limit`, `sobrecarga`, `timeout`, `conexion`, `respuesta_inesperada`, `generador_relleno`, `excepcion_interna`) o `no_alcanzo_nivel` | `null` |
| `rechazo_seguridad` | El modelo o el proveedor se negó por política | `null` |

Las corridas inválidas **no** cuentan como "el modelo olvidó el dato". Si cualquier turno falla, la corrida se aborta, porque una conversación con huecos es otro tratamiento (D-11).

**Política de reintentos (D-18).** Una falla técnica externa es reintentable: se repite al relanzar el mismo comando y cada intento queda como fila nueva con la columna `intento`. `no_alcanzo_nivel` no es reintentable, porque depende del tratamiento y no es una falla externa. El runner se detiene tras 3 fallas reintentables seguidas. En el análisis, cada celda se toma de la fila que la cierra.

En `final_D14` hubo 4 filas `invalida_tecnica`, todas con `generador_relleno` y todas de `gemma3:4b`. Las 4 filas corresponden a 3 celdas (bloque 1 mitad 12K, bloque 1 final 4K y bloque 5 inicio 8K); al relanzar, las 3 cerraron como válidas (la de bloque 1 final 4K, en el tercer intento). La causa de las fallas no está determinada: el código descarta el mensaje de la excepción (`detalle_error` queda en `None`). Una hipótesis, sin probar, es el tope de 600 s de la llamada al generador.

Límite conocido: los rechazos de seguridad escritos en texto ("no puedo ayudar con eso") no se detectan automáticamente, y la detección de `rechazo_seguridad` solo existe en las API en la nube.

Campos del CSV (27 columnas): `modelo, posicion, nivel_tokens, replica, estado_final, acierto, turnos_reales, contexto_al_dato, contexto_final, contexto_decreciente, tokens_totales, tiempo_segundos, errores, tema, dato_clave` y, desde D-14, D-16 y D-18, `bloque, orden_en_bloque, indice_dato, indice_tema, done_reason_final, respuesta_final_vacia, contexto_tras_dato, contexto_antes_pregunta, turnos_dato_a_pregunta, dato_sobre_nivel, turnos_relleno_cortados, intento`.

Notas sobre los campos:
- `tokens_prompt` (en el JSON) es la **suma** de los prompts de todas las llamadas (cada turno reenvía el historial); no es la longitud de la conversación.
- `contexto_final` es el `prompt_eval_count` de la llamada de la pregunta final, es decir, el contexto al preguntar. La redacción anterior de D-06 decía "prompt + respuesta" y se corrigió (D-16).
- `contexto_al_dato` se mide antes de insertar el dato y `contexto_tras_dato` al cierre de ese turno.
- `turnos_relleno_cortados` cuenta respuestas del modelo evaluado cortadas por el tope de tokens, no las del generador de relleno.

## Diseño experimental

Factorial completo en bloques completos aleatorizados (D-14, D-15). Detalle y justificación en `docs/DISENO.md`.

- **Factores fijos:** modelo (`phi4-mini`, `llama3.2:3b`, `gemma3:4b`) × posición del dato (inicio, mitad, final) × nivel de tokens (4,000, 8,000, 12,000) = 27 tratamientos.
- **Réplicas y bloques:** 5 réplicas organizadas en 5 bloques completos; el bloque es el dato inventado. Son 135 corridas. Dentro de cada bloque se baraja el orden de los 27 tratamientos con una semilla derivada del bloque (`crc32`, porque el `hash()` de Python cambia entre ejecuciones).
- **Tema:** 6 temas asignados por rotación, `((orden_en_bloque − 1) + bloque) mod 6`, con `orden_en_bloque` contando desde 1. No es un bloque completo, y las corridas por tema no quedan parejas dentro de cada posición del dato (medido sobre el plan: inicio [10, 8, 5, 9, 7, 6], mitad [2, 6, 7, 8, 12, 10], final [10, 8, 10, 6, 4, 7]); se documenta como límite.
- **Respuesta:** acierto binario por cadena exacta, sin negación; sin LLM juez (D-11, D-19).
- **Nivel de tokens:** "5 turnos" no es comparable entre modelos (`phi3:mini` procesó 10,259 tokens en 5 turnos y `gemma2:2b`, 1,903). El nivel es el contexto en la pregunta final (D-06).
- **Justificación:** sigue la estructura de Liu et al. (2023: posición × longitud del contexto × modelo) y de Zhang et al. (2024), formalizada con principios de diseño de experimentos. Nuestra variante inserta el dato dentro de la conversación y no en un documento recuperado. La estructura (factorial completo con réplicas, bloques completos y orden aleatorio) sigue lo que presentan Montgomery y Runger (2018, pp. 353, 368 a 369 y 378) y el modelo de tres factores del material del curso (sin autor indicado, pp. 1 a 3 y 6 a 7).
- **Análisis (D-19, D-20 y D-21):** la respuesta es binaria y con 19 fallos los supuestos paramétricos no se pueden comprobar, así que los resultados principales son no paramétricos.
  - Descriptivo: acierto por celda y por factor con intervalo exacto de Clopper-Pearson al 95 %.
  - Pruebas: Fisher por pares con corrección de Holm (3 comparaciones por factor) y permutación estratificada (se baraja el acierto dentro de grupos de 3 corridas con el mismo bloque y los mismos otros dos factores; 20,000 permutaciones, semilla 42). Se justifican por intercambiabilidad bajo la hipótesis nula, no por una asignación aleatoria de tratamientos.
  - Modelo: regresión logística con one-hot y penalización L2, **exploratoria y descriptiva** (`analisis/logistica.py`): los tres modelos, términos modelo, posición, nivel y bloque sin interacción, referencias `phi4-mini`, inicio, 4,000 y bloque 1, y C = 1 como principal con 0.1, 10 y 1000 como sensibilidad. Reemplaza al plan bayesiano o de Firth de D-19.
  - Sensibilidad (hecha): criterio ampliado de formato (D-20) y sin el bloque 4; la posición lograda del dato se verificó de forma descriptiva. No se hicieron (D-23): tema, `contexto_final` y la posición lograda como covariables. El criterio principal (`verificar_acierto`) no se modifica.
- **Alcance:** el estudio solo dice algo sobre estos tres modelos y los niveles medidos (hasta 12K), no sobre contextos mayores aunque el modelo los soporte.

## Resultados finales (`final_D14`)

**Conteos descriptivos** (las pruebas están en "Análisis estadístico").

| Factor | Nivel | Aciertos |
|---|---|---|
| Modelo | `gemma3:4b` | 45 de 45 (1.000) |
| Modelo | `llama3.2:3b` | 38 de 45 (0.844) |
| Modelo | `phi4-mini` | 33 de 45 (0.733) |
| Posición | inicio | 39 de 45 (0.867) |
| Posición | mitad | 41 de 45 (0.911) |
| Posición | final | 36 de 45 (0.800) |
| Nivel | 4,000 | 40 de 45 (0.889) |
| Nivel | 8,000 | 37 de 45 (0.822) |
| Nivel | 12,000 | 39 de 45 (0.867) |

Observaciones, con cautela:
- Los fallos son de `llama3.2:3b` (7) y `phi4-mini` (12). `gemma3:4b` acertó sus 45 corridas, sus 9 celdas con 5 de 5, lo que genera separación en el modelo logístico (por eso D-21 usa penalización L2 en la logística exploratoria)
- Por bloque (dato inventado) hay 1, 1, 1, 11 y 5 fallos. Más de la mitad está en un solo dato, y por eso el bloque entra como efecto en el modelo.
- Solo 13 de las 27 celdas tienen algún fallo.
- En estos conteos no se ve el patrón clásico de "lost in the middle": la posición mitad tiene el mayor acierto y el nivel no baja de forma ordenada. Con 45 corridas por grupo, diferencias de pocos fallos pueden ser azar; las pruebas están en "Análisis estadístico"
- Dos de los 19 fallos (F003 y F004 en la hoja de etiquetado) contienen el número correcto con coma ("44,295") y el criterio exacto los cuenta como fallo. El análisis de sensibilidad de D-20 los trata aparte.

## Tiempo de ejecución (`final_D14`)

Mediana por corrida, en minutos, de las 135 corridas válidas (`analisis/tiempos.py`):

| Modelo | 4,000 tokens | 8,000 tokens | 12,000 tokens | Suma |
|---|---|---|---|---|
| `gemma3:4b` | 2.7 | 5.5 | 7.8 | 4.20 h |
| `llama3.2:3b` | 2.5 | 5.9 | 9.1 | 4.74 h |
| `phi4-mini` | 4.2 | 9.6 | 17.3 | 8.38 h |

Total de las corridas válidas: 17.31 h (por nivel: 2.38 h a 4K, 5.65 h a 8K y 9.29 h a 12K). El tiempo crece con el nivel en los tres modelos, y `phi4-mini` es el más lento (hasta 28.6 min en una corrida). La causa de esa diferencia no se probó. Límites: medido en una RTX 3050 de 6 GB, con el PC en uso y con cortes manuales durante la ejecución; no incluye los intentos fallidos ni las corridas interrumpidas.


## Análisis estadístico (D-21)

Resultados principales no paramétricos, con respuesta binaria. Todos salen de `analisis/`; ejecuta desde la raíz del proyecto:

```bash
python analisis/descriptivo.py                      # acierto e intervalos de Clopper-Pearson
python analisis/fisher.py                           # Fisher por pares con Holm
python analisis/permutaciones.py                    # permutación estratificada
python analisis/eda.py                              # fallos por bloque, orden y tema
python analisis/posicion_lograda.py                 # dónde quedó realmente el dato
python analisis/sensibilidad_bloque4.py             # sin el bloque 4
PYTHONPATH=. python analisis/sensibilidad_formato.py   # criterio ampliado de formato (D-20)
PYTHONPATH=. python analisis/sensibilidad_ampliado.py  # Fisher y permutación con ese criterio
python analisis/logistica.py                        # regresión logística exploratoria (one-hot, L2)
python analisis/tipos_de_fallo.py                   # tipos de fallo por modelo (un evaluador)
PYTHONPATH=. python analisis/kappa.py               # kappa de Cohen entre las dos hojas de etiquetado
python analisis/graficas.py                         # figuras en analisis/figuras/
```

Los dos scripts de formato necesitan `PYTHONPATH=.` porque importan `agente.py`, que está en la raíz, y `kappa.py` porque importa `preparar_etiquetado.py`.

| Análisis | Modelo | Posición | Nivel |
|---|---|---|---|
| Permutación estratificada, 135 corridas | p ≤ 1/20 001 | 0.21 | 0.67 |
| Sin el bloque 4 (108 corridas) | 0.035 | 0.25 | 0.71 |
| Criterio ampliado (17 fallos) | 0.00095 | 0.38 | 0.44 |

Fisher por pares con Holm (modelo): gemma frente a phi4-mini 0.0006 (sin el bloque 4, 0.075; con el criterio ampliado, 0.0015); gemma frente a llama 0.024 (sin el bloque 4, 0.52; con el criterio ampliado, 0.052); llama frente a phi4-mini 0.30. En posición y nivel ningún p ajustado baja de 0.69.

Lectura: el modelo parece importar, pero la evidencia depende en buena parte de un solo dato difícil (el bloque 4), y la diferencia entre `gemma3:4b` y `llama3.2:3b` depende del criterio de formato. La posición y el nivel no muestran efecto detectable hasta 12K tokens. Con 17 a 19 fallos la potencia es baja: "no se detecta efecto" no equivale a "no hay efecto". Las pruebas suponen intercambiabilidad de las corridas dentro de cada grupo, y las corridas de un mismo dato se parecen (11 de los 19 fallos están en el bloque 4).

Regresión logística exploratoria (one-hot, penalización L2; razones de momios de acierto frente a `phi4-mini`, inicio, 4,000 y bloque 1; de C = 1 a C = 1000): `gemma3:4b` pasa de 7.29 a 5,027, es decir, crece sin tope al quitar la penalización (es la separación, y el valor con C = 1 lo fija la penalización); `llama3.2:3b` de 1.47 a 2.87; el bloque 4 de 0.16 a 0.02, el efecto más grande y de dirección constante (el dato 44295 fue mucho más difícil); en posición y nivel la dirección se mantiene (final y 8,000 por debajo de la referencia, mitad por encima) pero la magnitud cambia con la penalización, y las pruebas exactas no detectan efecto en ninguno de los dos. No hay errores estándar ni intervalos, la penalización encoge las razones hacia 1 y son 10 parámetros para 19 fallos: describe estos datos y no se generaliza.

## Etiquetado de fallos y kappa

Los 19 fallos se clasifican a mano con `docs/guia_etiquetado.md` (6 categorías: alucinación, admisión, negación de capacidad, alucinación narrativa, desvío y otra/duda). `preparar_etiquetado.py` carga los fallos de `resultados/final_D14`, los baraja con semilla 42 y escribe una hoja sin modelo, posición ni nivel (`etiquetado/hoja_ciega.csv`) y una clave aparte (`etiquetado/clave.csv`). Cada integrante etiqueta su propia copia y el acuerdo se mide con `kappa_cohen`.

- **Estado:** Cristian y Juan Pablo terminaron sus 19 etiquetas; el kappa no se ha calculado.
- **Reglas de borde, acordadas por el equipo:** F003 y F004 (número correcto con otro formato) van en "otra/duda" con la nota "variante de formato". "No recuerdo haber mencionado ese número" va en "admisión" (confirmado por Juan Pablo antes de etiquetar).
- **Cegamiento:** la hoja es ciega respecto a modelo, posición y nivel, pero algunas respuestas nombran al modelo ("como Phi, de Microsoft"). Además, `hoja_cristian.csv` y `clave.csv` están en el repositorio, así que la independencia entre etiquetadores se protegió por acuerdo y no técnicamente.
- **Verificación de `kappa_cohen`:** con un caso calculado a mano (50 casos, 35 coincidencias, acuerdo esperado por azar 0.5) dio 0.4, y con la misma lista contra sí misma dio 1.0.
- **Límite:** con 19 casos, un solo desacuerdo mueve mucho el kappa.

## Calidad del texto de relleno

`evaluar_calidad_texto.py` evalúa naturalidad, coherencia e interés de los turnos del "usuario" con `qwen2.5:1.5b` como LLM juez (dimensiones de Mehri y Eskenazi, 2020; mecanismo de G-Eval; D-04). Es exploratorio y **no está validado contra criterio humano**: sus notas no se usan en el análisis final hasta validarlas. Hallazgo previo: el juez no penalizó de forma consistente los turnos cortados a mitad de frase, cuyo origen (un límite de 200 caracteres) ya se corrigió.

## Decisiones de diseño

Cada decisión se documenta con su alternativa descartada. Registro completo en `docs/decisiones.md`.

- **Agente CrewAI con una herramienta.** El agente es una capa delgada para uso interactivo. La lógica del experimento es código determinista. Alternativa descartada: tres herramientas separadas, porque pasar el texto de la conversación por el agente entre cada una saturaba su contexto.
- **Agentes solo donde hay juicio de lenguaje (D-08).** No hay agente selector local/nube (un diccionario lo resuelve) ni agente para verificar supuestos estadísticos (código plano). Se planearon un verificador de checkpoints intermedios, un clasificador de tipo de fallo y un analista de hallazgos, y **no se implementaron** (D-22): el etiquetado manual con kappa cumple el papel del clasificador, el análisis es determinista y los puntos de control dentro de la conversación se dejaron como trabajo futuro (D-14).
- **CrewAI.** Alternativas descartadas: LangChain (más componentes para el mismo formato ReAct), LangGraph (sobrediseño para un flujo lineal) y AutoGen (complejidad sin beneficio).
- **Datos inventados, no conocimiento general (D-11).** La primera versión usaba "la capital de Australia es Canberra" y todos acertaban por conocimiento de entrenamiento.
- **Evaluación determinista, no LLM juez, para retención (D-09, D-11).** Alternativa descartada: otro modelo como evaluador (ruido y circularidad).
- **Manejo de errores unificado (D-11).** Un solo punto (`consultar_modelo`) convierte errores de red en corridas inválidas tipadas. Alternativa descartada: copiar el parche en cada rama.
- **D-01:** `gemma2:2b` → `gemma3:4b`, por la ventana de contexto.
- **D-02:** pagar créditos de OpenRouter (~US$20) en lugar de depender de planes gratuitos, que producían corridas inválidas (Groq: límites de 8,000 y 1,000 tokens por minuto según el modelo; NVIDIA: ~7 min por corrida de 5 turnos y un endpoint anunciado como deprecado; Gemini: 503 intermitentes; OpenRouter `:free`: límites propios).
- **D-03:** Laya explorado y pospuesto como clasificador de tipo de fallo: zero-shot rinde 38 % en 5 categorías (frente a 20 % de azar uniforme, con n = 13) y falta un conjunto de fallos reales etiquetados. Con 19 fallos no se entrena ni se evalúa en este proyecto (D-22); queda como trabajo futuro con más corridas y más fallos etiquetados.
- **D-04:** evaluador de calidad de texto con LLM juez (exploratorio).
- **D-05:** el diseño factorial se justifica con la literatura del propio campo (Liu et al.; Zhang et al.).
- **D-06:** migración de turnos a niveles de tokens (4K, 8K, 12K).
- **D-07:** se retiran del código los proveedores cloud gratuitos.
- **D-09:** RAG, G-Eval y RAGAS se contrastan con el proyecto, pero no se usan para medir retención.
- **D-10:** selección de modelos y roles (un modelo por empresa).
- **D-12:** contraparte metodológica y su contraste con los hallazgos del equipo.
- **D-13:** `phi3:mini` → `phi4-mini`.
- **D-14 y D-15:** factorial en bloques, orden aleatorio, dato por bloque y tema por rotación; la semilla solo fija el diseño, no la generación de Ollama.
- **D-16:** guardado determinista por corrida y campos de registro de validez.
- **D-17:** revisión con agentes de Claude Code y reparto de trabajo (ver "Uso de IA en el desarrollo").
- **D-18:** corridas inválidas: reintento manual acotado a fallas técnicas externas y parada del runner tras 3 seguidas. Alternativas descartadas: no reintentar nunca y reintentar sin límite.
- **D-19:** medida de respuesta y plan de análisis (ver "Diseño experimental"). Alternativas descartadas: ANOVA sobre el acierto 0/1, chi-cuadrado como prueba principal, modelo sin bloque, interacción triple e imputación de corridas inválidas.
- **D-20:** análisis de sensibilidad por variantes de formato numérico. Alternativas descartadas: modificar `verificar_acierto` y decidir caso por caso a mano.
- **D-21:** análisis no paramétrico como resultado principal y regresión logística con one-hot como modelo exploratorio. Alternativas descartadas: ANOVA y pruebas paramétricas, medida cuantitativa, enfoque bayesiano o Firth como principal, y regresión sin penalizar.
- **D-22:** Laya y los agentes planeados en D-08 quedan fuera del alcance. Alternativas descartadas: entrenar a Laya con 19 fallos, Laya zero-shot y un clasificador automático con LLM.
- **D-23:** cierre de alcance: el Diseño B con modelos en la nube y otros pendientes no se ejecutaron; quedan como trabajo futuro. Alternativas descartadas: ejecutar el Diseño B completo y una prueba parcial con un solo modelo en la nube. 

## Uso de IA en el desarrollo

Declarado según la rúbrica y registrado en D-17:

- **Decisiones de diseño:** del equipo (semilla que solo fija el diseño; tema por posición en el orden; reemplazos de modelos; contraparte metodológica; categorías del etiquetado y sus reglas de borde).
- **Asistente de IA en chat (Claude):** explicó el porqué de cada paso antes del código, redactó la función `orden_del_bloque` (que Cristian tecleó, probó y puede explicar línea por línea), las especificaciones de cada tarea y las pruebas de verificación.
- **Claude Code, con permiso por edición y sin commits:** escribió el cambio mecánico en `agente.py` y `correr_experimento.py` (parámetros `indice_dato` e `indice_tema`, configuración `final_D14`, bucle por bloques, columnas nuevas, guardado determinista, manejo de errores del runner, campos de registro, reintentos de D-18).
- **Asistente de IA en chat, fase de análisis y etiquetado:** redactó la función `kappa_cohen` (probada con un caso calculado a mano), los borradores de las entradas D-20 a D-23, el script que escribió las etiquetas de Cristian en su hoja (las categorías las decidió Cristian; el asistente solo mostró los textos y pasó los números a CSV sin sugerir categorías) y los comandos de conteo por terminal usados en "Resultados finales".
- **Scripts de `analisis/`** (`descriptivo.py`, `fisher.py`, `eda.py`, `graficas.py`, `posicion_lograda.py`, `sensibilidad_formato.py`, `permutaciones.py`, `sensibilidad_bloque4.py`, `sensibilidad_ampliado.py`, `tiempos.py`, `logistica.py`, `tipos_de_fallo.py`): los redactó el asistente de IA en chat; Cristian los tecleó, los ejecutó y contrastó sus salidas con las del asistente. Los métodos (no paramétrico, one-hot y regresión logística) los decidió el equipo y están registrados en D-21.
- **Sesión de Claude en la nube, solo lectura:** auditó el repositorio, repitió los análisis y propuso preguntas de sustentación. Sus hallazgos se contrastaron con el código y las salidas antes de aplicar cambios: corrigieron una frase de D-21 sobre el criterio de formato y la razón para descartar Freeman-Halton. Es de la misma familia que el asistente del chat, así que su coincidencia no es verificación independiente (D-12).
- **Subagentes de revisión de solo lectura** (`revisor-codigo-python` y `consultor-estadistico`): auditaron el código antes de las corridas. Sus resúmenes se contrastaron con el código y con las pruebas ejecutadas.
- **Verificación humana:** cada diff se revisó antes del commit y se ejecutaron pruebas con Ollama.
- **Sesión de Claude en la nube, video del proyecto:** generó la animación (index.html y guion) a partir del repositorio, sin editar archivos del proyecto. Pendiente: contrastar cada cifra con el README y con la salida de los scripts.
- **Claude Code, sesión de Juan Pablo (4 y 5 de noviembre), con permiso por cada cambio:** a pedido de Juan Pablo hizo los commits y los push de esta sesión, cada uno después de describirle los cambios y con su aprobación, y solo con los archivos nombrados; ejecutó `analisis/kappa.py` una vez subidas las dos hojas. Además escribió `analisis/kappa.py` (probado con un caso calculado a mano: 4 casos, 3 coincidencias, kappa 0.5), volvió a ejecutar los scripts de `analisis/` para contrastar las cifras del README y de DISENO.md (coinciden; `logistica.py` no se pudo ejecutar porque `scikit-learn` no estaba instalado en ese entorno), cerró con referencia a D-22 y D-23 las notas pendientes de D-02, D-03 y D-13, y generó una página con el diagrama del diseño para la exposición (cubo 3 × 3 × 3, 27 tratamientos × 5 bloques con su orden y el flujo de una corrida), con los datos de `final_D14.csv`; la página no está en el repositorio. En el etiquetado de Juan Pablo mostró las respuestas de `hoja_juan.csv` una por una y pasó al CSV los números que él decidió, sin sugerir categorías ni comentar las respuestas; solo le recordó las reglas de borde ya acordadas cuando aplicaban (F003 y F004). En la revisión inicial del repositorio, un comando de conteo imprimió por error las categorías de `hoja_cristian.csv` en la salida de la sesión, antes de que Juan Pablo etiquetara.
- **Distribución del trabajo entre integrantes:** el proyecto lo hicieron en equipo Cristian Vallejo y Juan Pablo Tibamoso. Las ideas, los cambios de diseño y las decisiones se discutieron y se tomaron entre los dos en varias sesiones, siguiendo también las indicaciones y sugerencias del profesor.
  - **Trabajo conjunto:** casi todo se hizo juntos en el computador de Cristian, que corre los modelos más rápido. Ahí se ejecutaron las corridas y desde ahí se subieron los commits. Por eso casi todos los commits aparecen bajo el usuario de git de Cristian, aunque el trabajo fue de los dos.
  - **Código:** lo escribieron los dos; Cristian escribió la mayor parte.
  - **Análisis, fuentes y entregas del curso:** los hicieron entre los dos.
  - **Etiquetado:** cada uno etiquetó por separado sus 19 fallos. Juan Pablo confirmó las reglas de borde, calculó el kappa y volvió a ejecutar los scripts de análisis para contrastar las cifras de la documentación.

## Guardarraíles

- No genera conclusiones estadísticas ni decide qué modelo es "mejor": ejecuta pruebas y reporta.
- No accede a datos personales ni confidenciales.
- No modifica los modelos evaluados.
- La verificación de retención es determinista: no se usa un LLM como evaluador para esa parte.

## Iteraciones del diseño

- **v1, párrafos estáticos:** el dato entre texto de relleno. Todos los modelos acertaban.
- **v2, conversación con preguntas fijas:** las preguntas no seguían el hilo.
- **v3, conversación natural generada:** `qwen2.5` escribe los mensajes del usuario según las respuestas del modelo.
- **v4, dato inventado con banco rotativo:** los datos de conocimiento general medían conocimiento previo, no retención.
- **v5, orquestador liviano y temporizador:** `qwen2.5:1.5b` (986 MB) en lugar de `qwen2.5` (4.7 GB), para correr con 8 GB de RAM.
- **v6, control de variables y errores tipados:** temperatura fija, timeout, clasificación de corridas inválidas, detección de rechazos de seguridad, banco reescrito con frases neutras ("número de expediente") porque "código secreto" activaba filtros de seguridad.
- **v7, niveles de tokens y diseño en bloques:** longitud medida en tokens (D-06), factorial en bloques con orden aleatorio, dato por bloque y tema por rotación (D-14, D-15), y registro de validez por corrida (D-16).
- **v8, reintentos y análisis planeado:** reintento acotado de fallas técnicas (D-18), plan de análisis (D-19) y sensibilidad por formato (D-20).

## Herramientas exploratorias (fuera del núcleo de `agente.py`)

- **`evaluar_calidad_texto.py`:** evaluador de calidad conversacional del generador de relleno. Vive en este repositorio. Ver D-04.
- **Exploración de Laya** (clasificador de tipo de fallo): se probó en un entorno y carpeta separados (`venv-laya`, fuera de este repositorio, por conflicto de dependencias con `torch`/`transformers`), leyendo los JSON ya generados en `resultados/json/`. Pospuesto por falta de datos de fallo reales. Ver D-03. El código de esa exploración no está versionado aquí.

## Resultados preliminares

Son exploratorios, con una réplica por combinación, y no permiten inferencia estadística.

### Primer corte (septiembre 2026)

9 pruebas, dato en posición *inicio*, longitud en turnos. Las cifras vienen del informe del primer corte (Cuadro 3) y no se reproducen con los JSON del repositorio (el de `phi3:mini` a 5 turnos da 10,304 tokens totales y 2,221 de respuesta), así que qué mide esa columna no está verificado.

| Modelo | Turnos | Tokens | Tiempo | Resultado |
|---|---|---|---|---|
| gemma2:2b | 5 | 1,903 | 1:40 | Acierto |
| gemma2:2b | 10 | 2,224 | ~3:00 | Acierto |
| gemma2:2b | 20 | 9,548 | 6:30 | Fallo |
| phi3:mini | 5 | 10,259 | 9:00 | Fallo |
| phi3:mini | 10 | 4,474 | 5:00 | Fallo |
| phi3:mini | 20 | 8,889 | 11:33 | Fallo |
| llama3.2:3b | 5 | 1,728 | 0:58 | Fallo |
| llama3.2:3b | 10 | 4,361 | 2:40 | Fallo |
| llama3.2:3b | 20 | 10,605 | 6:30 | Fallo |

Observaciones:
1. `gemma2:2b`, con la ventana más pequeña (8,192), fue el único que acertó; falló a los 20 turnos. La ventana nominal no predijo la retención.
2. `phi3:mini` falló desde 5 turnos y generó respuestas muy largas. Se plantea como **hipótesis** (no probada) que esa longitud dispersa la atención.
3. Parte de los fallos de `llama3.2:3b` fueron rechazos de seguridad ante datos que sonaban sensibles, no pérdida de retención. Ese sesgo se corrigió reescribiendo el banco de datos.
4. Se observaron cuatro tipos de fallo: alucinación (inventa un dato), admisión ("no tengo esa información"), negación de capacidad ("no puedo recordar conversaciones") y alucinación narrativa (`phi3:mini` convirtió un código en una leyenda cósmica). Son observación propia; la literatura da el marco pero no las nombra (D-03).
5. El orquestador se equivoca con listas largas de modelos (confunde nombres o omite parámetros); una Task literal lo reduce pero no lo elimina.
6. Pruebas manuales posteriores con `gemma3:4b` (fuera del análisis): 5 y 10 turnos terminaron con un contexto de ~3K tokens en ambos casos, lo que confirma que "turnos" no mide longitud.

### Piloto de `phi4-mini` (2 de octubre de 2026, D-13)

Posición *mitad*, 1 réplica por nivel, 3 corridas válidas. El fallo a 4K no se interpreta con una sola réplica.

| Nivel | Resultado | `contexto_final` | Turnos | Tiempo |
|---|---|---|---|---|
| 4K | Fallo | 4,260 | 12 | 241 s |
| 8K | Acierto | 8,115 | 23 | 523 s |
| 12K | Acierto | 12,328 | 37 | 915 s |

El piloto de `phi4-mini` tardó 28.0 min en total, frente a 49.3 min de `phi3:mini` en el piloto equivalente (−43 %).

## Requisitos

- Python 3.12
- [Ollama](https://ollama.ai)
- Memoria: con `num_ctx` 16,384, `phi4-mini` ocupó 4.8 GB en `ollama ps` (9–15 % en CPU) y `phi3:mini` 9.0 GB (D-13). El requisito de 8 GB de RAM del diseño original sigue abierto para los otros dos modelos.
- GPU opcional. Probado con 6 GB de VRAM (RTX 3050); los modelos que no caben en la GPU se reparten entre GPU y CPU, más lento pero con los mismos resultados.
- Probado en Ubuntu 24.04 con Python 3.12. No se probó en Windows: `requirements.txt` viene de Linux e incluye paquetes como `uvloop` que, hasta donde sé, no existen para Windows. Si la instalación falla ahí, instala primero `crewai`, `requests` y `python-dotenv` y deja que pip resuelva el resto.

## Instalación

```bash
git clone https://github.com/CristianVallejo0104/Consultoria.git
cd Consultoria

python3 -m venv venv                # Linux/Mac
python -m venv venv                 # Windows

source venv/bin/activate            # Linux/Mac
venv\Scripts\activate               # Windows

pip install -r requirements.txt

ollama pull qwen2.5:1.5b            # orquestador y generador de relleno
ollama pull phi4-mini
ollama pull llama3.2:3b
ollama pull gemma3:4b
# Solo para reproducir el primer corte (preliminar):
ollama pull phi3:mini
ollama pull gemma2:2b
```

## Configuración de modelos en la nube (opcional)

El núcleo local no necesita claves. Para evaluar modelos en la nube, copia `.env.example` a `.env` y completa solo lo que vayas a usar:

```bash
cp .env.example .env
```

Variable usada por el código actual: `OPENROUTER_API_KEY`. **Nunca subas `.env` al repositorio** (está en `.gitignore`). Los modelos en la nube cuestan dinero o tienen límites de tasa: revisa las condiciones de tu proveedor antes de lanzar corridas masivas.

## Uso

**1. Corridas del diseño (runner):**

```bash
python correr_experimento.py              # sin argumento: lista las configuraciones disponibles
python correr_experimento.py final_D14    # las 135 corridas del diseño
```

- Configuraciones: `final_D14` (diseño final, ya completo), y `preliminares_tokens` y `piloto_phi4` (primer corte y piloto, ya hechas: **no volver a correrlas**, sus CSV tienen 15 columnas y quedarían desalineados).
- Salidas: `resultados/<config>.csv` (una fila por corrida), `resultados/<config>/` (JSON y TXT por corrida, con nombre determinista como `llama3_2_3b_mitad_4000tok_01`) y `resultados/<config>_errores.log` (errores de guardado).
- Para retomar una corrida cortada, vuelve a ejecutar el mismo comando: `ya_hechas` omite las celdas con resultado y repite las que solo tienen fallas técnicas externas (D-18). No cambies `SEMILLA_EXPERIMENTO` ni las listas de modelos, posiciones o niveles entre retomas.
- Un reintento sobrescribe el JSON y el TXT del intento anterior (nombre determinista); el CSV conserva todos los intentos.
- Si lo lanzas en segundo plano con `nohup`, la salida va al archivo de log y no a la pantalla. Para verla en vivo usa `python -u` con `| tee -a`.

**2. Una sola corrida, sin CrewAI:**

```bash
python -c "from agente import ejecutar_evaluacion as e, guardar_resultado as g; r = e('gemma3:4b','mitad',4000,indice_dato=0,indice_tema=0); g(r, carpeta_salida='resultados/prueba', replica=1); print(r['estado_final'], r['acierto'])"
```

`ejecutar_evaluacion()` devuelve un diccionario; el nivel debe ser 4000, 8000 o 12000. Sin `indice_dato` ni `indice_tema`, dato y tema se sortean.

**3. Interactivo con el agente CrewAI:**

```bash
python3 agente.py
```

El modo interactivo imprime los modelos, posiciones y niveles de tokens permitidos y pide tres datos: modelo, posición del dato y nivel de tokens; el agente orquestador llama a la herramienta con esos valores. Guarda el resultado en `resultados/txt/` y `resultados/json/`. Prueba del 3 de noviembre de 2026: `gemma3:4b`, mitad, 8,000 tokens → acierto en 349.5 s, coherente con la mediana de esa celda en `final_D14`.

**4. Hojas de etiquetado y kappa:**

```bash
python -c "from preparar_etiquetado import cargar_fallos, escribir_hojas; escribir_hojas(cargar_fallos('resultados/final_D14'), 'etiquetado')"
```

Genera `hoja_ciega.csv` y `clave.csv` en `etiquetado/`. `kappa_cohen(etiquetas_a, etiquetas_b)` en el mismo archivo calcula el acuerdo entre dos listas de etiquetas. `PYTHONPATH=. python analisis/kappa.py` revisa primero que `hoja_juan.csv` tenga una categoría del 1 al 6 en cada fila (si falla, no muestra nada de la otra hoja) y luego imprime el kappa, la tabla cruzada y los desacuerdos.

**5. Evaluar la calidad del texto del generador de relleno** (exploratorio, no forma parte del análisis final aún):

```bash
python3 evaluar_calidad_texto.py
```

Evalúa una muestra de `resultados/txt/` con `qwen2.5:1.5b` como LLM juez y guarda en `resultados/calidad_texto/` (no versionado). Ver limitaciones en `docs/decisiones.md`.

**6. Con un agente de terminal (Claude Code u opencode):** ver la sección siguiente.

## Usar el proyecto con Claude Code u opencode

El repositorio incluye dos plantillas equivalentes de un agente **operador**:

- `agente_eval_claude.md`: para Claude Code
- `agente_eval_open.md`: para opencode

El agente corre las evaluaciones, revisa Ollama y resume los JSON. **No mide ni decide si un modelo acertó**: eso lo hace siempre el código Python, para que el resultado no dependa de qué agente lo lance. Ambas herramientas leen `CLAUDE.md`, que contiene el contexto y las decisiones del proyecto; opencode lo usa como respaldo de `AGENTS.md`, por eso no debe crearse un `AGENTS.md`.

Cada herramienta busca sus agentes en una carpeta propia, así que hay que copiar la plantilla desde la raíz del proyecto:

```bash
mkdir -p .claude/agents .opencode/agents
cp agente_eval_claude.md .claude/agents/evaluador-retencion.md
cp agente_eval_open.md .opencode/agents/evaluador-retencion.md
```

Después:
- Claude Code: ejecuta `claude` y pide *"Usa el subagente evaluador-retencion para correr gemma3:4b en mitad con nivel 4000"*.
- opencode: ejecuta `opencode` y escribe `@evaluador-retencion corre gemma3:4b en mitad con nivel 4000`.

## Estructura del proyecto

```
├── agente.py # Núcleo (ejecutar_evaluacion) y agente evaluador
├── correr_experimento.py # Runner: configuraciones, bloques, orden aleatorio, reintentos y CSV
├── preparar_etiquetado.py # Hojas de etiquetado ciegas y kappa de Cohen
├── evaluar_calidad_texto.py # Naturalidad/coherencia/interés del generador de relleno
├── analisis/ # Análisis estadístico (D-19 a D-21); ver “Análisis estadístico”
│ ├── descriptivo.py # Acierto e intervalos de Clopper-Pearson
│ ├── fisher.py # Fisher por pares con Holm
│ ├── permutaciones.py # Permutación estratificada por bloque
│ ├── eda.py # Fallos por bloque, orden y tema
│ ├── posicion_lograda.py # Dónde quedó realmente el dato
│ ├── sensibilidad_bloque4.py # Análisis sin el bloque 4
│ ├── sensibilidad_formato.py # Criterio ampliado de formato (D-20)
│ ├── sensibilidad_ampliado.py # Fisher y permutación con ese criterio
│ ├── tiempos.py # Tiempo de ejecución por modelo y nivel
│ ├── logistica.py             # Regresión logística exploratoria (one-hot, L2)
│ ├── tipos_de_fallo.py        # Tipos de fallo por modelo (un evaluador)
│ ├── kappa.py                 # Kappa de Cohen entre las dos hojas de etiquetado
│ ├── graficas.py # Figuras
│ └── figuras/ # Imágenes generadas
├── agente_eval_claude.md # Plantilla de agente operador para Claude Code
├── agente_eval_open.md # Plantilla de agente operador para opencode
├── CLAUDE.md # Contexto del proyecto para agentes de IA
├── requirements.txt # Dependencias con versiones fijadas (pip freeze)
├── .env.example # Nombre de la variable de entorno (sin valores)
├── docs/
│ ├── DISENO.md # Diseño experimental completo
│ ├── decisiones.md # Registro de decisiones D-01 a D-23
│ ├── guia_etiquetado.md # Categorías y reglas del etiquetado de fallos
│ ├── contraparte/ # Registro de la contraparte metodológica (D-12)
│ ├── fuentes/ # Papers descargados y verificados
│ └── informes/ # PDF del primer corte
├── etiquetado/ # Hoja ciega, clave y hojas de cada evaluador
├── resultados/
│ ├── final_D14.csv # Una fila por corrida
│ ├── final_D14/ # JSON y TXT por corrida
│ ├── txt/ y json/ # Corridas del primer corte y de modos interactivos
│ ├── pruebas/ # Pruebas con proveedores gratuitos y registros del piloto
│ └── calidad_texto/ # Notas de calidad conversacional (exploratorio, no versionado)
├── nada_sin_fuente/ # Otra actividad del curso (ver su propio README)
└── README.md
```
## Trabajo futuro

- Evaluar modelos en la nube (Diseño B) con el mismo diseño factorial, para compararlos con los locales; antes hay que calcular el costo real (D-02, D-23).
- Más réplicas y más datos inventados en el banco (hoy 5 datos y 5 bloques) para ganar potencia y poder estimar la interacción posición × nivel.
- Niveles de contexto mayores a 12K y otros modelos locales.
- Clasificador de tipo de fallo (Laya u otro) con más fallos etiquetados, y agentes de verificación y análisis (D-22).
- Puntos de control dentro de la conversación (medidas repetidas) y una medida de respuesta cuantitativa (D-14, D-21).
- Modelo bayesiano o de Firth para la separación (D-19, D-21).
- Guardar el mensaje de la excepción de `generador_relleno` (D-18).


## Limitaciones conocidas

- Métrica binaria (acierto/fallo): no captura degradación parcial.
- Los rechazos de seguridad escritos en texto no se detectan automáticamente.
- Cinco réplicas por celda dan poca potencia; con 5 de 5 aciertos, el intervalo exacto al 95 % va de 0.48 a 1.00. La interacción triple probablemente no es estimable (D-14).
- Con 19 fallos en total y ninguno de `gemma3:4b`, el modelo completo de D-19 tiene muchos más parámetros de los que los fallos permiten estimar con holgura; por eso D-21 lo simplifica (sin interacción, con penalización L2) y lo declara exploratorio.
- El criterio exacto cuenta como fallo el número correcto escrito con otro formato (2 casos); D-20 lo trata como sensibilidad.
- 4 corridas técnicas inválidas por `generador_relleno` (todas de `gemma3:4b`) tienen causa no determinada porque el error no se guarda (`detalle_error` en `None`).
- El tema no queda perfectamente balanceado entre posiciones (ver "Diseño experimental").
- La posición lograda del dato se aparta de la nominal; se reporta de forma descriptiva (analisis/posicion_lograda.py) y no se usó como covariable (D-23) (en una corrida de prueba de `llama3.2:3b` a 4K, "mitad" quedó en el 56 % del nivel antes del dato y en el 65 % al cierre de su turno).
- El tope de 300 tokens cortó respuestas del modelo evaluado en las 135 corridas válidas (1,795 turnos en total): cerca del 37 % de los turnos de `gemma3:4b`, 65 % de `llama3.2:3b` y 60 % de `phi4-mini` (calculado a mano sobre el CSV, sin script, con `turnos_reales` como denominador). La proporción cambia con el modelo, así que el efecto del modelo puede incluir el del tope (D-06, D-16).
- Hay 5 datos para 5 bloques: con más réplicas el código daría `IndexError`.
- Cada modelo usa su propio tokenizador; las cifras de ambos cortes no son comparables.
- `top_k` y `top_p` no están fijados.
- Los modelos que razonan pueden consumir el límite de tokens en pensamiento interno y devolver texto vacío (relevante en la nube).
- El orquestador pequeño puede confundir nombres de modelos.
- El evaluador de calidad de texto es exploratorio y no está validado contra criterio humano.
- El etiquetado tiene 19 casos y dos evaluadores; la independencia se protegió por acuerdo.
- Los resultados valen para estos tres modelos y hasta 12K tokens.
- Resultados del primer corte: una réplica y solo posición *inicio*; los de `phi3:mini` y `gemma2:2b` no entran al análisis final.
- El texto final del agente interactivo lo redacta un modelo de 1.5B y puede sobreinterpretar una sola corrida (en la prueba del 3 de noviembre dijo que el resultado «demuestra la confiabilidad»); la medición es la línea «Resultado» de la herramienta.
- Al terminar, CrewAI 1.15.17 mostró un enlace de traza en `app.crewai.com`: el modo interactivo parece enviar la traza de la ejecución a ese servicio. No se verificó qué contiene ni cómo desactivarlo. Las 135 corridas no pasan por CrewAI.
- La hipótesis central de D-14 (interacción posición × nivel) no se contrasta: D-21 usa un modelo sin interacción por la baja potencia (19 fallos).

## Fuentes y trazabilidad

El corpus son 11 artículos públicos guardados en `docs/fuentes/`. Su origen, versión, fecha de ingreso al repositorio y licencia están en `nada_sin_fuente/03_sistema/procedencia.md`. La columna «Verificó» registra quién abrió cada PDF para comprobar su origen y versión: Juan Pablo verificó los 11.

Las afirmaciones del estado del arte se comprueban una por una en `nada_sin_fuente/03_sistema/trazabilidad.md`, con página y cita corta. Las que no se sostienen como estaban escritas se registran en la tabla «Afirmaciones corregidas» de ese archivo.

Los PDF son copias para uso académico. Varios están bajo la licencia no exclusiva de arXiv, que no autoriza expresamente la redistribución, así que se enlaza la fuente original y se retiran si un autor lo pide.

## Referencias del diseño experimental

- Montgomery, D. C., y Runger, G. C. (2018). *Applied statistics and probability for engineers* (7.ª ed.). John Wiley & Sons. Páginas citadas: 353, 361 a 363, 368 a 369, 378 y 381.
- Material del curso: «Capítulo 6: Diseños factoriales con tres factores» (sin autor indicado en el archivo), pp. 1 a 3 y 6 a 7.
- Permutación, Fisher exacto, Clopper-Pearson y Holm: sin cita; los scripts de `analisis/` y D-21 los describen.

## Autores

- Juan Pablo Tibamoso
- Cristian Vallejo

Consultoría e Investigación, Pregrado en Estadística. Universidad Santo Tomás, Bogotá, Colombia.
Docente: Javier Mauricio Sierra