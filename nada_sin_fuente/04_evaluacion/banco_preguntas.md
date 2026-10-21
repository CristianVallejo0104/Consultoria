# Banco de evaluación

- Entre 15 y 20 preguntas en total.
- Al menos 3 cuya respuesta **no** está en el corpus (marcadas «Fuera»): miden si el sistema se abstiene o inventa.
- La respuesta conocida y su ubicación se escriben **antes** de preguntarle al sistema.
- Cada pregunta se hace **dos veces**: en `A` (chat sin fuentes, el control) y en `C-v1` (el sistema con
  protocolo v1). Si hay v2, repetir en `C-v2`. Sin `A` no se puede decir cuánto mejoró el sistema.

## Resumen

| | A · control | C-v1 · sistema |
|---|---|---|
| Dentro del corpus: correctas y sostenidas por fragmento real | __ de __ (IC exacto 95 % [__, __]) | __ de __ (IC exacto 95 % [__, __]) |
| Fuera del corpus: se abstuvo | __ de __ | __ de __ |
| Fuera del corpus: inventó | __ de __ | __ de __ |

En A no hay fragmento que citar: ahí «correcta» es que coincida con la respuesta conocida.
Los intervalos se calculan en R con `binom.test(k, n)$conf.int`.

## Preguntas

| # | Pregunta | Respuesta conocida | Dónde está (documento, página) | A: respuesta obtenida | A: ¿correcta? | C-v1: respuesta obtenida | C-v1: ¿sostenida por un fragmento real? |
|---|---|---|---|---|---|---|---|
| 1 | ¿Qué correlación de Spearman obtiene G-Eval con GPT-4 en la tarea de resumen? | 0,514 | liu2023_GEVAL.pdf, p. 1 (resumen) | | sí / no | | sí / no |
| 2 | ¿Qué método usa RAG para encontrar los K documentos más relevantes dada una consulta? | Maximum Inner Product Search (MIPS) | RAG.pdf, p. 2 (Figura 1) | | sí / no | | sí / no |
| 3 | ¿Con qué dos tareas analizan Liu et al. cómo los modelos usan el contexto largo? | Respuesta a preguntas sobre múltiples documentos y recuperación de clave-valor (multi-document question answering y key-value retrieval) | liu2023_lost_in_the_middle.pdf, p. 1 (resumen) | | sí / no | | sí / no |
| 4 | ¿Qué forma tiene la curva de rendimiento cuando cambia la posición de la información relevante en el contexto? | Curva en forma de U (mejor al inicio y al final, peor en el medio) | liu2023_lost_in_the_middle.pdf, p. 1 (Figura 1) | | sí / no | | sí / no |
| 5 | ¿Qué ganancia promedio de precisión logra Ms-PoE en el benchmark Zero-SCROLLS? | Hasta 3,8 puntos | zhang2024_found_in_the_middle.pdf, p. 1 (resumen) | | sí / no | | sí / no |
| 6 | ¿Qué tres aspectos de calidad evalúa RAGAS? | Faithfulness, Answer Relevance y Context Relevance | RAGAS.pdf, p. 3 | | sí / no | | sí / no |
| 7 | ¿Qué modelo usa RAGAS para evaluar todos sus prompts en su implementación? | gpt-3.5-turbo-16k, disponible mediante la API de OpenAI | RAGAS.pdf, p. 3 | | sí / no | | sí / no |
| 8 | ¿En qué conferencia se publicó ReAct? | ICLR 2023 | yao2022_react.pdf, p. 1 (encabezado) | | sí / no | | sí / no |
| 9 | ¿En qué dos benchmarks de toma de decisiones supera ReAct a los métodos de imitación y refuerzo, y por cuánto? | ALFWorld y WebShop, por 34 % y 10 % de éxito absoluto respectivamente | yao2022_react.pdf, p. 1 (resumen) | | sí / no | | sí / no |
| 10 | ¿En qué dos tipos principales clasifican Huang et al. las alucinaciones? | Factuality hallucination y faithfulness hallucination | huang2023_hallucination_survey.pdf, p. 2 | | sí / no | | sí / no |
| 11 | ¿Cuáles son las dos subcategorías de la «Factual Contradiction» en Huang et al.? | Entity-error hallucination y relation-error hallucination | huang2023_hallucination_survey.pdf, p. 6 | | sí / no | | sí / no |
| 12 | ¿Cuáles son los tres tipos de alucinación que muestra la Figura 1 de Siren's Song? | Input-conflicting, context-conflicting y fact-conflicting | zhang2023_sirens_song.pdf, p. 2 (Figura 1) | | sí / no | | sí / no |
| 13 | ¿Qué nivel de acuerdo con las preferencias humanas logra GPT-4 como juez, según Zheng et al.? | Más del 80 %, el mismo nivel de acuerdo que hay entre humanos | zheng2023_llm_as_judge.pdf, p. 1 (resumen) | | sí / no | | sí / no |
| 14 | ¿Qué seis puntajes recibe cada respuesta en la anotación humana de Mehri y Eskenazi? | Understandable, Natural, Maintains Context, Interesting, Uses Knowledge y Overall Quality | mehri2020_user.pdf, p. 2 | | sí / no | | sí / no |
| 15 | ¿Desde qué tres perspectivas analiza Wen et al. cuándo debe abstenerse un modelo? | Perspectiva de la consulta, del conocimiento del modelo y de los valores humanos | KnowYourLimitsASurveyofAbstentioninLargeLanguageModels.pdf, pp. 2–3 | | sí / no | | sí / no |
| 16 | [Fuera] ¿Qué es CrewAI y cómo coordina a los agentes? | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |
| 17 | [Fuera] ¿Qué es Ollama y para qué sirve? | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |
| 18 | [Fuera] ¿Qué es el Model Context Protocol (MCP) y para qué sirve? | No está en el corpus | — | | se abstuvo / inventó | | se abstuvo / inventó |