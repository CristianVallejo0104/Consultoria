# c2_B: Consensus, plan gratis

Fecha y hora: 21 oct 2026, 5:45 pm
Herramienta: Consensus (consensus.app), plan gratis
Modo: la respuesta apareció marcada como "Pro", con "3 steps" y "20 papers read". No lo activé yo.

## Consulta
Dame 5 referencias académicas, con autores, año y DOI o enlace, sobre cómo los modelos de lenguaje pierden información en conversaciones largas.

## Respuesta completa
Consensus response

Pro


3 steps

2
2
.
6
M

Total papers found across all searches
Retrieved

7
9

Papers meeting relevance criteria, after deduplication
Eligible

2
0

Papers selected for the final analysis
Included

language models lose information in long conversations

21.4M results

large language models with long-context degradation, context window limitations, and information loss in multi-turn dialogue

1.2M results


Read

Abstracts and PDFs

20 papers read

Pérdida de información en modelos de lenguaje durante conversaciones largas
Los modelos de lenguaje tienden a sufrir una pérdida progresiva de contexto y degradación de rendimiento conforme aumenta la longitud o el número de turnos en una conversación 
Laban
2025
Kwan
2024
Li
2025
. A continuación se presentan 5 referencias académicas clave que analizan experimentalmente las causas, la posición del olvido y los mecanismos subyacentes de este fenómeno.

Referencias Académicas Principales
Autores y Año	Título del Trabajo	Hallazgo Clave sobre la Pérdida de Información	Enlace / Identificador
Nelson F. Liu et al. (2023) 
Liu
2023
Lost in the Middle: How Language Models Use Long Contexts	El acceso a datos decae significativamente en la zona intermedia del contexto largo 
Liu
2023
.	arXiv:2307.03172
Philippe Laban et al. (2025) 
Laban
2025
LLMs Get Lost In Multi-Turn Conversation	Rendimiento cae un 39% en múltiples turnos por asunciones tempranas y verbosidad 
Laban
2025
.	arXiv:2505.09387
Wai-Chung Kwan et al. (2024) 
Kwan
2024
MT-Eval: A Multi-Turn Capabilities Evaluation Benchmark for LLMs	La distancia al contenido relevante y la propagación de errores deterioran el diálogo 
Kwan
2024
.	arXiv:2401.16876
Adyasha Maharana et al. (2024) 
Maharana
2024
Evaluating Very Long-Term Conversational Memory of LLM Agents	Dificultad para retener dinámicas temporales y causales en diálogos de hasta 300 turnos 
Maharana
2024
.	arXiv:2402.17753
Vardhan Dongre et al. (2026) 
Dongre
2026
When Attention Closes: How LLMs Lose the Thread in Multi-Turn Interaction	El canal de atención a tokens de instrucciones decae progresivamente con los turnos 
Dongre
2026
.	arXiv:2605.13280
Query-aware contextualization (placing the query before and after the documents) does not substantially improve robustness of language models to changing the position of relevant information in multidocument QA; performance slightly increases when relevant information occurs at the very beginning, but otherwise slightly decreases.
Expand
Figure 9Query-aware contextualization (placing the query before and after the documents) does not substantially improve robustness of language models to changing the position of relevant information in multidocument QA; performance slightly increases when relevant information occurs at the very beginning, but otherwise slightly decreases.


Show more
How to readEl gráfico muestra el rendimiento del modelo en función de la posición del documento relevante dentro del contexto. Las curvas representan la precisión según si el contenido se sitúa al inicio, en medio o al final.


Lost in the Middle: How Language Models Use Long Contexts

2023
·
Nelson F. Liu et al.
·
Transactions of the Association for Computational Linguistics
Mecanismos del Olvido Conversacional
La degradación en interacciones prolongadas surge de distintos factores arquitectónicos y dinámicos:

Efecto de posición contextual: Los modelos procesan con mayor solidez los turnos iniciales y finales, perdiendo datos situados en los turnos intermedios 
Laban
2025
Liu
2023
.
Cierre del canal de atención: Conforme avanzan los intercambios, la atención directa hacia las instrucciones globales y reglas del sistema disminuye sistemáticamente 
Dongre
2026
.
Propagación y bloqueo de errores: Las suposiciones tempranas no corregidas generan respuestas sobrecargadas que desvían el modelo de la intención del usuario 
Laban
2025
Liu
2026
Singh
2026
.
Ruptura de coherencia temporal: A lo largo de cientos de turnos, los mecanismos estándar pierden dependencias causales e incrementan las inconsistencias internas 
Maharana
2024
Li
2025
.



## Observaciones
- Consensus usó un análisis Pro por su cuenta. Hay que confirmar con JP que él lo obtenga en las mismas condiciones.
- La tabla trajo 5 referencias; clasifico solo esas. El texto cita otras (Li 2025, Liu 2026, Singh 2026) que no cuentan como las 5 principales.