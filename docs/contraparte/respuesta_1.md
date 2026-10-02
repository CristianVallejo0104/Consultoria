Modelo: Claude Opus 5.5, esfuerzo medio. Chat incógnito, sin conectores ni búsqueda web.
Fecha y hora: 2 de octubre de 2026, 5:48 pm
Archivos cargados: agente.py, correr_experimento.py, evaluar_calidad_texto.py, decisiones.md
Prueba de limpieza: no tenía información del proyecto (conocía solo el perfil de preferencias).

**0. Archivos recibidos**

Recibí completos `correr_experimento.py` y `evaluar_calidad_texto.py`. **`agente.py` y `decisiones.md` figuran como subidos, pero su contenido no está en el material** que puedo leer, y la consigna me prohíbe usar herramientas para abrirlos. Por eso, todo lo que depende del núcleo (prompts del relleno, banco de datos, verificación, medición de contexto, semilla) lo evalúo solo desde el resumen y lo marco así. Los veredictos de A1–A6 tienen confianza media.

---

**A1. Construcción del tratamiento**
- **Veredicto:** problemático.
- **Evidencia:** resumen, pasos 3–4. El código no está en el material. La columna `contexto_decreciente` en `COLUMNAS` (`correr_experimento.py`) indica que ya observaron contextos que bajan entre turnos.
- **Riesgos:**
  - **ERROR, alta.** "Inicio = turno 2" es una posición absoluta, mientras que mitad y final son relativas al nivel. Así, la posición relativa del dato "inicio" cambia con el nivel, y parte de la interacción posición × nivel queda fabricada por el propio diseño.
  - **RIESGO, alta.** Un mismo nivel de tokens no equivale a la misma cantidad de texto entre modelos, porque cada uno usa un tokenizador distinto. El factor modelo queda confundido con el volumen de texto (conocimiento general).
  - **RIESGO, alta, confianza media.** `phi3:mini` en Ollama corresponde, hasta donde sé, a la variante de 4k de contexto (conocimiento general, no verificado). A 8 000 y 12 000 tokens el modelo estaría operando fuera de su ventana de entrenamiento: un fallo ahí no sería "lost in the middle", sino exceso de capacidad.
  - **RIESGO, media.** Un contexto decreciente sugiere caché de prompt (Ollama podría reportar solo los tokens nuevos) o truncamiento silencioso. En ambos casos el "nivel" medido deja de ser fiable.
  - **RIESGO, media.** Por la granularidad de turnos (hasta 300 tokens por respuesta), a 4 000 tokens el 15 % restante después de "final" puede ser apenas uno o dos turnos. Además, el sobrepaso del nivel varía entre corridas.
- **Mejora:**
  - Definir las tres posiciones de forma relativa, por ejemplo inicio = primer turno que cruza el 10 %.
  - Medir los tokens con un tokenizador común (o contar caracteres) como covariable.
  - Registrar la distancia real en tokens entre el dato y la pregunta.
  - Verificar la ventana nativa de cada modelo.

**A2. Banco de datos y pregunta final**
- **Veredicto:** con reservas.
- **Evidencia:** resumen, paso 3. El banco y el texto de la pregunta no están en el material.
- **Fortaleza:** un dato inventado evita que el modelo responda por conocimiento previo, y eso es sólido.
- **Riesgos:**
  - **ERROR potencial, alta.** El modelo evaluado probablemente responde haciendo eco del dato ("anotado: 3851"), y el relleno, que lee esa respuesta, puede repetirlo. Si el dato reaparece después, la posición efectiva pasa a ser su última mención y no el turno de inserción, lo que contamina el factor posición.
  - **RIESGO, baja.** Con 5 datos y 6 temas asignados al azar, algunas combinaciones pueden quedar desbalanceadas entre celdas.
- **Mejora:** contar las apariciones de la cifra después de la inserción en cada TXT, y excluir o modelar las corridas con repetición. También conviene instruir al relleno para que no mencione cifras.

**A3. Generador de relleno**
- **Veredicto:** problemático.
- **Evidencia:** resumen, paso 2. El prompt no está en el material.
- **Riesgos:**
  - **ERROR, alta.** El relleno depende de lo que escribe el modelo evaluado, así que cada modelo recibe una conversación distinta. El tratamiento no es idéntico entre modelos y el efecto "modelo" incluye la calidad de la conversación que el propio modelo induce. Esto es endogeneidad.
  - **RIESGO, media.** Como el relleno solo ve el último mensaje, la conversación puede derivar o volverse repetitiva, y esa degeneración puede variar por modelo.
- **Mejora:** precalcular guiones fijos de mensajes de usuario por tema, compartidos por todos los modelos, o al menos fijar la semilla del relleno. Así el único factor que cambia es el modelo.

**A4. Verificación por cadena exacta**
- **Veredicto:** con reservas.
- **Evidencia:** resumen, paso 5. El código no está en el material.
- **Riesgos:**
  - **RIESGO, media.** Hay falsos negativos posibles: "3.851" o "3 851" (separador de miles en español), o la cifra escrita en palabras.
  - Hay falsos negativos por cortesía: "no estoy seguro, pero creo que es 3851" contiene una frase de negación aunque el dato es correcto.
  - Hay falsos positivos si el modelo enumera varias cifras candidatas.
- **Mejora:**
  - Normalizar separadores y usar el patrón `\b3851\b`.
  - Codificar tres categorías (correcto seguro, correcto con duda, fallo).
  - Auditar manualmente una muestra con dos codificadores y reportar kappa.

**A5. Corridas inválidas y criterios de parada**
- **Veredicto:** problemático.
- **Evidencia:** en `correr_experimento.py`, `ya_hechas()` toma toda fila del CSV como hecha, sin importar `estado_final`. Por lo tanto, **una corrida inválida nunca se repite** y ocupa su réplica.
- **Riesgos:**
  - **ERROR, alta.** Las inválidas no son faltantes al azar. Un modelo escueto puede no alcanzar 12 000 tokens en 60 turnos: se necesita un promedio de unos 200 tokens por turno, y el tope de 300 por respuesta lo vuelve plausible. Ese modelo pierde sistemáticamente las celdas largas, justo donde se esperan más fallos, y eso sesga su tasa de acierto hacia arriba.
  - Los rechazos de seguridad pueden correlacionar con el tema.
- **Mejora:**
  - Reintentar las inválidas con una semilla nueva hasta k veces.
  - Reportar la tasa de invalidez por celda como resultado en sí.
  - Para "nivel no alcanzado", subir el máximo de turnos o reportarlo como desenlace aparte.

**A6. Parámetros de generación**
- **Veredicto:** con reservas.
- **Evidencia:** en `correr_experimento.py`, `ejecutar_evaluacion(modelo, pos, nivel)` **no recibe ni la réplica ni una semilla**.
- **Riesgos:**
  - **RIESGO, alta.** Si la semilla es global, el dato y el tema dependen del orden de ejecución. Al retomar una corrida cortada, la secuencia aleatoria cambia y se pierde la reproducibilidad.
  - Si la semilla se fija por llamada, las 5 réplicas reciben el mismo dato y tema. No puedo saber cuál de los dos casos aplica (no está en el material).
  - Fortalezas: usar la misma ventana (16 384) en todos los niveles evita confundir nivel con configuración, y una temperatura de 0.7 con réplicas es razonable.
- **Mejora:** derivar la semilla de (modelo, posición, nivel, réplica), pasarla también a Ollama (`options.seed`) y guardarla en el CSV.

**A7. Diseño y análisis**
- **Veredicto:** con reservas.
- **Evidencia:** `CONFIGS` solo define `preliminares_tokens`; **la configuración de las 270 corridas no está en el material**. Los bucles recorren modelo → posición → nivel → réplica en orden fijo.
- **Riesgos:**
  - **RIESGO, media.** El orden de ejecución no está aleatorizado. La deriva temporal (temperatura de la GPU, actualizaciones de Ollama) queda confundida con el modelo.
  - **ERROR para el análisis, alta.** Con 5 observaciones binarias por celda, una logística con la interacción triple casi seguro tendrá separación completa (celdas con 0 % o 100 % de acierto) y estimaciones infinitas (conocimiento general).
  - Usar chi-cuadrado con conteos esperados menores a 5 no es válido.
  - Los modelos de nube difieren en tamaño y arquitectura, así que "empresa" queda confundida con escala.
  - Tres niveles son pocos para estimar "en qué punto" se pierde el dato.
- **Mejora:**
  - Aleatorizar el orden de las corridas.
  - Balancear dato y tema entre celdas (cuadrado latino) en lugar de asignarlos al azar.
  - Usar regresión de Firth o bayesiana, con efectos principales más la interacción posición × nivel.
  - Usar la prueba exacta de Fisher en vez de chi-cuadrado.
  - Hacer un análisis de potencia con el piloto.
  - Analizar local y nube por separado.

**A8. Evaluador de calidad**
- **Veredicto:** problemático, aunque es exploratorio.
- **Evidencia (`evaluar_calidad_texto.py`):**
  - `extraer_turnos_usuario` quita las respuestas del modelo evaluado, pero el prompt pide juzgar si es "continuación lógica del contexto previo". **Sin ese contexto, la coherencia no se puede evaluar (ERROR).**
  - Por el regex `Usuario: (.+?)`, probablemente se incluyen también el mensaje de apertura fijo, el dato y la pregunta final, que no son del relleno. Confianza media, porque depende del formato del TXT.
  - `num_ctx: 8192`: las conversaciones de 12 000 tokens pueden superarlo. Ollama trunca el inicio, que es donde están las instrucciones (confianza media).
  - `num_predict: 600` puede cortar la respuesta antes de que aparezcan las notas, y entonces quedan en `None`.
  - Un juez de 1.5B no está validado contra personas, y G-Eval original usa un modelo grande con notas ponderadas por probabilidad (conocimiento general).
  - `MUESTRA=5` toma los primeros archivos que devuelve `glob`, lo que no es una muestra aleatoria y probablemente pertenece a un solo modelo.
  - `"modelo_juez"` está escrito a mano en el registro en vez de leerse del parámetro.
- **Severidad:** media, y alta si se usa para afirmar que el relleno es natural.
- **Mejora:**
  - Incluir los turnos del modelo evaluado como contexto.
  - Filtrar solo los turnos del relleno.
  - Evaluar por ventanas.
  - Usar `random.sample` con semilla.
  - Validar con unas 30 calificaciones humanas.

---

**(a) Las 3 debilidades más graves**
1. Relleno endógeno y posible repetición del dato (A2–A3): contaminan tanto el factor modelo como el factor posición.
2. Corridas inválidas no aleatorias y no reintentadas (A5): sesgan la tasa de acierto en las celdas largas.
3. Nivel no comparable entre modelos, más la ventana nativa de phi3 y la posición "inicio" absoluta (A1).

**(b) Antes de las 270 corridas**
- Guiones de relleno fijos, o un control de menciones del dato.
- Posiciones relativas.
- Semilla derivada de la celda y guardada.
- Reintento de las inválidas.
- Orden aleatorio de ejecución.
- Datos y temas balanceados.
- Verificar la ventana de cada modelo y la medición de tokens (resolver `contexto_decreciente`).
- Plan de análisis con Firth.
- Auditoría manual de la verificación.

**(c) Diferencias entre el código y el resumen**
- No existe la configuración final, solo la preliminar.
- Las inválidas sí cuentan como réplica hecha y bloquean su repetición.
- No se ve ninguna semilla en la ejecución.
- El juez probablemente evalúa turnos que no son del relleno, y sin contexto.
- El resto no se puede contrastar porque `agente.py` no está en el material.

**(d) Información que necesitaría**
- El contenido de `agente.py` (prompts, medición de tokens, semilla, verificación, `num_ctx` por llamada) y de `decisiones.md`.
- Un TXT de ejemplo.
- La versión de Ollama y las etiquetas exactas de los modelos.
- Las tasas de invalidez y de `contexto_decreciente` del piloto, aunque sea sin los aciertos.