# c2_C: NotebookLM, contexto cerrado con los 11 PDF

Fecha y hora: 21 oct 2026, 5:57 pm
Herramienta: NotebookLM (notebook.google.com), plan [el que tengas; en pantalla aparece "PLUS"]
Fuentes cargadas: 11 PDF de docs/fuentes/, sin añadir nada más
Configuración: sin protocolo ni instrucciones personalizadas. No usé "Buscar nuevas fuentes en la Web" ni Studio.

## Consulta
Dame 5 referencias académicas, con autores, año y DOI o enlace, sobre cómo los modelos de lenguaje pierden información en conversaciones largas.

## Respuesta completa
Aquí tienes **5 referencias académicas** extraídas de tus fuentes que analizan cómo los modelos de lenguaje pierden o procesan deficientemente la información en contextos extensos y conversaciones de múltiples turnos:

1. **Liu et al. (2023)** — *"Lost in the Middle: How Language Models Use Long Contexts"*
  * **Autores:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni y Percy Liang[1].
  * **Año:** 2023[1][2].
  * **Enlace:** [arXiv:2307.03172](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Farxiv.org%2Fabs%2F2307.03172)[2].
  * **Resumen:** Demuestra la existencia de una "curva en U" en el rendimiento de los LLM: la precisión cae significativamente cuando la información relevante se encuentra en la parte media del contexto, mostrando un sesgo marcado por la información ubicada al inicio (primacía) o al final (recencia) del texto[1][3].
2. **Zhang et al. (2024)** — *"Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding"*
  * **Autores:** Zhenyu Zhang, Runjin Chen, Shiwei Liu, Zhewei Yao, Olatunji Ruwase, Beidi Chen, Xiaoxia Wu y Zhangyang Wang[4].
  * **Año:** 2024[4][5].
  * **Enlace:** [arXiv:2403.04797](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Farxiv.org%2Fabs%2F2403.04797)[4][5].
  * **Resumen:** Examina cómo las codificaciones posicionales como RoPE sufren un efecto de decaimiento a largo plazo que lleva a los modelos a ignorar la parte central de un contexto extenso, y propone la técnica *Multi-scale Positional Encoding* (Ms-PoE) para corregir esta pérdida[4].
3. **Huang et al. (2024)** — *"A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions"*
  * **Autores:** Lei Huang, Weijiang Yu, Weitao Ma, Weihong Zhong, Zhangyin Feng, Haotian Wang, Qianglong Chen, Weihua Peng, Xiaocheng Feng, Bing Qin y Ting Liu[8].
  * **Año:** 2024[8][9].
  * **DOI / Enlace:** [10.1145/3703155](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Fdoi.org%2F10.1145%2F3703155)[8].
  * **Resumen:** Revisa las alucinaciones derivadas de la falta de fidelidad en textos largos y conversaciones extensas, explicando que la atención localizada en los mecanismos de los Transformers causa el olvido de instrucciones (*instruction forgetting*) y disminuye la capacidad de atención al contexto general[10][11].
4. **Zhang et al. (2023)** — *"Siren's Song in the AI Ocean: A Survey on Hallucination in Large Language Models"*
  * **Autores:** Yue Zhang, Leyang Cui, Wei Bi, Shuming Shi, et al.[12][13].
  * **Año:** 2023[12][13].
  * **Enlace:** [arXiv:2309.01219](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Farxiv.org%2Fabs%2F2309.01219)[13][14].
  * **Resumen:** Aborda las alucinaciones por conflicto de contexto (*context-conflicting hallucinations*), las cuales surgen en respuestas largas o diálogos multiturno cuando el modelo pierde el hilo del contexto previo o falla al mantener consistencia debido a limitaciones en su memoria a largo plazo[15][16].
5. **Yi et al. (2024)** — *"A survey on recent advances in LLM-Based multi-turn dialogue systems"*
  * **Autores:** Zihao Yi, Jiarui Ouyang, Yuwen Liu, Tianhao Liao, Zhe Xu y Ying Shen[17].
  * **Año:** 2024[17].
  * **Enlace:** [arXiv:2402.18013](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Farxiv.org%2Fabs%2F2402.18013)[17].
  * **Resumen:** Proporciona una revisión sobre sistemas de diálogo multiturno basados en LLM, abordando cómo el contexto acumulado en turnos anteriores impacta los juicios y decisiones del modelo a lo largo de conversaciones extensas[17][18].

💡 ¿Te gustaría explorar alguna de las estrategias propuestas en estas fuentes para mitigar la pérdida de información (como el decodificado consciente del contexto o las modificaciones en la codificación posicional)?


## Observaciones
- Las citas aparecen como números entre corchetes ([1], [2]...), sin indicar página.
- Cuatro de las cinco referencias corresponden a PDF del cuaderno (Liu, Zhang 2024, Huang, Zhang 2023).
- La quinta (Yi et al., arXiv:2402.18013) no es uno de los 11 PDF. Aparece en la bibliografía del PDF de Wen et al. (abstención).
- NotebookLM terminó con una pregunta sugerida, que no respondí.