# CLAUDE.md — Contexto del proyecto

Contexto para Claude Code, opencode o cualquier asistente que trabaje en este repositorio. Proyecto académico en curso, con decisiones ya tomadas y justificadas en `docs/decisiones.md`.

## Qué es este proyecto

Evaluador de confiabilidad de LLMs en conversaciones largas (fenómeno "lost in the middle"). Mide en qué punto un modelo local deja de retener un dato inventado según el modelo, la posición del dato y el nivel de tokens.

- **Curso:** Consultoría e Investigación, Universidad Santo Tomás, Bogotá. Docente: Javier Mauricio Sierra.
- **Autores:** Cristian Vallejo, Juan Pablo Tibamoso.
- **Repositorio:** github.com/CristianVallejo0104/Consultoria
- **Restricción central:** núcleo local y reproducible en cuanto al diseño (CrewAI + Ollama).
- **La sustentación es individual:** cada línea de código debe poder explicarla quien la presenta. Por eso se avanza paso a paso y se declara qué escribió la IA (ver README, "Uso de IA en el desarrollo").

## Estado (2026-11-05)

- Las 135 corridas de `final_D14` están completas: 135 celdas válidas y 139 filas en `resultados/final_D14.csv` (4 filas `invalida_tecnica` por `generador_relleno`, todas de `gemma3:4b`, conservadas como historial; D-18).
- 19 fallos: `llama3.2:3b` 7, `phi4-mini` 12, `gemma3:4b` 0. Más de la mitad está en el bloque 4.
- Etiquetado de los 19 fallos terminado por los dos (`etiquetado/`, `docs/guia_etiquetado.md`); kappa de Cohen 0.089 (4 de 19 coincidencias, 2 de ellas fijadas por la regla de F003 y F004): acuerdo apenas por encima del azar (`analisis/kappa.py`). Sin consenso y sin reetiquetar; los tipos de fallo por modelo no se presentan como resultado (D-24).
- Análisis no paramétrico ejecutado (D-21), en `analisis/`: descriptivo, Fisher por pares con Holm, permutación estratificada, EDA y sensibilidades (formato, sin el bloque 4, posición lograda). Regresión logística exploratoria con one-hot y penalización L2 ajustada (`analisis/logistica.py`). No hechas (D-23): tema y `contexto_final` como covariables.
- Fuera de alcance (D-22): Laya y los agentes planeados en D-08. Diseño B con modelos en la nube: no ejecutado (D-23).

## Reglas para el asistente

- Cada decisión debe tener una alternativa descartada documentada (requisito de la rúbrica).
- No inventar datos, referencias ni versiones: marcar como "sin verificar" lo que no se haya confirmado con `ollama show`, la documentación oficial o una fuente abierta.
- No cambiar `verificar_acierto` ni nada del diseño después de ver resultados: cualquier cambio va como entrada nueva en `decisiones.md` (ver D-19 y D-20).
- No editar sin permiso por edición, y sin commits: el equipo revisa cada `git diff` (D-17).
- Nunca `git add .`: hay cientos de archivos de resultados sin seguimiento. Agregar siempre archivos por nombre.
- Antes de proponer un agente LLM, verificar que no sea lógica determinista.
- Nunca escribir claves de API en código, README ni archivos versionados. Van en `.env` (ignorado por git); solo se documentan los nombres de las variables.
- Los datos del piloto y del primer corte no entran al análisis final.

## Stack

Python 3.12, CrewAI, Ollama, `requests`, `python-dotenv`. Ubuntu 24.04, GPU de 6 GB (RTX 3050), 30 GB de RAM.

## Piezas del sistema (son tres)

1. **Agente CrewAI (orquestador).** `qwen2.5:1.5b`, temperatura 0.0. Entrada interactiva: recibe una tarea literal armada en Python con modelo, posición y nivel ya validados, y llama a la herramienta `evaluar_retencion` con parámetros exactos. No se usa en las corridas masivas.
2. **Núcleo en Python.** `ejecutar_evaluacion()` ejecuta la conversación turno a turno y verifica el resultado de forma determinista. Las corridas masivas lo llaman desde `correr_experimento.py`.
3. **Generador de relleno.** `qwen2.5:1.5b` por `/api/generate`, temperatura 0.7. Escribe los mensajes del "usuario" en los turnos sin el dato.

Los modelos evaluados son de empresas distintas a la del orquestador (Alibaba), para evitar sesgo de autopreferencia.

## Archivos del código

- `agente.py`: núcleo y agente. Solo conserva Ollama y OpenRouter (D-07).
- `correr_experimento.py`: runner. Bloques, orden con `crc32`, reintentos (`ya_hechas`, `es_reintentable`, `intentos_previos`) y parada tras 3 fallas reintentables seguidas (D-15, D-18).
- `preparar_etiquetado.py`: `cargar_fallos`, `escribir_hojas` (hoja ciega y clave) y `kappa_cohen`.
- `analisis/`: scripts del análisis estadístico (ver README, "Análisis estadístico"). Se ejecutan desde la raíz con `python analisis/<script>.py`; `sensibilidad_formato.py` y `sensibilidad_ampliado.py` necesitan `PYTHONPATH=.` porque importan `agente.py`.
- `evaluar_calidad_texto.py`: evaluador exploratorio del texto de relleno (D-04).

Mapa de funciones de `agente.py` (las funciones nombradas existen según una revisión del 2026-11-03; además existen `validar_parametros`, `_consultar_ollama`, `_consultar_openrouter`, `_toca_insertar_dato`, `_resultado_vacio`, `_contar_error`, `generar_nombre_archivo`, `texto_resultado` y `evaluar_retencion`): `consultar_modelo` (punto único de manejo de errores de red), `_despachar_modelo`, `_procesar_openai_compat`, `_invalida`, `_valida`, `_generar_relleno` (devuelve `None` si falla y no guarda la excepción), `simular_conversacion` (aborta si falla cualquier turno), `ejecutar_evaluacion`, `verificar_acierto`, `guardar_resultado`, `seleccionar_dato_clave`, `seleccionar_tema`.

## Diseño experimental (cerrado, D-14 y D-15)

Factorial completo en bloques completos aleatorizados:
- Modelo (`phi4-mini`, `llama3.2:3b`, `gemma3:4b`) × posición (inicio, mitad, final) × nivel (4,000, 8,000, 12,000) = 27 tratamientos.
- 5 bloques; el bloque es el dato inventado. 135 corridas. Orden aleatorio dentro de cada bloque con semilla derivada de (`SEMILLA_EXPERIMENTO` = 42, bloque). La semilla solo fija el diseño, no la generación de Ollama.
- Tema por rotación (6 temas), covariable.
- Respuesta binaria por cadena exacta, sin negación; sin LLM juez para retención (D-11, D-19).
- Nivel = contexto en la pregunta final, medido con `prompt_eval_count` (D-06). Posiciones: inicio = 2.º turno, mitad al cruzar el 50 %, final al cruzar el 85 %.
- Alcance: solo estos tres modelos y hasta 12K tokens.

## Parámetros controlados

| Constante | Valor |
|---|---|
| `TEMPERATURA` | 0.7 (modelos evaluados y generador de relleno) |
| `TEMPERATURA_ORQUESTADOR` | 0.0 |
| `NUM_CTX_OLLAMA` | 16,384 |
| `TIMEOUT_SEGUNDOS` | 600 |
| Tope de respuesta | 300 tokens |
| Máximo de turnos | 60 |
| `SEMILLA_EXPERIMENTO` | 42 (en `correr_experimento.py`) |

`top_k` y `top_p` no se fijan. `random.seed(42)` sigue en `agente.py` solo para el modo interactivo.

## Clasificación de corridas

- `valida`: el modelo respondió; `acierto` es `True` o `False`.
- `invalida_tecnica`: fallo de API o red, o `no_alcanzo_nivel`. `acierto = None`. Es reintentable salvo `no_alcanzo_nivel`, que es resultado del tratamiento (D-18).
- `rechazo_seguridad`: el modelo o el proveedor se negó por política. `acierto = None`.

Las corridas inválidas no cuentan como "el modelo olvidó el dato". Los rechazos escritos en texto no se detectan automáticamente.

## Esquema de salida

CSV de `final_D14`: 27 columnas (lista completa en el README, "Clasificación de las corridas"). `intento` es la última. Cada reintento agrega una fila y sobrescribe el JSON y el TXT del intento anterior (nombre determinista, D-16).

Claves del JSON por corrida: `modelo, empresa, posicion, nivel_tokens, tema, dato_clave, verificacion, turno_dato, contexto_al_dato, contexto_final, turnos_reales, contextos_por_turno, tokens_prompt, tokens_respuesta, tokens_totales, tiempo_segundos, acierto, estado_final, errores_por_tipo, contexto_decreciente, done_reason_final, respuesta_final_vacia, contexto_tras_dato, contexto_antes_pregunta, turnos_dato_a_pregunta, dato_sobre_nivel, turnos_relleno_cortados, respuesta_final, detalle_error, temperatura, max_tokens_respuesta, num_ctx`.

`tokens_prompt` es la suma de los prompts de todas las llamadas, no la longitud de la conversación. Las corridas con `final_D14` guardan en `resultados/final_D14/`.

## Modelos

Evaluados (locales): `phi4-mini` (Microsoft, 3.8B, Q4_K_M), `llama3.2:3b` (Meta, 3.2B, Q4_K_M), `gemma3:4b` (Google, 4.3B, Q4_K_M). Un modelo por empresa. Orquestador y relleno: `qwen2.5:1.5b` (Alibaba). `phi3:mini` y `gemma2:2b` solo en el primer corte, como resultados preliminares (D-01, D-13).

Diseño B con modelos en la nube: **no ejecutado** (D-23). `MODELOS_CLOUD` está vacío; `agente.py` conserva la rama de OpenRouter, que no se usó en `final_D14` (D-07).

## Decisiones clave (resumen; detalle y alternativas en `docs/decisiones.md`)

- **D-11:** datos inventados, evaluación determinista, aborto ante cualquier turno fallido.
- **D-14, D-15:** factorial en bloques; semilla solo del diseño; `crc32` y no `hash()`.
- **D-16:** guardado determinista y campos de registro de validez.
- **D-18:** reintento manual acotado de fallas técnicas externas; parada tras 3 seguidas.
- **D-19, D-20, D-21:** plan de análisis, criterio ampliado por formato como análisis aparte, y cambio a pruebas no paramétricas como resultado principal (Fisher por pares con Holm y permutación estratificada), con regresión logística con one-hot como modelo exploratorio. D-21 sustituye el plan bayesiano o de Firth de D-19.
- **D-08:** agentes solo donde hay juicio de lenguaje; verificador, clasificador y analista no se implementaron (D-22).
- **D-03, D-22:** Laya pospuesto y fuera de alcance: con 19 fallos no se entrena.
- **D-23:** cierre de alcance: qué no se hizo (Diseño B en la nube y otros pendientes) y por qué.
- **D-24:** kappa del etiquetado 0.089; se reporta sin consenso y los tipos de fallo no son resultado.


## Hallazgos preliminares (primer corte y piloto; no entran al análisis final)

- La ventana nominal no predijo la retención en el primer corte.
- Cuatro tipos de fallo observados: alucinación, admisión, negación de capacidad y alucinación narrativa (D-03).
- Las palabras del banco de datos importan: "código secreto" disparaba filtros de seguridad.
- El orquestador pequeño se equivoca con listas largas de modelos.

## Actividad separada: "Nada sin fuente"

Otra actividad del mismo curso (trazabilidad de fuentes y referencias inventadas por IA sobre el anteproyecto). No se mezcla con este código y no es un RAG dentro de este proyecto.

## Agentes CLI

Plantillas de un agente operador en la raíz: `agente_eval_claude.md` (Claude Code, `.claude/agents/evaluador-retencion.md`) y `agente_eval_open.md` (opencode, `.opencode/agents/evaluador-retencion.md`). Solo ejecutan y reportan; la medición la hace el código Python. opencode lee este `CLAUDE.md` como respaldo de `AGENTS.md`, por eso no debe crearse un `AGENTS.md`.