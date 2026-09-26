# Registro de decisiones

Cada entrada documenta una decisión de diseño con su alternativa descartada, como exige la rúbrica del curso.

---

## D-01 · Reemplazar `gemma2:2b` por `gemma3:4b` como modelo local de Google

**Fecha:** 2026-09-23
**Estado:** verificado con `ollama show`

**Contexto.** El anteproyecto evaluaba `phi3:mini`, `llama3.2:3b` y `gemma2:2b`. Al migrar la longitud de la conversación de turnos a niveles de tokens, se quieren niveles de 10K a 30K. `gemma2:2b` tiene una ventana de 8,192 tokens, por lo que no puede recibir esos niveles.

**Decisión.** Usar `gemma3:4b` (Google) en el diseño factorial. Se conserva `gemma2:2b` como referencia a un nivel bajo (5K).

**Ficha verificada de `gemma3:4b`:** 4.3B parámetros, ventana 131,072, cuantización Q4_K_M.

**Alternativas descartadas:**
- Mantener `gemma2:2b` con niveles ≤5K: restringe todo el estudio a la capacidad de un solo modelo.
- Excluir a Google: rompe la regla de un modelo por empresa.
- Usar otro modelo ya instalado (`llama3.1`, `llama3.2:1b`, `qwen2.5`/`qwen3.5`): repiten empresa (Meta) o son de Alibaba, la misma del orquestador, lo que introduce sesgo de familia.

**Justificación.** La decisión responde a una restricción de diseño (ventana de contexto), no a resultados observados: se tomó antes de correr datos con el modelo nuevo.

**Consecuencias.** El hallazgo del primer corte (`gemma2:2b` fue el más resiliente con la ventana más pequeña) queda como resultado preliminar y ya no se replica en el diseño final, salvo la referencia a 5K. Desviación respecto al anteproyecto.

---

## D-02 · Pagar créditos de OpenRouter en lugar de depender de APIs gratuitas

**Fecha:** 2026-09-23

**Contexto.** Se probaron cuatro proveedores cloud gratuitos, con estos problemas observados:
- Groq (gratis): límite de 8,000 tokens/min en `gpt-oss` y de 1,000 tokens/min de salida en `qwen`; las conversaciones fallaban a mitad con HTTP 429.
- NVIDIA (gratis): ~7 min por corrida de 5 turnos, y el endpoint `deepseek-v4-flash-0731` se anunció como deprecado con ~5 días de aviso.
- Gemini: sobrecarga intermitente (HTTP 503).
- OpenRouter `:free`: límites propios, y los modelos de Google heredan los límites de Google AI Studio (rate limit inmediato en todas las pruebas).

**Decisión.** Pagar ~US$20 en créditos de OpenRouter y usar modelos de pago baratos.

**Alternativas descartadas.** Seguir con los planes gratuitos: sus límites producen corridas inválidas (429/503) que no miden retención.

**Justificación.** Los niveles de 10K a 30K tokens superan los límites por minuto de los planes gratuitos, y el diseño necesita un proveedor estable.

**Pendiente.** Calcular el costo real con los precios de cada modelo antes de pagar.

---

## D-03 · Laya explorado y pospuesto como clasificador de tipo de fallo

**Fecha:** 2026-09-26
**Entorno.** Explorado en `~/explorar_laya` (venv separado, `venv-laya`), fuera de este repositorio, por conflicto de dependencias (`torch`/`transformers`) con el entorno de CrewAI. Lee los JSON ya generados en `resultados/json/`; código de la exploración no versionado aquí.

**Contexto.** Se planeaba un clasificador de tipo de fallo con juicio de lenguaje (alucinación, admisión, negación de capacidad, alucinación narrativa). Laya (`convaiinnovations/laya`) es un modelo de decisión de 421M de parámetros (ModernBERT-large) que da probabilidades calibradas sin generar texto.

**Experimentos realizados (evidencia real, sobre 13 corridas válidas del primer corte):**
- Pregunta tipo `choice` (elegir entre las 5 categorías): 38% de coincidencia con `verificar_acierto()` — cercano al azar (20%).
- Pregunta tipo `noul` (sí/no binario, "¿acertó?"): 100% de coincidencia, con separación clara de probabilidad (0.77–0.92 en aciertos reales, 0.095–0.167 en fallos reales).
- El checkpoint reporta en tiempo de ejecución que sus temperaturas de calibración están fuera de rango válido (`invalid temperatures... outside [0.5, 5]`); su confianza debe tratarse como no calibrada.
- Se probó también `convaiinnovations/laya-multilingual` (322M, mmBERT-base) sobre los mismos 13 casos, esperando mejor desempeño en español: rindió peor que el checkpoint inglés (`choice` 62%, `noul` 62%, frente a 38%/100% del inglés). Contraintuitivo respecto a la documentación oficial, que recomienda el multilingüe para "cualquier cosa que no sea inglés".
- Cascada `noul` → `choice` (clasificar tipo solo si `noul` indica fallo): probada sobre los 2 únicos fallos reales disponibles; clasificación cualitativamente razonable pero con confianza baja (0.03–0.11) y muestra insuficiente para validar.

**Decisión.** Posponer la implementación de Laya como clasificador hasta contar con un dataset etiquetado de tamaño suficiente (decenas o cientos de fallos reales, no 2). Si se retoma, usar el checkpoint inglés (`laya`) como base para fine-tuning, no el multilingüe, según la evidencia empírica de arriba.

**Alternativas descartadas.**
- Implementar ya el clasificador con Laya zero-shot: descartado por el 38% en `choice`, cercano al azar.
- Usar `laya-multilingual` por ser el recomendado para español: descartado por rendir peor que el inglés en pruebas reales.

**Fuentes de respaldo para la taxonomía** (independientes de si se usa Laya o no):
- Huang et al. (2023), *"A Survey on Hallucination in Large Language Models"*: "alucinación" → *Context Inconsistency* (Faithfulness Hallucination); "alucinación narrativa" → adaptación de *Factual Fabrication*.
- Zhang et al. (2023), *"Siren's Song in the AI Ocean"*: "alucinación" → *Context-Conflicting Hallucination* (contradice la propia conversación previa, más específico que Huang et al. para nuestro caso conversacional); "admisión"/"negación de capacidad" → *Under-informativeness*, categoría explícitamente distinta de alucinación en ese paper.
- Wen et al. (2025), *"Know Your Limits: A Survey of Abstention in LLMs"*: "admisión"/"negación de capacidad" → perspectiva de conocimiento del modelo (el sistema debería abstenerse si no tiene confianza suficiente); "rechazo de seguridad" → perspectiva de valores humanos.

Estas categorías (admisión, negación de capacidad) son observación propia del primer corte — los papers dan el marco conceptual bajo el que encajan, no las nombran textualmente.

**Pendiente.** Etiquetado manual (Cristian y Juan Pablo, por separado, con kappa de Cohen) de las respuestas del piloto y de las 270 corridas finales, para construir el dataset de entrenamiento.

---

## D-04 · Evaluador de calidad de texto con LLM juez (exploratorio)

**Fecha:** 2026-09-26
**Archivo.** `evaluar_calidad_texto.py`, en la raíz de este repositorio.

**Contexto.** El profesor pidió verificar la calidad del texto generado en las conversaciones. Se decidió evaluar los turnos de "Usuario" (generador de relleno, `qwen2.5:1.5b`), no los del modelo evaluado, porque es el texto enteramente artificial y donde existe riesgo real de invalidar el experimento si suena poco natural. **Pendiente de confirmar con el profesor** si también se espera evaluar el lado del modelo evaluado.

**Método.** Se adaptaron las dimensiones de Mehri y Eskenazi (2020, *"USR: An Unsupervised and Reference Free Evaluation Metric for Dialog Generation"*): naturalidad, coherencia e interés (se omite *groundedness*, la cuarta dimensión del paper, porque se solaparía con la variable de retención ya medida aparte). Se miden con un LLM juez (`qwen2.5:1.5b`) siguiendo el mecanismo de razonamiento paso a paso de G-Eval (Liu et al., 2023), **no** con el método original de USR (modelos entrenados tipo RoBERTa con regresión contra humanos). Es una adaptación explícita y parcial: se toma el "qué medir" de un paper y el "cómo medirlo" de otro.

**Respaldo del método (LLM como juez).** Zheng et al. (2023), *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"*: valida que un LLM juez puede aproximar bien el juicio humano (>80% de acuerdo en su estudio), pero documenta sesgos conocidos: posición, verbosidad (prefiere respuestas más largas por serlo) y auto-preferencia (favorece texto de su propia familia).

**Hallazgo real (evidencia, no hipótesis).** En una muestra de 5 conversaciones, se detectaron turnos de "Usuario" cortados a mitad de frase o de palabra (ej.: *"...evoluciona rápido. ¿En qué tipo de IA te interesaría saber más? Por ejemplo, podríamos hablar sobre el aprendizaje automático o la inteligencia artific"*). El LLM juez no penalizó consistentemente estos cortes (dio Naturalidad 4/5 e Interés 5/5 a esa conversación) — consistente con el sesgo de verbosidad documentado en Zheng et al. (2023).

**Estado de validación.** Sin validar contra criterio humano. Pendiente: comparar las notas del LLM juez contra una lectura propia de las mismas conversaciones, antes de usar estos números en el análisis final.

**Alternativas descartadas.**
- Evaluación 100% manual (leer todas las conversaciones a mano): más lenta a escala; se usa como validación de una muestra, no como método principal.
- Reimplementar el método original de USR (modelos entrenados): fuera del alcance de tiempo del proyecto.

---

## D-05 · Justificación del diseño factorial con literatura del propio campo

**Fecha:** 2026-09-26

**Contexto.** Se buscó respaldo para el diseño factorial (modelo × posición × nivel de tokens × réplicas), preferiblemente en literatura del campo de evaluación de LLMs y no solo en un texto de estadística general.

**Fuentes verificadas directamente en el PDF (no solo por resumen de terceros):**
- Liu et al. (2023), *"Lost in the Middle: How Language Models Use Long Contexts"* — el paper base del proyecto. Usa 2,655 preguntas, varía sistemáticamente la posición del documento clave y el número total de documentos (k = 10, 20, 30), sobre 6 modelos (GPT-3.5-Turbo, GPT-3.5-Turbo-16K, Claude-1.3, Claude-1.3-100k, MPT-30B-Instruct, LongChat-13B). **No usa el término "diseño de bloques"** en ningún lugar del texto — verificado por búsqueda directa en el PDF completo; una fuente de IA (Gemini) atribuyó ese término al paper sin que apareciera ahí.
- Zhang et al. (2024), *"Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding"* — extiende el mismo esquema a 7 modelos (Llama-2-chat-7B/13B, StableBeluga-7B/13B, Vicuna-7B, Vicuna-7B-16K), comparando contra métodos de la literatura (PI, Self-Extend) con estudio de ablación (sección 4.3) sobre estrategias de asignación y rangos de escala.

**Decisión.** Justificar el diseño factorial citando esta línea de trabajo (posición × longitud × modelo, variados sistemáticamente), en vez de citar únicamente un libro de estadística general de diseño de experimentos. Se describe como "variación sistemática de factores", sin forzar terminología estadística (bloques, factorial) que las fuentes originales no usan.

**Diferencia con nuestro diseño.** Liu et al. y Zhang et al. insertan el dato clave en un documento recuperado externamente (memoria no paramétrica, estilo RAG). Nuestro diseño lo inserta dentro de la propia conversación (memoria de trabajo conversacional) — la misma distinción ya documentada al descartar RAG como herramienta aplicable.