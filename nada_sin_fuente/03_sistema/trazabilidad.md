# Tabla de trazabilidad del anteproyecto

Fuente de las afirmaciones: `docs/informes/Primera_Entrega_Consultoria.pdf`, sección 2 (estado del arte).
Una fila por cada afirmación sustantiva: toda frase que diga algo que no es opinión nuestra
(un resultado, una cifra, una definición, lo que hace o propone un autor).

**Clave del gestor** = la clave de cita de Zotero (la misma que aparece en `biblioteca.bib`).
**Ubicación** = página del PDF guardado en `docs/fuentes/` y, si se puede, una cita textual corta (menos de 15 palabras).

| # | Afirmación (cita textual del anteproyecto, con su §) | Fuente (clave del gestor) | Ubicación (página y cita corta) | Verificado por | Fecha |
|---|---|---|---|---|---|
| 1 | §2.1: «la ventana de contexto nominal de un modelo no refleja su capacidad real de retención uniforme» | `liu2023_lost_in_the_middle.pdf` [clave Zotero pendiente] | p. 2 — «extended-context models are not necessarily better at using their input context»; p. 5 — «Extended-context models are not necessarily better at using input context». Ojo: la fuente dice «no necesariamente mejor», más débil que nuestra frase | PENDIENTE: abrir PDF | |
| 2 | §2.1: «un patrón consistente de rendimiento en forma de U [...] retienen mejor la información ubicada al inicio y al final del contexto, pero tienden a perder la que se encuentra en la mitad» | `liu2023_lost_in_the_middle.pdf` [clave Zotero pendiente] | p. 1 (Figura 1) — «results in a U-shaped performance curve»; p. 5 — «highest when relevant information occurs at the beginning or end» | PENDIENTE: abrir PDF | |
| 3 | §2.1: «Este hallazgo, realizado con modelos como GPT-3.5 y Claude» | `liu2023_lost_in_the_middle.pdf` [clave Zotero pendiente] | p. 2 — «closed (OpenAI's GPT-3.5-Turbo and Anthropic's Claude-1.3)» | PENDIENTE: abrir PDF | |
| 4 | §2.1: «Liu et al. (2023a) evaluaron este fenómeno con documentos estáticos de una sola entrada, no con conversaciones interactivas de múltiples turnos» | `liu2023_lost_in_the_middle.pdf` [clave Zotero pendiente] | p. 1 — «multi-document question answering and key-value retrieval» (las dos tareas). Ojo: en la p. 10 citan «Sankar et al. (2019) found similar results in dialogue models» | PENDIENTE: abrir PDF | |
| 5 | §2.2: «G-Eval (Liu et al., 2023b) propone utilizar GPT-4 como juez para calificar textos generados por otros modelos» | `liu2023_GEVAL.pdf` [clave Zotero pendiente] | p. 1 — «with GPT-4 as the backbone model»; p. 3 — «GPT-3.5 (text-davinci-003) and GPT-4» (también usan GPT-3.5) | PENDIENTE: abrir PDF | |
| 6 | §2.2: «en dimensiones como coherencia, fluidez y relevancia» | `liu2023_GEVAL.pdf` [clave Zotero pendiente] | p. 4 — «fluency, coherence, consistency and relevance» (dimensiones de SummEval) | PENDIENTE: abrir PDF | |
| 7 | §2.2: «asignando puntuaciones del 1 al 5» | `liu2023_GEVAL.pdf` [clave Zotero pendiente] | p. 3 — «output a score from 1 to 5». Ojo: en las p. 10–11 la de engagingness va de 1 a 3 | PENDIENTE: abrir PDF | |
| 8 | §2.2: «es subjetivo (la misma evaluación puede producir calificaciones diferentes en ejecuciones distintas)» | `liu2023_GEVAL.pdf` [clave Zotero pendiente] | no encontrada. Lo más cercano está en la p. 3: «n = 20, temperature = 1, top p = 1» (muestrean 20 veces con GPT-4); el artículo no lo llama subjetivo | PENDIENTE: abrir PDF | |
| 9 | §2.2: «depende de una API de pago» | `liu2023_GEVAL.pdf` [clave Zotero pendiente] | no encontrada como afirmación. En la p. 3 — «We use OpenAI's GPT family as our LLMs»; «de pago» es inferencia nuestra | PENDIENTE: abrir PDF | |
| 10 | §2.2: «RAGAS (Es et al., 2023) evalúa sistemas de Generación Aumentada por Recuperación (RAG), donde un modelo consulta documentos externos antes de responder» | `RAGAS.pdf` [clave Zotero pendiente] | p. 1 — «reference-free evaluation of Retrieval Augmented Generation (RAG) pipelines»; p. 2 — «the system first retrieves some context c(q)» | PENDIENTE: abrir PDF | |
| 11 | §2.2: «RAGAS mide la fidelidad de la respuesta respecto al documento recuperado y la relevancia del documento seleccionado» | `RAGAS.pdf` [clave Zotero pendiente] | p. 3 — «Faithfulness refers to the idea that the answer should be grounded»; p. 4 — context relevance. Ojo: falta la tercera métrica, Answer Relevance (p. 3) | PENDIENTE: abrir PDF | |
| 12 | §2.2: «opera sobre interacciones individuales (una pregunta, un documento, una respuesta)» | `RAGAS.pdf` [clave Zotero pendiente] | p. 2 — «given a question q, the system first retrieves some context c(q)». Que no evalúe varios turnos es inferencia nuestra: el PDF no menciona conversaciones | PENDIENTE: abrir PDF | |
| 13 | §2.3: «ninguno mide la retención de información a lo largo de una conversación con múltiples turnos» | `liu2023_GEVAL.pdf`, `RAGAS.pdf` [claves Zotero pendientes] | no encontrada (es una afirmación negativa). Ojo: G-Eval sí evalúa diálogo; en la p. 1 — «text summarization and dialogue generation»; en la p. 4 — Topical-Chat | PENDIENTE: abrir PDF | |
| 14 | §2.3: «ambos dependen de APIs de pago y modelos propietarios» | `RAGAS.pdf`, `liu2023_GEVAL.pdf` [claves Zotero pendientes] | RAGAS p. 3 — «gpt-3.5-turbo-16k model, which is available through the OpenAI API»; G-Eval p. 3 — «OpenAI's GPT family». «De pago» no aparece en ninguno | PENDIENTE: abrir PDF | |
| 15 | §2.4: «Yao et al. (2023) propusieron el formato ReAct [...] donde el modelo alterna entre pasos de razonamiento (Thought), ejecución de acciones (Action) y observación de resultados (Observation)» | `yao2022_react.pdf` [clave Zotero pendiente] | p. 1 — «reasoning traces and task-specific actions in an interleaved manner»; p. 2 (Figura 1); p. 6 — «interleaving reasoning, action and observation steps». Ojo: la figura usa las etiquetas «Act» y «Obs» | PENDIENTE: abrir PDF | |
| 16 | §2.4: «Este formato es el utilizado por CrewAI, el framework con el que se construyó nuestro agente» | — | no encontrada en `docs/fuentes/` (la documentación de CrewAI no está en el corpus) | PENDIENTE: abrir PDF | |
| 17 | §2.4: «permite que el modelo decida cuándo y cómo utilizar herramientas externas» | `yao2022_react.pdf` [clave Zotero pendiente] | parcial: en la p. 1 — «gather additional information from external sources such as knowledge bases». No encontré «decide cuándo» | PENDIENTE: abrir PDF | |

> La fila 1 es el ejemplo que dio el profesor en su informe (sección 6). Antes de dejarla, ábranla
> ustedes en el PDF y confirmen las páginas.

## Afirmaciones corregidas

Las que no tenían de dónde salir, o decían algo distinto a la fuente. Van también al apartado 5 de la memoria.

| Afirmación original | Problema | Corrección |
|---|---|---|
| Liu et al. citado como «(2023)» con el volumen 12 de *TACL* | Ese volumen es de 2024 (vol. 12, pp. 157–173, doi:10.1162/tacl_a_00638); 2023 es el preprint de arXiv | El PDF que usamos es la versión de TACL: se cita como Liu et al. (2024), Transactions of the Association for Computational Linguistics, 12, 157–173. G-Eval queda como Liu et al. (2023) y se eliminan las letras a y b. |
| «100 % localmente con Ollama, sin APIs de pago» y reproducible «en cualquier computador con 8 GB de RAM» | D-02 decidió pagar OpenRouter; D-10 registra 9,0 GB de phi3:mini con `num_ctx` 16.384 | [nueva redacción] |
| Objetivo específico 2: phi3:mini, llama3.2:3b y gemma2:2b con 5, 10 y 20 turnos | Hoy: phi4-mini, llama3.2:3b y gemma3:4b con niveles de 4.000, 8.000 y 12.000 tokens (D-01, D-06, D-13) | [nueva redacción] |
