# Evaluador de Confiabilidad de LLMs en Conversaciones Largas

Agente de IA que evalúa si los modelos de lenguaje pierden información
según la longitud de la conversación y la posición del dato clave.
Proyecto de Consultoría e Investigación - Universidad Santo Tomás.

## Contraparte

Estudiantes y profesionales de estadística que utilizan modelos de
lenguaje locales (Ollama) como herramienta de apoyo en análisis de
datos, cálculos y consultas técnicas. Actualmente no existe una forma
sistemática de saber en qué punto de una conversación larga el modelo
deja de ser confiable, lo que puede llevar a decisiones basadas en
respuestas que el modelo ya "olvidó" o inventó.

### Por qué no usar herramientas de evaluación existentes

Existen frameworks como G-Eval y RAGAS que evalúan LLMs, y servicios
como Copilot o Gemini que ofrecen respuestas de alta calidad. Sin
embargo, nuestro enfoque se diferencia en tres aspectos:

1. **Validación estadística**: G-Eval y RAGAS reportan métricas pero
   no verifican supuestos estadísticos ni aplican pruebas formales
   como chi-cuadrado o entropía de Shannon
2. **Modelos locales**: Copilot y Gemini son servicios en la nube con
   modelos propietarios. Nuestro agente evalúa modelos que cualquier
   persona puede correr en su propia máquina con Ollama, sin costo
   ni dependencia de internet
3. **Reproducibilidad total**: Todo el experimento es reproducible
   en cualquier PC con 8 GB de RAM, sin APIs externas ni claves

## Línea base — cómo se hace sin el agente

Sin esta herramienta, un usuario tendría que:
1. Abrir Ollama manualmente y escribir una conversación larga
2. Insertar un dato a mano en algún punto
3. Seguir conversando y al final preguntar por el dato
4. Anotar en papel si acertó o no
5. Repetir para cada modelo, posición y longitud

Esto tomaría aproximadamente 2-3 horas por combinación y no
genera registros sistemáticos ni reproducibles. Con el agente,
una prueba completa de 9 combinaciones (3 modelos × 3 longitudes)
tarda aproximadamente 45 minutos y genera reportes automáticos.

## Qué hace

El agente genera conversaciones naturales con un modelo de prueba,
inserta un dato inventado en una posición controlada (inicio, mitad o final),
y al finalizar le pregunta por ese dato para verificar si lo retuvo.

El flujo de trabajo es:

1. El usuario elige modelo, posición del dato y cantidad de turnos
2. El agente (qwen2.5:1.5b) decide cómo ejecutar la evaluación
3. La herramienta inicia una conversación real con el modelo de prueba
4. En cada turno, qwen2.5:1.5b genera preguntas naturales basadas en
   las respuestas del modelo, simulando un usuario real
5. En el turno indicado, se inserta el dato clave de forma natural
6. La conversación cambia de tema para alejar al modelo del dato
7. Al final se pregunta por el dato y se evalúa si acertó
8. El reporte completo se guarda en resultados.txt con el tiempo de ejecución

## Decisiones de diseño

### Por qué un agente y no un script

La tarea requiere interpretar instrucciones en lenguaje natural y
decidir qué herramienta usar con qué parámetros. El agente recibe
"prueba los tres modelos con 10 turnos" y él decide cuántas veces
llamar la herramienta y con qué valores.

### Por qué un solo agente y no varios

Las operaciones (generar conversación, consultar modelo, evaluar)
son pasos secuenciales de un mismo proceso, no roles distintos que
requieran razonamiento independiente. Un segundo agente evaluador
sería innecesario porque la evaluación es determinística (verificar
si un dato exacto aparece en la respuesta).

### Por qué CrewAI

- Estructura clara con pocos conceptos (Agent, Task, Tool, Crew)
- Soporte nativo para Ollama (modelos locales)
- Fácil de explicar y sustentar
- Alternativas descartadas: LangChain (demasiado complejo para 3
  semanas), AutoGen (orientado a conversación entre agentes, no a
  flujos con herramientas)

### Elección de modelos

**Agente (orquestador):** qwen2.5:1.5b (Alibaba, 986 MB)
- Elegido por su capacidad de seguir instrucciones estructuradas
- Lo suficientemente liviano para correr junto con el modelo de prueba
  en 8 GB de RAM
- Separado del experimento para no contaminar las mediciones

**Modelos de prueba (sujetos):**
- phi3:mini (Microsoft, 3.8B parámetros, 2.2 GB)
- llama3.2:3b (Meta, 3B parámetros, 2.0 GB)
- gemma2:2b (Google, 2B parámetros, 1.6 GB)

Tres empresas distintas y tres tamaños distintos para evaluar si la
degradación depende del tamaño, la arquitectura, o ambas.

### Por qué datos inventados y no conocimiento general

La primera versión usaba "la capital de Australia es Canberra". Todos
los modelos acertaban siempre porque Canberra es conocimiento que ya
tienen de su entrenamiento, no información que retuvieron de la
conversación. Se cambió a datos inventados (códigos secretos, números
de expediente) que el modelo solo puede saber si los retuvo del contexto.
Se implementó un banco de tres datos que rotan aleatoriamente.

## Guardarraíles — qué NO hace el agente

- No genera conclusiones estadísticas ni interpreta resultados
- No toma decisiones sobre qué modelo es "mejor"
- No accede a datos personales ni confidenciales
- No modifica los modelos evaluados ni sus parámetros internos
- Solo ejecuta pruebas y reporta acierto/fallo
- El análisis estadístico y la interpretación son responsabilidad
  del equipo investigador

La verificación de la salida es determinística: se busca si el dato
exacto aparece en la respuesta del modelo. No se usa otro LLM como
evaluador porque la tarea no requiere juicio, solo comparación de texto.

## Iteraciones del diseño

### v1 — Párrafos estáticos
Texto de relleno pegado con el dato clave entre medio.
Problema: todos los modelos acertaban, era demasiado fácil.

### v2 — Conversación real con preguntas fijas
Se cambió a conversación ida y vuelta usando la API de chat de Ollama.
Problema: las preguntas del usuario eran fijas y no seguían el hilo.

### v3 — Conversación natural generada
qwen2.5 genera las preguntas del usuario basándose en las respuestas
del modelo de prueba. La conversación fluye naturalmente y cambia
de tema después del dato clave.

### v4 — Dato inventado con banco rotativo
Se descubrió que los datos de conocimiento general no medían retención
sino conocimiento previo. Se cambió a datos inventados que el modelo
solo puede saber si los retuvo de la conversación.

### v5 — Optimización de recursos y timer
Se cambió qwen2.5 (4.7 GB) por qwen2.5:1.5b (986 MB) como orquestador
para reducir tiempos de ejecución y permitir reproducibilidad en PCs
con 8 GB de RAM. Se agregó medición automática de tiempo por prueba.

## Resultados preliminares

| Modelo | Parámetros | Turnos | Posición | Tokens | Tiempo | Resultado |
|--------|-----------|--------|----------|--------|--------|-----------|
| gemma2:2b (Google) | 2B | 5 | inicio | 1903 | 1:40 | ACIERTO |
| gemma2:2b (Google) | 2B | 10 | inicio | 2224 | ~3 min | ACIERTO |
| gemma2:2b (Google) | 2B | 20 | inicio | 9548 | 6:30 | FALLO |
| phi3:mini (Microsoft) | 3.8B | 5 | inicio | 10259 | 9:00 | FALLO |
| phi3:mini (Microsoft) | 3.8B | 10 | inicio | 4474 | 5:00 | FALLO |
| phi3:mini (Microsoft) | 3.8B | 20 | inicio | 8889 | 11:33 | FALLO |
| llama3.2:3b (Meta) | 3B | 5 | inicio | 1728 | 0:58 | FALLO |
| llama3.2:3b (Meta) | 3B | 10 | inicio | 4361 | 2:40 | FALLO |
| llama3.2:3b (Meta) | 3B | 20 | inicio | 10605 | 6:30 | FALLO |

### Hallazgos principales

1. **gemma2:2b es el más resiliente**: Es el único modelo que acertó
   con 5 y 10 turnos. Falla a partir de 20 turnos.

2. **El tamaño no garantiza retención**: phi3:mini (3.8B) falló desde
   5 turnos a pesar de ser el modelo más grande. Genera respuestas
   muy largas (10259 tokens en 5 turnos vs 1903 de gemma2:2b) que
   saturan su propia ventana de contexto.

3. **llama3.2:3b tiene filtros de seguridad**: Se negó a procesar
   datos que suenan a información sensible ("clave de acceso al
   laboratorio"). No es un fallo de retención sino un comportamiento
   de seguridad del modelo.

4. **Se observaron cuatro tipos de fallo distintos**:
   - Alucinación: el modelo inventa un dato falso con confianza
   - Admisión: dice "no tengo esa información"
   - Negación de capacidad: dice "no puedo recordar conversaciones"
   - Alucinación narrativa: reinterpreta el dato como ficción
     (phi3:mini convirtió "código 7492" en una leyenda cósmica)

5. **El orquestador también falla**: qwen2.5:1.5b a veces omite
   parámetros al llamar la herramienta o envía sinónimos como
   "inicial" en vez de "inicio", lo cual requirió manejo robusto
   de entrada en el código.

## Requisitos

- Python 3.12+
- Ollama instalado (https://ollama.ai)
- 8 GB de RAM mínimo (16 GB recomendado)
- GPU opcional (6 GB VRAM recomendado, acelera la ejecución)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/CristianVallejo0104/Consultoria.git
cd Consultoria

# Crear entorno virtual
python3 -m venv venv                # Linux/Mac
python -m venv venv                 # Windows

# Activar entorno virtual
source venv/bin/activate            # Linux/Mac
venv\Scripts\activate               # Windows

# Instalar dependencias
pip install -r requirements.txt

# Descargar los modelos necesarios en Ollama
ollama pull qwen2.5:1.5b
ollama pull phi3:mini
ollama pull llama3.2:3b
ollama pull gemma2:2b
```

## Uso

```bash
source venv/bin/activate            # Linux/Mac
venv\Scripts\activate               # Windows
python3 agente.py                   # Linux/Mac
python agente.py                    # Windows
```

El programa pide tres datos:
- **Modelo a evaluar:** phi3:mini, llama3.2:3b o gemma2:2b
- **Posición del dato:** inicio, mitad o final
- **Número de turnos:** 5, 10 o 20

Los resultados se guardan en resultados.txt con la conversación
completa, el tiempo de ejecución y si acertó o falló.

## Tiempos aproximados de ejecución

| Turnos | Con GPU (6 GB VRAM) |
|--------|---------------------|
| 5      | ~1-9 min            |
| 10     | ~3-5 min            |
| 20     | ~6-12 min           |

Los tiempos varían según el modelo. phi3:mini es el más lento
por generar respuestas más largas. Sin GPU los tiempos se
multiplican aproximadamente por 3.

## Estructura del proyecto
consultoria-investigacion/
├── agente.py # Agente evaluador principal
├── requirements.txt # Dependencias con versiones fijadas
├── resultados.txt # Resultados de las evaluaciones (generado)
├── .gitignore
└── README.md


## Limitaciones conocidas

- La métrica de evaluación es binaria (acierto/fallo). No captura
  degradación parcial como loops repetitivos o alucinaciones
- Cada ejecución puede usar un dato clave diferente por el banco
  rotativo, lo cual introduce variabilidad entre corridas
- Los datos inventados que suenan a información sensible pueden
  activar filtros de seguridad en algunos modelos (llama3.2:3b)
- El orquestador qwen2.5:1.5b a veces omite parámetros o envía
  sinónimos inesperados al llamar la herramienta
- Falta validación con posiciones mitad y final (solo se probó inicio)
- Se requieren repeticiones para confirmar patrones estadísticamente

## Autores

- Juan Pablo Tibamoso
- Cristian Vallejo

Consultoría e Investigación - Pregrado en Estadística
Universidad Santo Tomás - Bogotá, Colombia
Docente: Javier Mauricio Sierra