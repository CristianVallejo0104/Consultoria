# Respuestas del banco en C-v1 (NotebookLM con el protocolo v1)

Cuaderno «Evaluación Automatizada de Generación Aumentada por Recuperación», con el protocolo v1 en las
instrucciones del chat. Preguntas hechas por Juan Pablo el 5 nov 2026. Respuestas copiadas tal como salieron
(la pérdida de saltos de línea es del copiado). Los números sueltos después de las citas son las marcas de cita
de NotebookLM.

## 1

¿Qué correlación de Spearman obtiene G-Eval con GPT-4 en la tarea de resumen?

> En la tarea de resumen (text summarization), G-EVAL con GPT-4 (G-EVAL-4) obtiene una correlación de Spearman promedio de 0.514 con los juicios humanos (Liu et al., 2023, pág. 1)1.En el benchmark SummEval, el desglose de la correlación de Spearman ($\rho$) a nivel de resumen para cada dimensión evaluada es el siguiente (Liu et al., 2023, pág. 4, Tabla 1)2:Coherencia (Coherence): 0.582 (Liu et al., 2023, pág. 4, Tabla 1)2.Consistencia (Consistency): 0.507 (Liu et al., 2023, pág. 4, Tabla 1)2.Fluidez (Fluency): 0.455 (Liu et al., 2023, pág. 4, Tabla 1)2.Relevancia (Relevance): 0.547 (Liu et al., 2023, pág. 4, Tabla 1)2.Promedio (AVG): 0.514 (Liu et al., 2023, pág. 4, Tabla 1)2.Adicionalmente, en la evaluación de consistencia/alucinaciones en resumen sobre el benchmark QAGS, G-EVAL-4 obtiene las siguientes correlaciones de Spearman (Liu et al., 2023, pág. 5, Tabla 3)3:QAGS-CNN: 0.685 (Liu et al., 2023, pág. 5, Tabla 3)3.QAGS-XSUM: 0.537 (Liu et al., 2023, pág. 5, Tabla 3)3.Promedio: 0.611 (Liu et al., 2023, pág. 5, Tabla 3)3.

## 2

¿Qué método usa RAG para encontrar los K documentos más relevantes dada una consulta?

> Para encontrar los $K$ documentos más relevantes dada una consulta, RAG formula la selección como un problema de búsqueda de producto interno máximo (Maximum Inner Product Search, MIPS) (Lewis et al., 2020, pág. 3). Concretamente, utiliza el recuperador neuronal denso DPR (Dense Passage Retriever) con una arquitectura bi-encoder para obtener las representaciones densas de la consulta y de los documentos, y resuelve la búsqueda de los $K$ documentos superiores construyendo un índice MIPS mediante la biblioteca FAISS con una aproximación de mundos pequeños jerárquicos navegables (Hierarchical Navigable Small World, HNSW) para recuperación rápida en tiempo sublineal (Lewis et al., 2020, págs. 2–4).

## 3

¿Con qué dos tareas analizan Liu et al. cómo los modelos usan el contexto largo?

> Liu et al. analizan cómo los modelos de lenguaje utilizan el contexto largo mediante dos tareas principales (Liu et al., 2023, pág. 1):Respuesta a preguntas sobre múltiples documentos (multi-document question answering) (Liu et al., 2023, págs. 1, 2).Recuperación sintética de clave-valor (synthetic key-value retrieval) (Liu et al., 2023, págs. 1, 5).

## 4

¿Qué forma tiene la curva de rendimiento cuando cambia la posición de la información relevante en el contexto?

> Tiene una curva de rendimiento en forma de U (U-shaped performance curve) (Liu et al., 2023, págs. 1, 2). El rendimiento del modelo es significativamente más alto cuando la información relevante se ubica al principio (primacy bias) o al final del contexto de entrada (recency bias), y se degrada de forma sustancial cuando la información relevante se sitúa en medio del contexto largo (Liu et al., 2023, págs. 2, 4).

## 5

¿Qué ganancia promedio de precisión logra Ms-PoE en el benchmark Zero-SCROLLS?

> Ms-PoE logra una ganancia de precisión promedio de hasta 3.8 puntos en el benchmark Zero-SCROLLS en comparación con los modelos de lenguaje originales (Zhang et al., 2024, págs. 1, 2, 6).

## 16

¿Qué es CrewAI y cómo coordina a los agentes?

> No está en las fuentes cargadas.
