# Evaluador de Confiabilidad de LLMs en Conversaciones Largas

Agente de IA que evalúa si los modelos de lenguaje pierden información
según la longitud de la conversación y la posición del dato clave.
Proyecto de Consultoría e Investigación - Universidad Santo Tomás.

## Qué hace

El agente genera conversaciones naturales con un modelo de prueba,
esconde un dato clave en una posición controlada (inicio, mitad o final),
y al finalizar le pregunta por ese dato para verificar si lo retuvo.

El flujo de trabajo es:

1. El usuario elige modelo, posición del dato y cantidad de turnos
2. El agente (qwen2.5) decide cómo ejecutar la evaluación
3. La herramienta inicia una conversación real con el modelo de prueba
4. En cada turno, qwen2.5 genera preguntas naturales basadas en las
   respuestas del modelo, simulando un usuario real
5. En el turno indicado, se inserta el dato clave de forma natural
6. Al final se pregunta por el dato y se evalúa si acertó
7. El reporte completo se guarda en resultados.txt

## Decisiones de diseño

### Por qué un agente y no un script

La tarea requiere interpretar instrucciones en lenguaje natural y
decidir qué herramienta usar con qué parámetros. El agente recibe
"prueba los tres modelos con 10 turnos" y él decide cuántas veces
llamar la herramienta y con qué valores.

### Por qué un solo agente y no varios

Las tres operaciones (generar conversación, consultar modelo, evaluar)
son pasos secuenciales de un mismo proceso, no roles distintos que
requieran razonamiento independiente. Un segundo agente evaluador
sería innecesario porque la evaluación es determinística (verificar
si una palabra aparece en la respuesta).

### Por qué CrewAI

- Estructura clara con pocos conceptos (Agent, Task, Tool, Crew)
- Soporte nativo para Ollama (modelos locales)
- Fácil de explicar y sustentar
- Alternativas descartadas: LangChain (demasiado complejo para 3
  semanas), AutoGen (orientado a conversación entre agentes, no a
  flujos con herramientas)

### Elección de modelos

**Agente (orquestador):** qwen2.5 (Alibaba, 4.7 GB)
- Elegido por su capacidad de seguir instrucciones estructuradas,
  necesaria para el formato ReAct que usa CrewAI
- Separado del experimento para no contaminar las mediciones

**Modelos de prueba (sujetos):**
- llama3.1 (Meta, 4.9 GB) - modelo grande
- phi3:mini (Microsoft, 2.2 GB) - modelo mediano
- gemma2:2b (Google, 1.6 GB) - modelo pequeño

Tres empresas distintas y tres tamaños distintos para evaluar si la
degradación depende del tamaño, la arquitectura, o ambas.

### Conversación natural vs párrafos pegados

La primera versión usaba párrafos de relleno estáticos. Todos los
modelos acertaban porque era demasiado fácil. Se cambió a
conversaciones reales ida y vuelta donde qwen2.5 genera las preguntas
del usuario basándose en las respuestas del modelo de prueba, lo cual
refleja mejor el uso real de un LLM.

## Requisitos

- Python 3.12+
- Ollama instalado (https://ollama.ai)
- 8 GB de RAM mínimo (16 GB recomendado)
- GPU opcional (acelera la ejecución pero no es obligatoria)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/CristianVallejo0104/Consultoria.git
cd Consultoria

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar los modelos necesarios en Ollama
ollama pull qwen2.5
ollama pull llama3.1
ollama pull phi3:mini
ollama pull gemma2:2b
```

## Uso

```bash
source venv/bin/activate
python3 agente.py
```

El programa pide tres datos:
- **Modelo a evaluar:** llama3.1, phi3:mini o gemma2:2b
- **Posición del dato:** inicio, mitad o final
- **Número de turnos:** 5, 10 o 20

Los resultados se guardan en `resultados.txt` con la conversación
completa, la respuesta del modelo y si acertó o falló.

## Tiempos aproximados de ejecución

| Turnos | Con GPU (6 GB) | Sin GPU (CPU) |
|--------|---------------|---------------|
| 5      | ~12 min        | ~30 min        |
| 10     | ~25 min        | ~60 min       |
| 20     | ~50 min       | ~2 horas       |

Los tiempos varían según el modelo y la longitud de las respuestas.

## Estructura del proyecto


## Limitaciones conocidas

- La métrica de evaluación es binaria (acierto/fallo por contención
  de texto). No captura degradación parcial como loops repetitivos
  o alucinaciones que se observaron en phi3:mini
- El intercambio de modelos en VRAM causa tiempos largos de ejecución
  en GPUs con poca memoria
- Los mensajes del usuario generados por qwen2.5 a veces son
  repetitivos ("Eso suena interesante")
- El dato clave ("la capital de Australia es Canberra") puede ser
  respondido por conocimiento del modelo y no por retención de la
  conversación

## Autores

- Juan Pablo Tibamoso
- Cristian Vallejo

Consultoría e Investigación - Pregrado en Estadística
Universidad Santo Tomás - Bogotá, Colombia
Docente: Javier Mauricio Sierra