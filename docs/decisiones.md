# Registro de decisiones

Cada entrada documenta una decisión de diseño con su alternativa descartada, como exige la rúbrica del curso.

---

## D-01 · Reemplazar `gemma2:2b` por `gemma3:4b` como modelo local de Google

**Fecha:** 2026-09-23
**Estado:** verificado con `ollama show`

**Contexto.** El anteproyecto evaluaba `phi3:mini`, `llama3.2:3b` y `gemma2:2b`. Al migrar la longitud de la conversación de turnos a niveles de tokens, se querían niveles de 10K a 30K; los niveles finales son 4K, 8K y 12K (D-06) y `gemma2:2b` no llega a 12K.

**Decisión.** Adoptar `gemma3:4b` (Google) como modelo de Google en el diseño factorial. `gemma2:2b` se retiene únicamente como evidencia del primer corte (resultado preliminar, una réplica por celda); no se ejecutan corridas adicionales con este modelo en el diseño final.
- Ejecutar `gemma2:2b` como referencia a 4K tokens: descartado; introduce una excepción a la regla de un modelo por empresa (D-10) y consume cómputo fuera del diseño. El hallazgo del primer corte se conserva como resultado preliminar.


**Ficha verificada de `gemma3:4b`:** 4.3B parámetros, ventana 131,072, cuantización Q4_K_M.

**Alternativas descartadas:**
- Mantener `gemma2:2b` con niveles ≤5K: restringe todo el estudio a la capacidad de un solo modelo.
- Excluir a Google: rompe la regla de un modelo por empresa.
- Usar otro modelo ya instalado (`llama3.1`, `llama3.2:1b`, `qwen2.5`/`qwen3.5`): repiten empresa (Meta) o son de Alibaba, la misma del orquestador, lo que introduce sesgo de familia.

**Justificación.** La decisión responde a una restricción de diseño (ventana de contexto), no a resultados observados: se tomó antes de correr datos con el modelo nuevo.

**Consecuencias.** El hallazgo del primer corte (`gemma2:2b` fue el más resiliente con la ventana más pequeña) queda documentado como resultado preliminar y no se replica en el diseño final. Constituye una desviación respecto al anteproyecto, declarada y justificada.
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
- Pregunta tipo `choice` (5 categorías): 38% de coincidencia con `verificar_acierto()`, frente a 20% de azar uniforme; con n = 13 el porcentaje es inestable.
- Pregunta tipo `noul` (sí/no binario, "¿acertó?"): 100% de coincidencia, con separación clara de probabilidad (0.77–0.92 en aciertos reales, 0.095–0.167 en fallos reales).
- El checkpoint reporta en tiempo de ejecución que sus temperaturas de calibración están fuera de rango válido (`invalid temperatures... outside [0.5, 5]`); su confianza debe tratarse como no calibrada.
- Se probó también `convaiinnovations/laya-multilingual` (322M, mmBERT-base) sobre los mismos 13 casos, esperando mejor desempeño en español: rindió peor que el checkpoint inglés (`choice` 62%, `noul` 62%, frente a 38%/100% del inglés). Contraintuitivo respecto a la documentación oficial, que recomienda el multilingüe para "cualquier cosa que no sea inglés".
- Cascada `noul` → `choice` (clasificar tipo solo si `noul` indica fallo): probada sobre los 2 únicos fallos reales disponibles; clasificación cualitativamente razonable pero con confianza baja (0.03–0.11) y muestra insuficiente para validar.

**Decisión.** Posponer la implementación hasta contar con fallos reales etiquetados. La evidencia sobre el checkpoint es mixta: el inglés rindió mejor en `noul` (100% frente a 62%) y el multilingüe en `choice` (62% frente a 38%). Como el uso previsto es clasificar el tipo (`choice`), la elección de checkpoint queda abierta.

**Alternativas descartadas.**
- Implementar ya el clasificador con Laya zero-shot: descartado por el 38% en `choice` (frente a 20% de azar uniforme, con n = 13).
- Usar `laya-multilingual` por ser el recomendado para español: no descartado; rindió mejor en `choice` (62% frente a 38%) y peor en `noul` (62% frente a 100%).

**Fuentes de respaldo para la taxonomía** (independientes de si se usa Laya o no):
- Huang et al. (2023), *"A Survey on Hallucination in Large Language Models"*: "alucinación" → *Context Inconsistency* (Faithfulness Hallucination); "alucinación narrativa" → adaptación de *Factual Fabrication*.
- Zhang et al. (2023): "alucinación" → *Input-Conflicting* (cercano: se desvía de lo que el usuario dio, p. 3). *Context-Conflicting* es conflicto con lo que el propio modelo generó antes (p. 3) y no es nuestro caso. "Admisión"/"negación de capacidad" → *Under-informativeness* (p. 6). El "desvío" de phi3 (12K) → Huang *instruction inconsistency* (p. 7); Wen: reformular la pregunta no es abstención (p. 2).
- Wen et al. (2025), *"Know Your Limits: A Survey of Abstention in LLMs"*: "admisión"/"negación de capacidad" → perspectiva de conocimiento del modelo (el sistema debería abstenerse si no tiene confianza suficiente); "rechazo de seguridad" → perspectiva de valores humanos.

Estas categorías (admisión, negación de capacidad) son observación propia del primer corte — los papers dan el marco conceptual bajo el que encajan, no las nombran textualmente.

**Pendiente.** Etiquetado manual (Cristian y Juan Pablo, por separado, con kappa de Cohen) de las respuestas del piloto y de las 270 corridas finales, para construir el dataset de entrenamiento.

---

## D-04 · Evaluador de calidad de texto con LLM juez (exploratorio)

**Fecha:** 2026-09-26
**Archivo.** `evaluar_calidad_texto.py`, en la raíz de este repositorio.

**Contexto.** El profesor pidió verificar la calidad del texto generado en las conversaciones. Se decidió evaluar los turnos de "Usuario" (generador de relleno, `qwen2.5:1.5b`), no los del modelo evaluado, porque es el texto enteramente artificial y donde existe riesgo real de invalidar el experimento si suena poco natural. **Pendiente de confirmar con el profesor** si también se espera evaluar el lado del modelo evaluado.

**Método.** Se adaptaron tres dimensiones de USR (Mehri y Eskenazi, 2020, pp. 2–3): *Natural*, *Maintains Context* e *Interesting* (naturalidad, coherencia, interés). Se omite *Uses Knowledge*, que se solaparía con la retención.

**Respaldo del método.** Zheng et al. (2023): jueces fuertes como GPT-4 superan el 80% de acuerdo con humanos (p. 1); nuestro juez es un modelo de 1.5B, sin validar. Describen sesgos de posición, verbosidad y autopreferencia; en esta última sus datos no permiten concluir que exista (p. 5).

**Hallazgo.** En 5 conversaciones se detectaron turnos de usuario cortados a mitad de frase. Causa: el límite de 200 caracteres en `_generar_relleno`, ya corregido (ahora corta en el último fin de oración). El juez no penalizó esos cortes de forma consistente; la causa de esa indulgencia no está establecida y no se atribuye al sesgo de verbosidad.

**Parámetros del juez (2026-09-30).** `temperature` 0, `num_ctx` 8,192, `num_predict` 600 y `timeout` 600 s. Con la ventana por defecto (4,096 tokens), la conversación más larga del piloto (`phi3:mini`, 12K; unos 18,000 caracteres de usuario) salió sin notas: el juez respondió 159,895 caracteres sin evaluar, lo que es consistente con que las instrucciones quedaran fuera de la ventana. Con los nuevos parámetros la evaluó (naturalidad 4, coherencia 5, interés 4). Con temperatura 0, 11 de las 12 notas de las cuatro conversaciones cortas se repitieron en tres corridas; la de interés de `gemma3:4b` (8K) varió (5, 3, 5). Las 5 conversaciones evaluadas son las primeras que devolvió el sistema de archivos, no una muestra aleatoria.

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
- Zhang et al. (2024), *"Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding"* — extiende el mismo esquema a siete LLM según el texto (p. 6), que nombra seis: Llama-2-chat-7B/13B, StableBeluga-7B/13B, Vicuna-7B y Vicuna-7B-16K,

**Decisión.** Justificar el diseño factorial citando esta línea de trabajo (posición × longitud × modelo, variados sistemáticamente), en vez de citar únicamente un libro de estadística general de diseño de experimentos. Se describe como "variación sistemática de factores", sin forzar terminología estadística (bloques, factorial) que las fuentes originales no usan.

**Diferencia con nuestro diseño.** Liu et al. y Zhang et al. insertan el dato clave en un documento recuperado externamente (memoria no paramétrica, estilo RAG). Nuestro diseño lo inserta dentro de la propia conversación (memoria de trabajo conversacional) — la misma distinción ya documentada al descartar RAG como herramienta aplicable.

---

## D-06 · Migrar de turnos a niveles de tokens
**Fecha:** 2026-09-26
**Contexto.** "5 turnos" no es comparable entre modelos: en el primer corte phi3:mini
procesó 10,259 tokens en 5 turnos y gemma2:2b, 1,903 (Cuadro 3 del informe).
**Decisión.** El nivel es el contexto en la pregunta final, medido con
prompt_eval_count + eval_count de la última llamada. Niveles 4,000, 8,000 y 12,000.
Posición del dato en tokens: inicio = 2.º turno; mitad = al cruzar el 50 % del nivel;
final = al cruzar el 85 %. Constantes: num_ctx 16,384; tope común de 300 tokens por
respuesta; máximo 60 turnos; timeout 600 s. Una sola función (sin duplicar).
**Alternativas descartadas.** Seguir en turnos (plan B: versión en git); mantener dos
funciones (por turnos y por tokens); niveles candidatos 5K/10K/15K (razón: por documentar).
**Validación.** Piloto de 9 corridas, todas válidas; el contexto nunca decreció; el dato
de "mitad" entró entre el 50.2 % y el 58.4 % del nivel; el contexto final superó el
nominal entre 0.5 % y 10.3 % (se usará contexto_final como covariable).
**Límites.** Cada modelo usa su tokenizador; las cifras de ambos cortes no son
comparables; phi3:mini a 12K hizo 57 turnos con un máximo de 60.
**Pendiente.** Evaluar subir el máximo de turnos; guardar done_reason de Ollama.

---

## D-07 · Retirar del código los proveedores cloud gratuitos
**Fecha:** 2026-09-29
**Contexto.** D-02 decidió pagar OpenRouter; los planes gratuitos dieron corridas inválidas.
**Decisión.** agente.py conserva solo Ollama (local) y OpenRouter (nube). Se retiraron las
ramas de NVIDIA, Groq y Gemini. MODELOS_CLOUD queda vacío hasta cerrar el Diseño B.
**Alternativas descartadas.** Conservar las cuatro ramas (código sin decisión y cuatro claves).
**Consecuencia.** La versión anterior está en el commit previo a 3f1961a; los resultados de
los planes gratuitos quedan en resultados/pruebas/ como referencia.

---

## D-08 · Rol del agente: dos puertas de entrada a un mismo núcleo
**Fecha:** 2026-09-29
**Contexto.** El orquestador de 1.5B ha omitido parámetros y sustituido el modelo pedido
(lámina 21 del primer corte; decisiones anteriores).
**Decisión.** Las corridas masivas llaman ejecutar_evaluacion() desde correr_experimento.py;
el agente CrewAI queda como entrada interactiva en lenguaje natural.
**Alternativas descartadas.** Que el agente dirija el bucle; eliminar el agente.
**Justificación.** Lo determinista va en código; los agentes se reservan para juicio de
lenguaje (verificador de checkpoints, clasificador de fallos, analista), aún sin implementar.
**Nota.** Unificar con la entrada previa "Funciones puras + ejecutar_evaluacion()".

---

## D-09 · RAG, G-Eval y RAGAS: contrastados con el proyecto, no usados para medir retención
**Fecha:** 2026-09-30 (registrada)
**Contexto.** Se contrastó el estado del arte (Lewis et al. 2020; Liu, Y. et al. 2023; Es et al. 2023) con el proyecto, citando la fuente con página.
**Decisión.** Ninguna de las tres se usa para medir retención. RAG genera respuestas con documentos recuperados (no evalúa). RAGAS evalúa sistemas RAG sobre tripletas (pregunta, contexto recuperado, respuesta) con un LLM (`gpt-3.5-turbo-16k` vía OpenAI, p. 3). G-Eval evalúa la calidad de un texto con un LLM juez; su mecanismo sí se adapta a la calidad del texto de relleno (D-04).
**Alternativas descartadas.** Usar G-Eval para verificar retención (añade variabilidad donde conocemos la respuesta); adaptar *faithfulness* de RAGAS con la conversación como contexto (añade un juez LLM donde hay respuesta conocida); implementar RAG (no hay documentos que recuperar).
**Fuentes.** Lewis et al. v4 (pp. 1–2); Liu, Y. et al. v3 (pp. 1–4, 6); Es et al. v2 (pp. 1, 3–5).
**Pendiente.** Aclarar el alcance de «implementarlo y probarlo» para RAG.

---

## D-10 · Selección de modelos y roles
**Fecha:** 2026-09-30 (registrada; criterios del primer corte, lámina 12)
**Decisión.** Evaluados: un modelo por empresa (`phi3:mini`, `llama3.2:3b`, `gemma3:4b`). Orquestador y generador de relleno: `qwen2.5:1.5b` (Alibaba), una cuarta empresa. Ventana declarada ≥ 12,000 tokens.
**Alternativas descartadas.** Dos modelos de la misma empresa (sesgo de familia); orquestador de la familia de un evaluado (precaución ante la autopreferencia, que Zheng et al. describen pero no confirman, p. 5); `gemma2:2b` (8,192 < 12K, D-01); `llama3.1` (8B) y `qwen3.5` (6.6 GB) por no caber en 8 GB de RAM (criterio del primer corte, abierto: `phi3:mini` con `num_ctx` 16,384 ocupa 9.0 GB); `smollm2:1.7b` como orquestador (bucle infinito: no siguió ReAct).
**Límites.** Cuantización distinta (`phi3:mini` en Q4_0); el evaluador de calidad usa el mismo `qwen2.5:1.5b` que genera el relleno (D-04).
**Fuente.** `ollama show` (sep. 2026).

---

## D-11 · Medición determinista y manejo de corridas inválidas
**Fecha:** 2026-09-30 (registrada; decisiones del primer corte)
**Decisión.** Dato inventado (5 datos rotativos); verificación por cadena exacta (`verificar_acierto`); toda llamada que falla aborta la corrida y se registra como inválida (`invalida_tecnica`, `acierto = None`), sin contarse como fallo del modelo; errores tipados en un solo punto (`consultar_modelo`).
**Alternativas descartadas.** Dato real (todos acertaban por conocimiento previo); LLM juez para retención (ruido y circularidad; D-04 lo usa solo para calidad de texto); continuar con huecos (otro tratamiento); parche de errores en cada rama.
**Límites.** Acepta «me parece que era 3851» y no detecta contexto inventado; el rechazo de seguridad solo se detecta en las API en la nube.