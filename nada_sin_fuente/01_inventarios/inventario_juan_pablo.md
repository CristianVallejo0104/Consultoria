# Inventario de fallos — Juan Pablo Tibamoso

## Fallo 1

- **Herramienta:** ChatGPT, plan gratis, chat temporal (21 de octubre de 2026, `02_experimento/respuestas/c1_A.md`).
- **Qué generó:** Le pedí referencias sin buscar en la web y salieron miniaturas.
- **Qué estaba mal:** Me pareció que no estaba bien, ya que claramente le di instrucciones de no buscar en la web y la respuesta de él dio a entender que aun así lo hizo.
- **Cómo lo detecté:** La respuesta de él fue darme miniaturas de respuestas de imágenes que claramente fueron sacadas de la web.
- **Qué me costó:** Afectó en tema de que la idea era que se hiciera la investigación con conocimiento propio de la IA, y aunque dijo que no había buscado en la web, su respuesta hizo parecer que sí.
- **Qué lo habría evitado:** No creo que se pudiera hacer nada distinto, ya que le di indicaciones precisas y aun así no tuvo en cuenta al 100 % las indicaciones.

## Fallo 2

- **Herramienta:** Claude, que nos recomendó el modelo y nos dio el código; el modelo era `smollm2:1.7b` (local, por Ollama), como orquestador del agente de CrewAI (descartado en `docs/decisiones.md`, D-10).
- **Qué generó:** El modelo se quedaba repitiendo la herramienta y no respondía.
- **Qué estaba mal:** Entró en bucle, y era porque al parecer no era competente con CrewAI o el orquestador. Claude nos dijo que lo podíamos usar y al final dio error y tocó quitarlo; después nos explicó el error, pero no lo tuvo en cuenta antes de darlo.
- **Cómo lo detecté:** Por tiempo de ejecución nos dimos cuenta de que entró en bucle.
- **Qué me costó:** Nos costó tiempo, ya que se realizó la instalación y la corrida del agente, pero al final tocó quitar todo eso.
- **Qué lo habría evitado:** Indagar un poco de la compatibilidad de modelos y no creer todo lo que dice la IA, ya que ella nos dio el código para correr todo y al final ella misma no nos dijo cuál había sido el error.

## Fallo 3

- **Herramienta:** Claude, que nos recomendó el modelo; el modelo era `phi3:mini` (local, por Ollama), reemplazado por `phi4-mini` (`docs/decisiones.md`, D-13).
- **Qué generó:** Claude recomendó ese modelo y dijo que iba a funcionar común y corriente. Al ver que ocupaba menos RAM de la que tengo, decidimos tomarlo, y después nos dimos cuenta de que no era así.
- **Qué estaba mal:** En mi PC no funcionaba porque al parecer ese modelo guardaba cosas en el caché que no dejaba reproducirlo, y es algo que omitió; por eso me causaba conflictos al usarlo.
- **Cómo lo detecté:** Por lo que mostraba `ollama ps`. Después, analizando en la terminal, me di cuenta de que usaba más RAM de la que decía que usaba, por lo del caché.
- **Qué me costó:** Nos costó tiempo, ya que nos tocó cambiar el modelo y cambiar muchas cosas.
- **Qué lo habría evitado:** Indagar primero de cada modelo antes de elegirlo.

---

Firma: Juan Pablo Tibamoso — Fecha: 5/11/2026
