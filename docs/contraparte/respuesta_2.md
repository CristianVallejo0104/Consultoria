Modelo: Claude Opus 5.5, esfuerzo medio. Chat incógnito, sin conectores ni búsqueda web.
Fecha y hora: 2 de octubre de 2026, 5:56 pm
Archivos cargados: agente.py, correr_experimento.py, evaluar_calidad_texto.py, decisiones.md
Prueba de limpieza: no tenía información del proyecto (conocía solo el perfil de preferencias).


**0. Archivos.** Ahora leí completos `agente.py` (638 líneas) y `decisiones.md` (D-01 a D-11). Abajo marco solo lo que cambia respecto a mi revisión anterior.

---

**A1. Tratamiento.** Confianza: **sube**. Veredicto: se mantiene problemático, pero cambian dos riesgos y aparece uno nuevo.

- **Baja el riesgo de phi3 fuera de su ventana** (de alta a baja). D-10 declara, con `ollama show`, una "ventana declarada ≥ 12,000" para los tres modelos. Queda una reserva: no se anota la cifra exacta de phi3, como sí se hace con gemma3 (131,072) en D-01. Mejora: anotarla.
- **Baja el riesgo de caché o truncamiento** (de media a baja). D-06 registra que en el piloto "el contexto nunca decreció". El sobrepaso del nivel (0.5–10.3 %) está documentado y se usará `contexto_final` como covariable, lo cual está bien.
- **Se confirma** que "inicio" es absoluto: `TURNO_DATO_INICIO = 2` (l. 35) y `_toca_insertar_dato` (l. 328–332).
- **Nuevo, RIESGO alta.** La parada (l. 399) exige que el dato ya esté insertado, y la inserción ocurre en el turno *siguiente* al cruce del umbral.
  - Para "final", si un turno salta de menos del 85 % a más del 100 %, el dato entra **por encima del nivel**, justo antes de la pregunta.
  - A 4 000 tokens, el 15 % restante (unos 600 tokens) cabe en un solo intercambio. En la práctica, "final" puede equivaler a "último turno".
  - **Mejora:** analizar la posición relativa *lograda*, `contexto_al_dato / contexto_final`, que ya se guarda, y descartar o reasignar las corridas que excedan un margen.

**A2. Datos y pregunta.** Confianza: **sube**.

- **Se confirma** la vía de repetición. El prompt del relleno invita a "hacer una pregunta sobre un detalle especifico que mencionaron" (l. 113–115), y no hay ningún control de menciones posteriores del dato. Severidad: alta.
- **Nuevo, RIESGO media.** Los datos tienen dificultad heterogénea: números de 4 dígitos, uno de 5 (`44295`) y una versión (`9.15.6`). Como el dato se asigna al azar sin balance, la dificultad puede quedar confundida con los factores. Mejora: incluir el dato como covariable o bloque.
- **Nuevo, MEJORA.** Todos los mensajes con el dato cambian de tema hacia "inteligencia artificial" (l. 103–107). Eso es bueno para la homogeneidad del tratamiento, pero lo que sigue al dato siempre es una conversación sobre IA. Conviene declararlo.

**A3. Relleno.** Confianza: **sube**. Se confirma el ERROR de endogeneidad.

- **Nuevo.** El generador no recibe historial: solo ve los últimos 500 caracteres del mensaje del asistente (l. 284) y llama a `/api/generate` sin semilla ni `num_ctx` (l. 289–290). La deriva temática depende por completo de lo que escribe cada modelo.
- **Nuevo, RIESGO baja.** El generador y el orquestador son el mismo `qwen2.5:1.5b`, que además es el juez de calidad (D-10, "Límites"). Esto no afecta la retención, pero sí la evaluación del relleno.

**A4. Verificación.** Confianza: **sube**. Veredicto: sigue con reservas.

- **Nuevo, RIESGO media.** La comparación de `verificar_acierto` (l. 429–444) es por subcadena, sin límites de palabra. Además, la lista de negaciones lleva tildes ("información", "no sé si"): una respuesta escrita sin tildes, como "no se si", no se detecta.
- La lista tampoco cubre "no lo recuerdo".
- `44295` falla si el modelo escribe "44.295".
- **Mitiga:** D-11 reconoce que "me parece que era 3851" se acepta, y D-03 planea etiquetado manual doble con kappa. Esto convierte mi mejora anterior en un plan ya previsto.

**A5. Inválidas.** Confianza: **sube**. Severidad alta, ahora con evidencia directa.

- D-06 registra que phi3 a 12K necesitó 57 de los 60 turnos. Por eso, `no_alcanzo_nivel` es muy probable justamente en la celda phi3 × 12K.
- **Nuevo, ERROR media.** Los rechazos de seguridad solo se detectan en OpenRouter (`_procesar_openai_compat`, l. 205). En Ollama, un rechazo cuenta como **fallo** y no como inválida (D-11, "Límites").
- **Nuevo, RIESGO media.** Según D-10, phi3 con `num_ctx` 16 384 ocupa 9.0 GB, más que los 6 GB de la GPU. El modelo corre parcialmente en CPU, así que los timeouts de 600 s se concentrarán en phi3 a niveles altos: otra fuente de faltantes no aleatorios.
- `done_reason` no se guarda (D-06, "Pendiente"), por lo que no se distinguen las respuestas truncadas por el tope de 300 tokens.

**A6. Parámetros.** Confianza: **sube**. Veredicto: problemático (antes: con reservas).

- **Se confirma el ERROR.** `random.seed(42)` se fija una sola vez al importar el módulo (l. 28). Por eso:
  - el dato y el tema dependen del orden de las corridas y de cuántas se hicieron en el mismo proceso;
  - al retomar una ejecución cortada, la asignación cambia;
  - no hay semilla para los modelos evaluados ni para el relleno.
- **Nuevo, RIESGO media.** La cuantización difiere entre modelos (phi3 en Q4_0, gemma3 en Q4_K_M; D-10), así que queda confundida con el factor modelo.
- **Nuevo, RIESGO para el Diseño B.** En OpenRouter no se controla la ventana de contexto, y los tokens de razonamiento pueden consumir el tope de 300 (comentario de la l. 242–243).

**A7. Diseño.** Confianza: **sube levemente**.

- **Se confirma** que no existe la configuración de las 270 corridas (`CONFIGS`) y que `MODELOS_CLOUD = {}` (l. 60). Con 3 modelos locales, el diseño completo da 135 corridas; las 270 dependen del Diseño B, que aún no está definido.
- **Nuevo, RIESGO baja.** `contexto_final` como covariable (D-06) es una variable posterior al tratamiento que depende del modelo. Si se usa, conviene interpretarla como ajuste y no como efecto causal.

---

**(c) Diferencias entre el código y el resumen (actualizado)**

1. Los rechazos de seguridad solo se tipifican como inválidos en la nube; en local cuentan como fallo (l. 205; D-11).
2. La semilla es global al importar y no por corrida; tampoco se pasa a los modelos (l. 28). El comentario cita D-07 como fuente del pendiente, pero D-07 trata de los proveedores: hay una inconsistencia documental.
3. El relleno no lee "el último mensaje", sino sus primeros 500 caracteres, sin historial ni semilla (l. 284–290).
4. `contexto_final` guarda solo `tokens_prompt` de la pregunta final (l. 424), mientras que la parada usa prompt + respuesta del turno anterior (l. 390). Son definiciones parecidas, pero no idénticas a la de D-06.
5. La réplica del archivo se calcula según los archivos que ya existen (`generar_nombre_archivo`, l. 514–521), no según el CSV. Si una corrida se interrumpe entre `guardar_resultado` y la escritura del CSV, las réplicas del TXT y del CSV quedan desalineadas.
6. Se confirma que las corridas inválidas ocupan su réplica y no se repiten (`ya_hechas`).
7. Se confirma en el juez que `extraer_turnos_usuario` incluye el mensaje de apertura y el mensaje con el dato, que no vienen del relleno. La pregunta final queda fuera, porque su etiqueta es `[PREGUNTA FINAL]`.

