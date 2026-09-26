# CLAUDE.md — Contexto del proyecto

Este archivo le da contexto a Claude Code (o cualquier asistente) que revise este repositorio. Es un proyecto académico en curso, con decisiones ya tomadas y justificadas. **Este asesor solo revisa y sugiere — no edita código directamente.** El código real lo escriben Cristian y Juan Pablo en su propio flujo de trabajo.

*Última actualización: 2026-09-26.*

## Qué es este proyecto

Evaluador de confiabilidad de LLMs en conversaciones largas — el fenómeno "lost in the middle". Mide en qué punto un modelo deja de retener un dato inventado que se le dio en una posición específica de la conversación.

- **Curso:** Consultoría e Investigación, Universidad Santo Tomás, Bogotá
- **Autores:** Cristian Vallejo, Juan Pablo Tibamoso
- **Docente:** Javier Mauricio Sierra
- **Repositorio:** github.com/CristianVallejo0104/Consultoria
- **Restricción de diseño central:** el núcleo es local y reproducible (CrewAI + Ollama). Los modelos cloud son un segundo diseño para comparar, no un requisito.
- **Por qué se construyó paso a paso:** la sustentación es individual, así que cada línea de código debe poder explicarse.

## Alcance y desviaciones respecto al anteproyecto

El anteproyecto (primera entrega, nota 4.9) prometía 3 modelos locales, longitud en turnos (5/10/20) y "sin APIs de pago". El proyecto evolucionó. Cada desviación se documenta en `docs/decisiones.md` con su razón:

- Se añadió un Diseño B con modelos cloud (propuesto por el profesor: comparar si la nube retiene mejor que lo local).
- La longitud pasa de **turnos a niveles de tokens**, porque "5 turnos" no es comparable entre modelos (phi3 genera ~10,000 tokens en 5 turnos; gemma2, ~1,900).
- `gemma2:2b` se reemplaza por `gemma3:4b` (ver D-01).
- Se pagarán créditos de OpenRouter (ver D-02).

## Stack

Python 3.12, CrewAI, Ollama, `requests`, `python-dotenv`. Entorno de desarrollo: Ubuntu 24.04, GPU de 6 GB de VRAM (RTX 3050), 30 GB de RAM.

## Piezas del sistema (importante: son tres, no una)

1. **Agente CrewAI (orquestador).** Modelo `qwen2.5:1.5b`, temperatura 0.0. Su único trabajo es recibir la tarea y llamar a la herramienta `evaluar_retencion` con los parámetros exactos. No escribe la conversación. En las corridas masivas **no se usa**: se llama a `ejecutar_evaluacion()` directamente.
2. **Herramienta / núcleo en Python.** Ejecuta toda la conversación turno a turno de forma determinista y verifica el resultado.
3. **Generador de relleno.** Mismo modelo (`qwen2.5:1.5b`) por `/api/generate`, temperatura 0.7. Escribe los mensajes del "usuario" en los turnos que no llevan el dato clave.

Los modelos evaluados son siempre distintos de la familia del orquestador (Alibaba), para evitar sesgo de auto-preferencia.

## Mapa del código (`agente.py`)

- `consultar_modelo(modelo, historial)`: punto de entrada único. Envuelve a `_despachar_modelo` en un `try/except` que convierte `Timeout`, `ConnectionError`, JSON inválido y otros errores de red en corridas inválidas tipadas. Nunca lanza excepciones de red.
- `_despachar_modelo`: elige la rama según el modelo (Ollama local, NVIDIA, Groq, Gemini, OpenRouter).
- `_procesar_openai_compat(resp)`: interpreta respuestas de NVIDIA, Groq y OpenRouter. Detecta `finish_reason == "content_filter"` y `message.refusal` como `rechazo_seguridad`, y `content` nulo como `respuesta_inesperada`.
- `_invalida(estado, http, tipo)` y `_valida(contenido, tokens_prompt, tokens_respuesta)`: construyen el diccionario estándar que devuelve `consultar_modelo`.
- `_generar_relleno(historial)`: pide el siguiente mensaje del "usuario"; devuelve `None` si falla.
- `simular_conversacion(...)`: si **cualquier** turno falla, aborta la corrida como inválida (una conversación con huecos no es el tratamiento que se quiere medir).
- `ejecutar_evaluacion(modelo, posicion, num_turnos)`: núcleo del experimento; devuelve un diccionario. Contiene una barrera de excepciones que imprime el traceback y devuelve una corrida inválida (`excepcion_interna`). Los `ValueError` de configuración (modelo no permitido, turnos mal escritos) **no** se capturan: deben fallar ruidosamente.
- `verificar_acierto`, `guardar_resultado`, `seleccionar_dato_clave`, `seleccionar_tema`, `resolver_turno_dato`.

## Parámetros controlados (constantes al inicio de `agente.py`)

| Constante | Valor | Razón |
|---|---|---|
| `TEMPERATURA` | 0.7 | Igual en todos los modelos evaluados y en el generador de relleno. Con 0 las réplicas serían casi idénticas; sin fijarla, cada proveedor usa la suya (Ollama 0.8, cloud ~1.0) y se confunde con el efecto del modelo. |
| `TEMPERATURA_ORQUESTADOR` | 0.0 | El orquestador solo copia parámetros. |
| `NUM_CTX_OLLAMA` | 8192 (**provisional**) | Evita el truncamiento silencioso de Ollama. Debe subir cuando los niveles de tokens superen ~6K. |
| `TIMEOUT_SEGUNDOS` | 180 | Aplica a todas las llamadas, locales y cloud. Sin timeout, `requests` espera para siempre. |
| `random.seed(42)` | — | Controla qué dato y qué tema se eligen. **No** controla la generación del modelo (a propósito: las réplicas necesitan variabilidad natural). |

Notas: `top_k` y `top_p` no se fijan; cada modelo usa los suyos (diferencia a documentar). `num_ctx` solo aplica a modelos locales (en cloud queda `None` en el JSON).

## Clasificación de corridas

- `valida`: el modelo respondió; `acierto` es `True` o `False`.
- `invalida_tecnica`: fallo de API o de red (`rate_limit`, `sobrecarga`, `timeout`, `conexion`, `respuesta_inesperada`, `generador_relleno`, `excepcion_interna`...). `acierto = None`.
- `rechazo_seguridad`: el modelo o el proveedor se negó por política. `acierto = None`.

Las corridas inválidas **no** cuentan como "el modelo olvidó el dato". Límite conocido: `finish_reason` solo detecta rechazos que el proveedor marca; un rechazo escrito en texto ("no puedo ayudar con eso") no se detecta, y lo cubrirá el clasificador de fallos planeado.

## Esquema del JSON de resultados

`modelo, empresa, turnos, posicion, tema, dato_clave, turno_dato, tokens_prompt, tokens_respuesta, tokens_totales, tiempo_segundos, acierto, estado_final, errores_por_tipo, respuesta_final, verificacion, detalle_error, temperatura, num_ctx`.

Ojo: `tokens_prompt` es la **suma** de los prompts de todas las llamadas (cada turno reenvía el historial), no la longitud de la conversación. Para medir el nivel real hay que registrar el `tokens_prompt` de la última llamada (pendiente, paso 7c).

## Pruebas

El código se validó con pruebas internas basadas en `unittest.mock` (simulan respuestas de las APIs para no gastar cuota). Son de uso interno del equipo y **no se versionan**; no las busques en el repositorio.

## Agentes CLI

Para operar el experimento desde un agente de terminal hay dos plantillas en la raíz del repositorio:
- Claude Code: `agente_eval_claude.md` (se copia a `.claude/agents/evaluador-retencion.md`)
- opencode: `agente_eval_open.md` (se copia a `.opencode/agents/evaluador-retencion.md`)

El agente solo ejecuta y reporta; la medición la hace el código Python. opencode lee este `CLAUDE.md` como respaldo de `AGENTS.md`, por eso **no debe crearse un `AGENTS.md`** (lo ignoraría).

Ambas plantillas incluyen el comando para correr `evaluar_calidad_texto.py` (ver más abajo), además de las corridas de retención.

## Modelos

**Locales (Diseño A):** `phi3:mini` (Microsoft, 3.8B, ventana 131,072, Q4_0), `llama3.2:3b` (Meta, 3.2B, 131,072, Q4_K_M), `gemma3:4b` (Google, 4.3B, 131,072, Q4_K_M). `gemma2:2b` (Google, 2.6B, ventana 8,192, Q4_0) queda como referencia a un nivel bajo. Un modelo por empresa.

**Cloud (Diseño B, por cerrar):** hay ramas de código para NVIDIA, Groq, Gemini y OpenRouter. El plan es usar **OpenRouter con créditos pagados** como proveedor principal. Candidatos: GPT-OSS-120B, GLM-5.3-Flash (Z.ai), Tencent Hy3, DeepSeek V4 Flash estable. La lista final está pendiente y depende del costo real y de los límites de cada modelo. Los modelos cloud son solo sujetos evaluados, nunca orquestador.

## Decisiones de diseño (con alternativa descartada)

- **Datos inventados, no reales:** con hechos reales todos acertaban por conocimiento de entrenamiento, no por retención. Alternativa descartada: hechos reales.
- **Evaluación determinista, no LLM-juez:** compara contra una cadena de verificación exacta. Alternativa descartada: LLM como juez (ruido y circularidad).
- **Un agente, una herramienta:** tres herramientas saturaban el contexto del agente al pasar JSON entre ellas.
- **CrewAI sobre LangChain, LangGraph y AutoGen:** LangChain necesita más componentes para el mismo formato ReAct; LangGraph es sobrediseño para un flujo lineal; AutoGen agrega complejidad sin beneficio.
- **Orquestador local:** el costo y la latencia de un modelo cloud erosionarían la ventaja.
- **No usar agentes LLM en tareas deterministas:** sin agente selector local/cloud ni agente para supuestos estadísticos. Los agentes se reservan para juicio de lenguaje.
- **Funciones puras + `ejecutar_evaluacion()`:** permite corridas masivas sin el overhead de CrewAI.
- **Manejo de errores unificado (`_procesar_openai_compat`, `consultar_modelo`):** el bug de detección de rechazos se corrigió una vez, no tres. Alternativa descartada: parche mínimo copiado en cada rama.
- **Abortar la corrida al primer turno fallido:** una conversación con huecos es otro tratamiento. Alternativa descartada: continuar con `continue`, que dejaba corridas "válidas" con el historial roto.
- **D-01 · `gemma2:2b` → `gemma3:4b`:** la ventana de 8,192 de gemma2 impide niveles de 10K+. Se decidió por una restricción de diseño, antes de correr datos con el modelo nuevo. Se conserva el hallazgo original como resultado preliminar. Alternativas descartadas: mantener gemma2 con niveles ≤5K, excluir a Google, usar modelos de Meta o Alibaba ya instalados.
- **D-02 · Pagar OpenRouter (~US$20):** los planes gratuitos producían corridas inválidas (Groq: 8,000 y 1,000 tokens/min; NVIDIA: ~7 min por corrida y endpoint deprecado con ~5 días de aviso; Gemini: 503 intermitente; OpenRouter `:free`: límites propios y modelos de Google con rate limit inmediato). Alternativa descartada: seguir con APIs gratuitas.

## Hallazgos del primer corte (preliminares; usaban conteo por turnos)

- La ventana de contexto **no** predijo la retención: gemma2:2b (ventana 8,192) fue el único que acertó; phi3 y llama3.2 (131,072) fallaron desde 5 turnos. Cuidado: parte de los fallos de llama3.2 fueron rechazos de seguridad, ya corregidos en el banco de datos.
- Cuatro tipos de fallo: alucinación, admisión ("no recuerdo"), negación de capacidad, alucinación narrativa.
- Las palabras del banco importan: "código secreto" y "clave de acceso" disparaban filtros de seguridad; se reescribió con frases neutras.
- El orquestador pequeño se equivoca con listas de modelos largas; se mitiga con una Task literal, no se elimina.
- Los errores 429 y 503 no son fallos de retención.
- Observación de pruebas manuales con gemma3:4b (no forman parte del análisis): 5 y 10 turnos terminaron con un contexto de ~3K tokens en ambos casos, y la verbosidad varió de ~490 a ~250 tokens por respuesta. Confirma que "turnos" no mide longitud.

## Diseño experimental (en definición, NO cerrado)

- Factores: modelo × posición del dato (inicio/mitad/final) × nivel de tokens × réplicas. Objetivo provisional: 6 modelos × 3 posiciones × 3 niveles × 5 réplicas = 270 corridas.
- Niveles de tokens: **pendientes**. Candidatos discutidos: 5K/10K/15K y 10K/20K/30K. Se decidirán con un **piloto local**: 3 modelos × niveles 2K/5K/10K/20K × 3 posiciones × 2 réplicas = 72 conversaciones. Los datos del piloto se guardan aparte y **no entran al análisis final** (evita sesgo de selección de niveles).
- El nivel es la longitud del contexto cuando se hace la pregunta final, medida con el conteo de tokens de cada modelo (se verificó que `prompt_eval_count` es estable entre llamadas repetidas). El dato se inserta una vez y se pregunta una vez.
- Posiciones medidas en tokens (propuesta: inicio = primer turno, mitad ≈ 50 % del nivel, final ≈ 90 %). Regla de parada y tope de turnos: pendientes.
- **Decisión abierta (A/B):** con o sin tope común de tokens por respuesta. A favor del tope: comparabilidad entre modelos verbosos y concisos, y entre local y cloud. En contra: altera el comportamiento de los modelos verbosos, corta frases y puede dejar vacíos a los modelos que razonan.
- Análisis previsto: regresión logística (modelo, posición, nivel, interacciones); chi-cuadrado solo para tablas marginales con frecuencias esperadas suficientes; verificación de supuestos.
- Límite del alcance: el estudio solo dice algo sobre los niveles de contexto medidos, no sobre contextos mayores aunque el modelo los soporte. La diferencia local–cloud mezcla tamaño del modelo, entrenamiento y ventana; no se atribuye a una sola causa.
- Justificación del diseño factorial: sigue la misma estructura experimental de Liu et al. (2023, "Lost in the Middle") y su extensión en Zhang et al. (2024, "Found in the Middle") — ver "Hallazgos de exploración" abajo.

## Hallazgos de exploración (2026-09-26)

- **Laya (convaiinnovations/laya, checkpoint inglés) explorado como clasificador de tipo de fallo:** zero-shot, `choice` (5 categorías) da 38% de coincidencia con `verificar_acierto()` (cercano al azar); `noul` (sí/no binario) da 100%, con separación clara de probabilidad. El checkpoint `laya-multilingual` rindió peor (62%/62%) pese a estar en español — usar el inglés como base si se hace fine-tuning más adelante. Checkpoint reporta temperaturas de calibración inválidas; tratar su confianza como no calibrada. Bloqueado por falta de datos (solo 2 fallos reales en 13 corridas válidas del primer corte).
- **Taxonomía de tipos de fallo, respaldada con 3 fuentes:** "alucinación" → Huang et al. (2023) *Context Inconsistency* y Zhang et al. (2023, "Siren's Song") *Context-Conflicting Hallucination*; "admisión"/"negación de capacidad" → Wen et al. (2025) perspectiva de conocimiento del modelo, y Zhang et al. (2023) *Under-informativeness* (explícitamente NO alucinación); "rechazo de seguridad" → Wen et al. (2025) perspectiva de valores humanos; "alucinación narrativa" → Huang et al. (2023) *Factual Fabrication*, adaptada. Fuentes en `docs/fuentes/`.
- **Evaluador de calidad de texto** (`evaluar_calidad_texto.py`, nuevo): evalúa solo los turnos de "Usuario" (generador de relleno) en naturalidad/coherencia/interés, adaptando las dimensiones de Mehri y Eskenazi (2020, USR) medidas con el mecanismo de G-Eval (LLM juez con razonamiento paso a paso) en vez del método de modelos entrenados del paper original — decisión explícita, no equivalencia. Respaldo del método: Zheng et al. (2023, "Judging LLM-as-a-Judge"), que documenta sesgos conocidos (verbosidad, posición, auto-preferencia). Hallazgo real: se detectaron cortes de frase a mitad de palabra en el generador de relleno que el LLM juez no penalizó consistentemente — evidencia de sesgo de verbosidad. Validación manual (comparar notas del LLM contra lectura propia) sigue pendiente. Pendiente de confirmar con el profesor si la calidad a evaluar es del generador de relleno, del modelo evaluado, o ambos.
- **Justificación del diseño factorial:** el diseño (modelo × posición × nivel × réplicas) sigue la misma estructura de Liu et al. (2023, "Lost in the Middle") — 2,655 preguntas, k=10/20/30 documentos, posición variada, 6 modelos — y su extensión en Zhang et al. (2024, "Found in the Middle") — 7 modelos, posición variada, con estudio de ablación. Verificado directamente contra los PDF: ninguno de los dos usa el término "diseño de bloques"; describir como variación sistemática de factores, no forzar terminología estadística que las fuentes no usan.

## Trabajo pendiente (por prioridad)

1. Migrar a niveles de tokens: reglas de posición y parada, cambio en `simular_conversacion`, registrar tokens reales (al insertar el dato y en la pregunta final), pruebas con mocks.
2. Subir `num_ctx` según los niveles, y cronometrar una corrida larga antes del piloto.
3. Piloto local, y luego fijar los niveles finales.
4. Decidir el tope de tokens por respuesta (A/B).
5. Script del diseño factorial con réplicas, con manejo de excepciones por corrida.
6. Cerrar los modelos cloud y calcular el costo real con los precios vigentes.
7. Tres agentes planeados: verificador de checkpoints, clasificador de tipo de fallo (Laya bloqueado por falta de datos — retomar tras el piloto/270 corridas), analista de hallazgos.
8. Documentación: `docs/DISEÑO.md` (tabla de taxonomía + justificación de diseño, con las fuentes de hoy), `docs/decisiones.md` (D-01 a D-05), `docs/REPLICAR.md`.
9. Validar manualmente las notas del evaluador de calidad de texto contra lectura propia (comparar con las 5 conversaciones ya evaluadas).
10. Confirmar con el profesor: ¿calidad de texto pedida es del generador de relleno, del modelo evaluado, o ambos? (hoy se implementó solo para el generador de relleno).

## Pendiente de confirmar con el profesor

- Qué debe quedar exactamente en Obsidian: diseño experimental, registro de decisiones, o ambos.
- El nombre exacto de la herramienta "jev" que mencionó (modelo que entrega probabilidades sin interpretar lenguaje natural): sin confirmar.
- La contraparte concreta del proyecto (hoy solo hay "comparar contra G-Eval y Copilot", que es estado del arte, no una contraparte).

## Actividad separada: "Nada sin fuente"

Es otra actividad del mismo curso (30 % del corte): sistema de trazabilidad de fuentes y medición de referencias inventadas por IA sobre el anteproyecto. **No se mezcla con este código.** No es un RAG dentro de este proyecto. RAG y RAGAS se descartaron para el evaluador porque aquí se mide retención en conversaciones, no recuperación de documentos.

## Cómo trabajar con este repo

- Rol del asesor: revisar y sugerir con ubicaciones concretas. No editar. La implementación se escribe en conversación directa.
- Cada decisión debe tener una alternativa descartada documentada (requisito de la rúbrica).
- Antes de proponer un agente LLM, verificar que no sea lógica determinista.
- No inventar datos, referencias ni versiones: marcar como "sin verificar" lo que no se haya confirmado con `ollama show`, la documentación oficial o una fuente abierta.
- Nunca escribir claves de API en código, en el README ni en archivos versionados. Van en `.env` (ignorado por git); se documentan solo los **nombres** de las variables.
- Los datos y resultados del piloto se separan de los del análisis final.