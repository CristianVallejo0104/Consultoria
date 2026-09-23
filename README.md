# Evaluador de Confiabilidad de LLMs en Conversaciones Largas

Sistema que evalúa en qué punto los modelos de lenguaje dejan de retener un dato inventado según la posición del dato y la longitud de la conversación (fenómeno "lost in the middle"). Proyecto de Consultoría e Investigación, Universidad Santo Tomás.

> **Estado:** en desarrollo. El núcleo local funciona y tiene resultados preliminares. Se está migrando la longitud de la conversación de *número de turnos* a *niveles de tokens* y se está cerrando el diseño con modelos en la nube. Las secciones marcadas como **pendiente** no están decididas.

## Contraparte

Estudiantes y profesionales de estadística que usan modelos de lenguaje locales (Ollama) como apoyo en análisis de datos, cálculos y consultas técnicas. Hoy no existe una forma sistemática de saber en qué punto de una conversación larga el modelo deja de ser confiable, lo que puede llevar a decisiones basadas en respuestas que el modelo ya olvidó o inventó.

### Por qué no usar herramientas de evaluación existentes

G-Eval (Liu et al., 2023) usa un modelo de lenguaje como juez para calificar la calidad de un texto aislado, y RAGAS (Es et al., 2023) evalúa sistemas de recuperación de documentos sobre interacciones individuales. Ninguno mide la **retención de información a lo largo de una conversación de varios turnos**. Este proyecto sí, con datos inventados que el modelo no puede conocer de su entrenamiento, evaluación determinista (sin modelo juez) y ejecución local reproducible.

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

1. **Agente CrewAI (orquestador).** Modelo `qwen2.5:1.5b`, temperatura 0.0. Recibe la tarea y llama a la herramienta `evaluar_retencion` con los parámetros exactos. No escribe la conversación.
2. **Núcleo en Python.** La función `ejecutar_evaluacion()` ejecuta toda la conversación turno a turno y verifica el resultado de forma determinista. Las corridas masivas la llaman directamente, sin pasar por el agente.
3. **Generador de relleno.** El mismo `qwen2.5:1.5b`, vía Ollama, escribe los mensajes del "usuario" en los turnos que no llevan el dato clave. Los modelos evaluados son de empresas distintas a la del orquestador para evitar sesgo de auto-preferencia.

Flujo de una corrida:
1. Se elige modelo, posición del dato y longitud.
2. Se inicia una conversación con el modelo evaluado.
3. En cada turno, el generador de relleno escribe el mensaje del usuario.
4. En el turno indicado se inserta un dato inventado (banco rotativo de 5 datos, 6 temas de conversación) y la conversación cambia de tema.
5. Al final se pregunta por el dato.
6. Se verifica si la cadena exacta aparece en la respuesta, sin negación.
7. Se guarda el reporte (`resultados/txt/`) y el JSON estructurado (`resultados/json/`).

## Modelos

Datos verificados con `ollama show`.

| Modelo | Empresa | Parámetros | Ventana | Cuantización | Rol |
|---|---|---|---|---|---|
| `phi3:mini` | Microsoft | 3.8B | 131,072 | Q4_0 | Evaluado (local) |
| `llama3.2:3b` | Meta | 3.2B | 131,072 | Q4_K_M | Evaluado (local) |
| `gemma3:4b` | Google | 4.3B | 131,072 | Q4_K_M | Evaluado (local) |
| `gemma2:2b` | Google | 2.6B | 8,192 | Q4_0 | Referencia a nivel bajo |
| `qwen2.5:1.5b` | Alibaba | 1.5B | 32,768 | Q4_K_M | Orquestador y generador de relleno |

Un modelo por empresa. `gemma2:2b` se reemplazó en el diseño factorial por `gemma3:4b` (ver D-01).

**Modelos en la nube (Diseño B, lista final pendiente).** El código tiene ramas para NVIDIA, Groq, Gemini y OpenRouter. El plan es usar OpenRouter con créditos pagados como proveedor principal. Los modelos en la nube solo son sujetos evaluados, nunca orquestador.

## Parámetros controlados

Constantes al inicio de `agente.py`:

| Constante | Valor | Razón |
|---|---|---|
| `TEMPERATURA` | 0.7 | Igual en todos los modelos evaluados y en el generador de relleno. Sin fijarla, cada proveedor usa la suya (Ollama 0.8, nube ~1.0) y se confunde con el efecto del modelo. Con 0 las réplicas serían casi idénticas. |
| `TEMPERATURA_ORQUESTADOR` | 0.0 | El orquestador solo copia parámetros. |
| `NUM_CTX_OLLAMA` | 8192 (**provisional**) | Evita el truncamiento silencioso de Ollama. Debe subir con los niveles de tokens. |
| `TIMEOUT_SEGUNDOS` | 180 | Aplica a todas las llamadas. Sin timeout, `requests` espera indefinidamente. |
| `random.seed(42)` | — | Controla qué dato y qué tema se eligen. No controla la generación del modelo (a propósito: las réplicas necesitan variabilidad natural). |

`top_k` y `top_p` no se fijan: cada modelo usa los suyos.

## Clasificación de las corridas

| Estado | Significado | `acierto` |
|---|---|---|
| `valida` | El modelo respondió | `true` / `false` |
| `invalida_tecnica` | Fallo de API o red (`rate_limit`, `sobrecarga`, `timeout`, `conexion`, `respuesta_inesperada`, `generador_relleno`, `excepcion_interna`) | `null` |
| `rechazo_seguridad` | El modelo o el proveedor se negó por política | `null` |

Las corridas inválidas **no** cuentan como "el modelo olvidó el dato". Si cualquier turno de la conversación falla, la corrida se aborta, porque una conversación con huecos es otro tratamiento. Límite conocido: los rechazos escritos en texto ("no puedo ayudar con eso") no se detectan automáticamente.

Campos del JSON: `modelo, empresa, turnos, posicion, tema, dato_clave, turno_dato, tokens_prompt, tokens_respuesta, tokens_totales, tiempo_segundos, acierto, estado_final, errores_por_tipo, respuesta_final, verificacion, detalle_error, temperatura, num_ctx`. Nota: `tokens_prompt` es la **suma** de los prompts de todas las llamadas (cada turno reenvía el historial), no la longitud de la conversación.

## Diseño experimental (en definición)

- **Factores:** modelo × posición del dato (inicio, mitad, final) × nivel de tokens × réplicas.
- **Niveles de tokens: pendiente.** La longitud pasa de turnos a tokens porque "5 turnos" no es comparable entre modelos (`phi3:mini` generó ~10,000 tokens en 5 turnos; `gemma2:2b`, ~1,900). Los niveles se fijarán con un piloto local cuyos datos no entran al análisis final.
- **Análisis previsto:** regresión logística (modelo, posición, nivel, interacciones); chi-cuadrado solo para tablas marginales con frecuencias esperadas suficientes; verificación de supuestos.
- **Alcance:** el estudio solo dice algo sobre los niveles de contexto medidos, no sobre contextos mayores aunque el modelo los soporte.

## Decisiones de diseño

Cada decisión se documenta con su alternativa descartada.

- **Agente CrewAI con una herramienta.** El agente es una capa delgada para uso interactivo: recibe instrucciones en lenguaje natural y llama a la herramienta. La lógica del experimento es código determinista, y las corridas masivas no usan el agente. Alternativa descartada: tres herramientas separadas, porque pasar el texto de la conversación por el agente entre cada una saturaba su contexto.
- **Agentes solo donde hay juicio de lenguaje.** No hay agente selector local/nube (un diccionario lo resuelve) ni agente para verificar supuestos estadísticos (código plano). Están planeados tres agentes con juicio real: un verificador de checkpoints intermedios, un clasificador de tipo de fallo y un analista de hallazgos.
- **CrewAI.** Alternativas descartadas: LangChain (más componentes para el mismo formato ReAct), LangGraph (grafo nodo por nodo, sobrediseño para un flujo lineal) y AutoGen (complejidad sin beneficio para este caso).
- **Datos inventados, no conocimiento general.** La primera versión usaba "la capital de Australia es Canberra" y todos acertaban por conocimiento de entrenamiento, no por retención.
- **Evaluación determinista, no LLM-juez.** Se busca la cadena exacta en la respuesta. Alternativa descartada: otro modelo como evaluador (ruido y circularidad).
- **Manejo de errores unificado.** Un solo punto (`consultar_modelo`) convierte errores de red en corridas inválidas tipadas; una sola función interpreta las APIs compatibles con OpenAI. Alternativa descartada: copiar el parche en cada rama.
- **D-01: `gemma2:2b` → `gemma3:4b`.** La ventana de 8,192 tokens de `gemma2:2b` impide niveles de 10K o más. Se decidió por una restricción de diseño, antes de correr datos con el modelo nuevo. Se conserva `gemma2:2b` como referencia y su hallazgo original como resultado preliminar.
- **D-02: pagar créditos de OpenRouter (~US$20).** Los planes gratuitos produjeron corridas inválidas: Groq (límites de 8,000 y 1,000 tokens por minuto según el modelo), NVIDIA (~7 min por corrida de 5 turnos y un endpoint anunciado como deprecado), Gemini (503 intermitentes) y OpenRouter `:free` (límites propios). Por eso no recomendamos depender de APIs gratuitas para corridas masivas. Alternativa descartada: seguir con los planes gratuitos.

## Guardarraíles

- No genera conclusiones estadísticas ni decide qué modelo es "mejor": ejecuta pruebas y reporta.
- No accede a datos personales ni confidenciales.
- No modifica los modelos evaluados.
- La verificación es determinista: no se usa un LLM como evaluador.

## Iteraciones del diseño

- **v1, párrafos estáticos:** el dato entre texto de relleno. Todos los modelos acertaban.
- **v2, conversación con preguntas fijas:** las preguntas no seguían el hilo.
- **v3, conversación natural generada:** `qwen2.5` escribe los mensajes del usuario según las respuestas del modelo.
- **v4, dato inventado con banco rotativo:** los datos de conocimiento general medían conocimiento previo, no retención.
- **v5, orquestador liviano y temporizador:** `qwen2.5:1.5b` (986 MB) en lugar de `qwen2.5` (4.7 GB), para correr con 8 GB de RAM.
- **v6, control de variables y errores tipados:** temperatura fija, timeout, clasificación de corridas inválidas, detección de rechazos de seguridad, banco reescrito con frases neutras ("número de expediente") porque "código secreto" activaba filtros de seguridad.

## Resultados preliminares (primer corte)

9 pruebas, una réplica por combinación, dato en posición *inicio*, longitud en turnos. Son exploratorios y no permiten inferencia estadística. La columna *Tokens* cuenta solo los tokens generados por el modelo.

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
4. Se observaron cuatro tipos de fallo: alucinación (inventa un dato), admisión ("no tengo esa información"), negación de capacidad ("no puedo recordar conversaciones") y alucinación narrativa (`phi3:mini` convirtió un código en una leyenda cósmica).
5. El orquestador se equivoca con listas largas de modelos (confunde nombres o omite parámetros); una Task literal lo reduce pero no lo elimina.
6. Pruebas manuales posteriores con `gemma3:4b` (fuera del análisis): 5 y 10 turnos terminaron con un contexto de ~3K tokens en ambos casos, lo que confirma que "turnos" no mide longitud.

## Requisitos

- Python 3.12
- [Ollama](https://ollama.ai)
- Diseño local original: 8 GB de RAM. Con contextos largos hace falta más memoria (pendiente de medir; con `num_ctx=8192`, `phi3:mini` ya ocupa ~5.6 GB).
- GPU opcional. Probado con 6 GB de VRAM (RTX 3050); los modelos que no caben en la GPU se reparten entre GPU y CPU, más lento pero con los mismos resultados.
- Probado en Ubuntu 24.04 con Python 3.12. No se probó en Windows: el archivo `requirements.txt` viene de Linux e incluye paquetes como `uvloop` que, hasta donde sé, no existen para Windows. Si la instalación falla ahí, instala primero `crewai`, `requests` y `python-dotenv` y deja que pip resuelva el resto.

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
ollama pull phi3:mini
ollama pull llama3.2:3b
ollama pull gemma3:4b
ollama pull gemma2:2b               # referencia
```

## Configuración de modelos en la nube (opcional)

El núcleo local no necesita claves. Para evaluar modelos en la nube, copia `.env.example` a `.env` y completa solo las que vayas a usar:

```bash
cp .env.example .env
```

Variables: `NVIDIA_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`. **Nunca subas `.env` al repositorio** (está en `.gitignore`). Los modelos en la nube cuestan dinero o tienen límites de tasa: revisa las condiciones de tu proveedor antes de lanzar corridas masivas.

## Uso

**1. Interactivo con el agente CrewAI:**

```bash
python3 agente.py
```

Pide el modelo (nombre exacto), la posición (`inicio`, `mitad` o `final`) y el número de turnos. Guarda el resultado automáticamente en `resultados/txt/` y `resultados/json/`.

**2. Directo, sin CrewAI** (lo que usarán las corridas masivas):

```bash
mkdir -p resultados/txt resultados/json
python3 -c "from agente import ejecutar_evaluacion as e, guardar_resultado as g; r = e('gemma3:4b','mitad',5); g(r); print(r['estado_final'], r['acierto'])"
```

`ejecutar_evaluacion()` devuelve un diccionario; `guardar_resultado()` escribe los archivos. La longitud sigue en turnos hasta que termine la migración a tokens.

**3. Con un agente de terminal (Claude Code u opencode):** ver la sección siguiente.

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
- Claude Code: ejecuta `claude` y pide *"Usa el subagente evaluador-retencion para correr gemma3:4b en mitad con 5 turnos"*.
- opencode: ejecuta `opencode` y escribe `@evaluador-retencion corre gemma3:4b en mitad con 5 turnos`.

## Estructura del proyecto

```
├── agente.py                # Núcleo y agente evaluador
├── agente_eval_claude.md    # Plantilla de agente operador para Claude Code
├── agente_eval_open.md      # Plantilla de agente operador para opencode
├── CLAUDE.md                # Contexto del proyecto para agentes de IA
├── requirements.txt         # Todas las dependencias con versiones fijadas (pip freeze)
├── .env.example             # Nombres de las variables (sin valores)
├── resultados/
│   ├── txt/                 # Conversación completa de cada corrida
│   └── json/                # Resultado estructurado de cada corrida
└── README.md
```

## Limitaciones conocidas

- Métrica binaria (acierto/fallo): no captura degradación parcial.
- Los rechazos de seguridad escritos en texto no se detectan automáticamente.
- El dato clave rota entre corridas (banco de 5), lo que introduce variabilidad; se controla con la semilla y las réplicas.
- La diferencia entre modelos locales y en la nube mezcla tamaño del modelo, entrenamiento y ventana: no se atribuye a una sola causa.
- Los modelos que razonan pueden consumir el límite de tokens en pensamiento interno y devolver texto vacío (relevante en la nube).
- `top_k` y `top_p` no están fijados.
- Resultados del primer corte: una réplica y solo posición *inicio*.
- El orquestador pequeño puede confundir nombres de modelos.

## Autores

- Juan Pablo Tibamoso
- Cristian Vallejo

Consultoría e Investigación, Pregrado en Estadística. Universidad Santo Tomás, Bogotá, Colombia.
Docente: Javier Mauricio Sierra