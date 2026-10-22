# Evaluador de Confiabilidad de LLMs en Conversaciones Largas

Sistema que evalúa en qué punto los modelos de lenguaje locales dejan de retener un dato inventado, según la posición del dato, el nivel de longitud en tokens y el modelo (fenómeno "lost in the middle"). Proyecto de Consultoría e Investigación, Universidad Santo Tomás.

> **Estado (octubre 2026):** el diseño experimental (D-14) está implementado en `main`: bloques aleatorizados, dato por bloque, tema por rotación, guardado por corrida y campos de registro de validez. Las 135 corridas finales aún no se han lanzado (no existe `resultados/final_D14.csv`), y falta decidir la política de reintentos. Los resultados de este documento son del primer corte y de un piloto (exploratorios, sin inferencia). El análisis estadístico, el etiquetado de fallos y el diseño con modelos en la nube siguen pendientes. Detalle en `docs/DISENO.md` y `docs/decisiones.md`.

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

1. **Agente CrewAI (orquestador).** Modelo `qwen2.5:1.5b`, temperatura 0.0. Es la entrada interactiva en lenguaje natural: recibe la tarea y llama a la herramienta `evaluar_retencion` con los parámetros exactos. No escribe la conversación ni dirige las corridas masivas (D-08).
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

**Modelos en la nube (Diseño B, lista final pendiente).** `agente.py` conserva solo Ollama y OpenRouter; se retiraron las ramas de NVIDIA, Groq y Gemini (D-07) tras comprobar que sus planes gratuitos producían corridas inválidas (D-02). `MODELOS_CLOUD` está vacío hasta cerrar el Diseño B. Los modelos en la nube solo serían sujetos evaluados, nunca orquestador.

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

**Pendiente de decisión:** `no_alcanzo_nivel` hoy se marca `invalida_tecnica`, igual que un error de red, pero depende de cuán verboso es el modelo y no es un fallo aleatorio; su tratamiento y la política de reintentos no están decididos. Mientras tanto, `ya_hechas` cuenta cualquier fila del CSV como hecha, incluidas las inválidas.

Límite conocido: los rechazos de seguridad escritos en texto ("no puedo ayudar con eso") no se detectan automáticamente, y la detección de `rechazo_seguridad` solo existe en las API en la nube.

Campos del CSV (26 columnas): `modelo, posicion, nivel_tokens, replica, estado_final, acierto, turnos_reales, contexto_al_dato, contexto_final, contexto_decreciente, tokens_totales, tiempo_segundos, errores, tema, dato_clave` y, desde D-14 y D-16, `bloque, orden_en_bloque, indice_dato, indice_tema, done_reason_final, respuesta_final_vacia, contexto_tras_dato, contexto_antes_pregunta, turnos_dato_a_pregunta, dato_sobre_nivel, turnos_relleno_cortados`.

Notas sobre los campos:
- `tokens_prompt` (en el JSON) es la **suma** de los prompts de todas las llamadas (cada turno reenvía el historial); no es la longitud de la conversación.
- `contexto_final` es el `prompt_eval_count` de la llamada de la pregunta final, es decir, el contexto al preguntar. La redacción anterior de D-06 decía "prompt + respuesta" y se corrigió (D-16).
- `contexto_al_dato` se mide antes de insertar el dato y `contexto_tras_dato` al cierre de ese turno.
- `turnos_relleno_cortados` cuenta respuestas del modelo evaluado cortadas por el tope de tokens, no las del generador de relleno.

## Diseño experimental

Factorial completo en bloques completos aleatorizados (D-14, D-15). Detalle y justificación en `docs/DISENO.md`.

- **Factores fijos:** modelo (`phi4-mini`, `llama3.2:3b`, `gemma3:4b`) × posición del dato (inicio, mitad, final) × nivel de tokens (4,000, 8,000, 12,000) = 27 tratamientos.
- **Réplicas y bloques:** 5 réplicas organizadas en 5 bloques completos; el bloque es el dato inventado. Son 135 corridas. Dentro de cada bloque se baraja el orden de los 27 tratamientos con una semilla derivada del bloque (`crc32`, porque el `hash()` de Python cambia entre ejecuciones).
- **Tema:** 6 temas asignados por rotación, `(posición en el bloque + bloque) mod 6`. No es un bloque completo, y las corridas por tema no quedan parejas dentro de cada posición del dato (medido sobre el plan: inicio [10, 8, 5, 9, 7, 6], mitad [2, 6, 7, 8, 12, 10], final [10, 8, 10, 6, 4, 7]); se documenta como límite.
- **Respuesta:** acierto binario por cadena exacta, sin negación; sin LLM juez.
- **Nivel de tokens:** "5 turnos" no es comparable entre modelos (`phi3:mini` procesó 10,259 tokens en 5 turnos y `gemma2:2b`, 1,903). El nivel es el contexto en la pregunta final (D-06).
- **Justificación:** sigue la estructura de Liu et al. (2023: posición × longitud del contexto × modelo) y de Zhang et al. (2024), formalizada con principios de diseño de experimentos. Nuestra variante inserta el dato dentro de la conversación y no en un documento recuperado. **[Texto de diseño de experimentos por citar.]**
- **Análisis previsto (no decidido):** modelo para respuesta binaria con efecto de bloque, manejo de la separación (Firth o enfoque bayesiano), prueba exacta de Fisher en lugar de chi-cuadrado, intervalos exactos por celda y verificación de supuestos.
- **Alcance:** el estudio solo dice algo sobre estos tres modelos y los niveles medidos (hasta 12K), no sobre contextos mayores aunque el modelo los soporte.

## Calidad del texto de relleno

`evaluar_calidad_texto.py` evalúa naturalidad, coherencia e interés de los turnos del "usuario" con `qwen2.5:1.5b` como LLM juez (dimensiones de Mehri y Eskenazi, 2020; mecanismo de G-Eval; D-04). Es exploratorio y **no está validado contra criterio humano**: sus notas no se usan en el análisis final hasta validarlas. Hallazgo previo: el juez no penalizó de forma consistente los turnos cortados a mitad de frase, cuyo origen (un límite de 200 caracteres) ya se corrigió.

## Decisiones de diseño

Cada decisión se documenta con su alternativa descartada. Registro completo en `docs/decisiones.md`.

- **Agente CrewAI con una herramienta.** El agente es una capa delgada para uso interactivo. La lógica del experimento es código determinista. Alternativa descartada: tres herramientas separadas, porque pasar el texto de la conversación por el agente entre cada una saturaba su contexto.
- **Agentes solo donde hay juicio de lenguaje (D-08).** No hay agente selector local/nube (un diccionario lo resuelve) ni agente para verificar supuestos estadísticos (código plano). Están planeados un verificador de checkpoints intermedios, un clasificador de tipo de fallo y un analista de hallazgos.
- **CrewAI.** Alternativas descartadas: LangChain (más componentes para el mismo formato ReAct), LangGraph (sobrediseño para un flujo lineal) y AutoGen (complejidad sin beneficio).
- **Datos inventados, no conocimiento general (D-11).** La primera versión usaba "la capital de Australia es Canberra" y todos acertaban por conocimiento de entrenamiento.
- **Evaluación determinista, no LLM juez, para retención (D-09, D-11).** Alternativa descartada: otro modelo como evaluador (ruido y circularidad).
- **Manejo de errores unificado (D-11).** Un solo punto (`consultar_modelo`) convierte errores de red en corridas inválidas tipadas. Alternativa descartada: copiar el parche en cada rama.
- **D-01:** `gemma2:2b` → `gemma3:4b`, por la ventana de contexto.
- **D-02:** pagar créditos de OpenRouter (~US$20) en lugar de depender de planes gratuitos, que producían corridas inválidas (Groq: límites de 8,000 y 1,000 tokens por minuto según el modelo; NVIDIA: ~7 min por corrida de 5 turnos y un endpoint anunciado como deprecado; Gemini: 503 intermitentes; OpenRouter `:free`: límites propios).
- **D-03:** Laya explorado y pospuesto como clasificador de tipo de fallo: zero-shot rinde 38 % en 5 categorías (frente a 20 % de azar uniforme, con n = 13) y falta un conjunto de fallos reales etiquetados.
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

## Uso de IA en el desarrollo

Declarado según la rúbrica y registrado en D-17:

- **Decisiones de diseño:** del equipo (semilla que solo fija el diseño; tema por posición en el orden; reemplazos de modelos; contraparte metodológica).
- **Asistente de IA en chat (Claude):** explicó el porqué de cada paso antes del código, redactó la función `orden_del_bloque` (que Cristian tecleó, probó y puede explicar línea por línea), las especificaciones de cada tarea y las pruebas de verificación.
- **Claude Code, con permiso por edición y sin commits:** escribió el cambio mecánico en `agente.py` y `correr_experimento.py` (parámetros `indice_dato` e `indice_tema`, configuración `final_D14`, bucle por bloques, columnas nuevas, guardado determinista, manejo de errores del runner, campos de registro).
- **Subagentes de revisión de solo lectura** (`revisor-codigo-python` y `consultor-estadistico`): auditaron el código antes de las corridas. Sus resúmenes se contrastaron con el código y con las pruebas ejecutadas.
- **Verificación humana:** cada diff se revisó antes del commit y se ejecutaron pruebas con Ollama.
- **Distribución del trabajo entre integrantes:** por documentar.

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

## Herramientas exploratorias (fuera del núcleo de `agente.py`)

- **`evaluar_calidad_texto.py`:** evaluador de calidad conversacional del generador de relleno. Vive en este repositorio. Ver D-04.
- **Exploración de Laya** (clasificador de tipo de fallo): se probó en un entorno y carpeta separados (`venv-laya`, fuera de este repositorio, por conflicto de dependencias con `torch`/`transformers`), leyendo los JSON ya generados en `resultados/json/`. Pospuesto por falta de datos de fallo reales. Ver D-03. El código de esa exploración no está versionado aquí.

## Resultados preliminares

Son exploratorios, con una réplica por combinación, y no permiten inferencia estadística.

### Primer corte (septiembre 2026)

9 pruebas, dato en posición *inicio*, longitud en turnos. La columna *Tokens* cuenta solo los tokens generados por el modelo.

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

Variable usada por el código actual: `OPENROUTER_API_KEY` (`agente.py` solo lee esa; `.env.example` aún lista además `NVIDIA_API_KEY`, `GROQ_API_KEY` y `GEMINI_API_KEY`, de las ramas retiradas en D-07). **Nunca subas `.env` al repositorio** (está en `.gitignore`). Los modelos en la nube cuestan dinero o tienen límites de tasa: revisa las condiciones de tu proveedor antes de lanzar corridas masivas.

## Uso

**1. Corridas del diseño (runner):**

```bash
python correr_experimento.py              # sin argumento: lista las configuraciones disponibles
python correr_experimento.py final_D14    # las 135 corridas del diseño
```

- Configuraciones: `final_D14` (diseño final), y `preliminares_tokens` y `piloto_phi4` (primer corte y piloto, ya hechas: **no volver a correrlas**, sus CSV tienen 15 columnas y quedarían desalineados).
- Salidas: `resultados/<config>.csv` (una fila por corrida), `resultados/<config>/` (JSON y TXT por corrida, con nombre determinista como `llama3_2_3b_mitad_4000tok_01`) y `resultados/<config>_errores.log` (errores de guardado).
- Para retomar una corrida cortada, vuelve a ejecutar el mismo comando: `ya_hechas` omite lo que ya está en el CSV. No cambies `SEMILLA_EXPERIMENTO` ni las listas de modelos, posiciones o niveles entre retomas.
- Hoy el runner cuenta como hecha cualquier fila, también las inválidas (ver "Clasificación de las corridas").

**2. Una sola corrida, sin CrewAI:**

```bash
python -c "from agente import ejecutar_evaluacion as e, guardar_resultado as g; r = e('gemma3:4b','mitad',4000,indice_dato=0,indice_tema=0); g(r, carpeta_salida='resultados/prueba', replica=1); print(r['estado_final'], r['acierto'])"
```

`ejecutar_evaluacion()` devuelve un diccionario; el nivel debe ser 4000, 8000 o 12000. Sin `indice_dato` ni `indice_tema`, dato y tema se sortean.

**3. Interactivo con el agente CrewAI:**

```bash
python3 agente.py
```

El modo interactivo imprime los modelos, posiciones y niveles de tokens permitidos y pide tres datos: modelo, posición del dato y nivel de tokens (ya no número de turnos); el agente orquestador llama a la herramienta con esos valores. Guarda el resultado en `resultados/txt/` y `resultados/json/`.

**4. Evaluar la calidad del texto del generador de relleno** (exploratorio, no forma parte del análisis final aún):

```bash
python3 evaluar_calidad_texto.py
```

Evalúa una muestra de `resultados/txt/` con `qwen2.5:1.5b` como LLM juez y guarda en `resultados/calidad_texto/` (no versionado). Ver limitaciones en `docs/decisiones.md`.

**5. Con un agente de terminal (Claude Code u opencode):** ver la sección siguiente.

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
├── agente.py                    # Núcleo (ejecutar_evaluacion) y agente evaluador
├── correr_experimento.py        # Runner: configuraciones, bloques, orden aleatorio y CSV
├── evaluar_calidad_texto.py     # Naturalidad/coherencia/interés del generador de relleno
├── agente_eval_claude.md        # Plantilla de agente operador para Claude Code
├── agente_eval_open.md          # Plantilla de agente operador para opencode
├── CLAUDE.md                    # Contexto del proyecto para agentes de IA
├── requirements.txt             # Dependencias con versiones fijadas (pip freeze)
├── .env.example                 # Nombres de las variables (sin valores)
├── docs/
│   ├── DISENO.md                # Diseño experimental completo
│   ├── decisiones.md            # Registro de decisiones D-01 a D-17
│   ├── contraparte/             # Registro de la contraparte metodológica (D-12)
│   ├── fuentes/                 # Papers descargados y verificados
│   └── informes/                # PDF del primer corte
├── resultados/
│   ├── <config>.csv             # Una fila por corrida
│   ├── <config>/                # JSON y TXT por corrida
│   ├── txt/ y json/             # Corridas del primer corte y de modos interactivos
│   ├── pruebas/                 # Pruebas con proveedores gratuitos y registros del piloto
│   └── calidad_texto/           # Notas de calidad conversacional (exploratorio, no versionado)
├── nada_sin_fuente/             # Otra actividad del curso (ver su propio README)
└── README.md
```

## Limitaciones conocidas

- Métrica binaria (acierto/fallo): no captura degradación parcial.
- Los rechazos de seguridad escritos en texto no se detectan automáticamente.
- Cinco réplicas por celda dan poca potencia; con 5 de 5 aciertos, el intervalo exacto al 95 % va de 0.48 a 1.00. La interacción triple probablemente no es estimable (D-14).
- Las corridas inválidas rompen el balance de los bloques, y su tratamiento (junto con `no_alcanzo_nivel`) está pendiente de decisión.
- El tema no queda perfectamente balanceado entre posiciones (ver "Diseño experimental").
- La posición lograda del dato se aparta de la nominal; se reporta y se analizará como sensibilidad (en una corrida de prueba de `llama3.2:3b` a 4K, "mitad" quedó en el 56 % del nivel antes del dato y en el 65 % al cierre de su turno).
- El tope de 300 tokens por respuesta puede truncar muchas respuestas en algunos modelos (en pruebas con `llama3.2:3b` hubo 3 y 10 respuestas cortadas en conversaciones de 11 turnos); se registra `done_reason`.
- Hay 5 datos para 5 bloques: con más réplicas el código daría `IndexError`.
- Cada modelo usa su propio tokenizador; las cifras de ambos cortes no son comparables.
- `top_k` y `top_p` no están fijados.
- Los modelos que razonan pueden consumir el límite de tokens en pensamiento interno y devolver texto vacío (relevante en la nube).
- El orquestador pequeño puede confundir nombres de modelos.
- El evaluador de calidad de texto es exploratorio y no está validado contra criterio humano.
- Resultados del primer corte: una réplica y solo posición *inicio*; los de `phi3:mini` y `gemma2:2b` no entran al análisis final.

## Fuentes verificadas

La procedencia de las fuentes está en nada_sin_fuente/03_sistema/procedencia.md.

## Autores

- Juan Pablo Tibamoso
- Cristian Vallejo

Consultoría e Investigación, Pregrado en Estadística. Universidad Santo Tomás, Bogotá, Colombia.
Docente: Javier Mauricio Sierra