# Guía de calibración

El objetivo del agente es pensar **como la manager de contenido de Teilur**, no como un revisor genérico. Antes de confiar en sus veredictos (y mucho antes de auditar los 314 artículos publicados), hay que calibrarlo contra revisiones reales de ella.

## Qué se necesita

Pedirle a la manager **2-3 artículos que ya haya revisado manualmente**, idealmente:

- 1 artículo que aprobó casi sin cambios (un "bueno").
- 1 artículo al que le marcó muchas correcciones (un "malo" o "regular").
- Sus comentarios/correcciones de cada uno (el doc con sugerencias, o una lista de lo que pidió cambiar).

## Proceso

1. **Pasar cada artículo por el agente** (la versión ANTES de las correcciones de ella):

   ```bash
   blog-auditor review articulo-1-antes.docx
   ```

2. **Comparar** el reporte del agente con lo que ella marcó:

   | Pregunta | Qué indica |
   |---|---|
   | ¿El agente detectó los mismos problemas que ella? | Cobertura del criterio |
   | ¿El agente marcó cosas que a ella no le importan? | Falsos positivos / ruido |
   | ¿El puntaje relativo coincide? (el "bueno" puntúa más que el "malo") | Calibración de escala |
   | ¿Las acciones sugeridas son las que ella habría pedido? | Utilidad para la redactora |

3. **Ajustar la rúbrica** según las diferencias, editando [src/blog_auditor/prompts/system_prompt.md](../src/blog_auditor/prompts/system_prompt.md):
   - Si al agente se le escapó algo que ella siempre marca → agregarlo como regla explícita en la dimensión correspondiente.
   - Si el agente es muy blando o muy duro → ajustar la "Guía de puntajes".
   - Si marca ruido → agregarlo a las reglas del reporte ("no inventes problemas").

4. **Repetir** hasta que los veredictos coincidan en lo esencial.

## Criterio de éxito

- El agente detecta **todos los problemas críticos** que la manager detectó (cero falsos negativos en lo importante).
- El orden de calidad entre artículos coincide con el de ella.
- Ella lee un reporte y dice "sí, esto es lo que yo habría dicho".

Cuando se cumpla → el agente está calibrado: se puede integrar a Slack (Fase 2) y correr el barrido de Webflow (Fase 3).

## Registro de calibración

Documentar aquí cada ronda (fecha, artículos usados, diferencias encontradas, ajuste hecho al prompt) para no perder el historial del criterio:

| Fecha | Artículo | Diferencia detectada | Ajuste al prompt |
|---|---|---|---|
| 2026-06-10 | Blog 2 (publicado, aprobado por la manager) y Blog 18 (sin revisar), ambos PDF | El agente marcó "faltan enlaces internos" como crítico en ambos, pero los PDF no muestran hipervínculos (solo el texto ancla), así que no se puede saber si el doc original los tenía. | Se agregó a la sección SEO la limitación de formato: si no hay URLs visibles pero sí anclas/menciones, pedir "verificar al cargar en Webflow" en vez de problema crítico. |
| 2026-06-10 | Blog 2 (publicado, aprobado) | Puntaje global 5.2/10 para un artículo que la manager aprobó. Hallazgos principales: cifras sin fuente ("2–4 week hiring delay", "30%–60% cost savings"), párrafos genéricos, transparent pricing solo al cierre. PENDIENTE: confirmar con la manager cuáles de estos hallazgos considera reales y cuáles son ruido, y ajustar la escala. | _(esperando feedback de la manager)_ |
