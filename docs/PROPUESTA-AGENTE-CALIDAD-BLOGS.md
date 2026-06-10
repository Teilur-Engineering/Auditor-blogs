# Propuesta: Agente de IA para revisar calidad de blogs — Teilur Talent
Fecha: 2026-06-09
Estado: IDEA DOCUMENTADA para construir en otra sesión. Nada construido todavía.
Propósito de este doc: dar TODO el contexto necesario para que otro chat de Claude construya
este agente sin tener que re-investigar nada.

═══════════════════════════════════════════════════════════════
## 1. EL OBJETIVO REAL (importante — define todo el diseño)
═══════════════════════════════════════════════════════════════
La manager de Teilur HOY revisa MANUALMENTE los blogs antes de publicarlos.
- La redactora (content writer) escribe el artículo en un documento de Google Docs o Word.
- La manager lo revisa ANTES de publicar y verifica sobre todo:
  1. Que TENGA SENTIDO (coherente, bien argumentado, no contradictorio).
  2. Que NO SEA MUY GENÉRICO (que aporte algo, no relleno vacío tipo "AI slop").
  3. POSICIONAMIENTO (que refleje la marca y el diferenciador de Teilur).
  4. SEO (que esté optimizado para buscadores).

→ EL AGENTE DEBE REPLICAR Y ESCALAR ESE CRITERIO HUMANO.
  NO es un auditor del sitio en vivo. Es un REVISOR DE BORRADORES, igual que la manager,
  que trabaja sobre el documento (Google Doc / Word / texto pegado) ANTES de publicar.

Beneficio: la manager ahorra tiempo, la calidad es consistente, y la redactora recibe
feedback estructurado y rápido (incluso antes de que la manager lo vea).

═══════════════════════════════════════════════════════════════
## 2. QUÉ DEBE REVISAR EL AGENTE (los criterios, en detalle)
═══════════════════════════════════════════════════════════════
Basado en lo que la manager revisa + lo aprendido en la auditoría de Teilur:

### A. ¿Tiene sentido? (coherencia y calidad de argumentación)
- ¿El artículo cumple lo que promete el título?
- ¿La estructura es lógica (intro → desarrollo → conclusión)?
- ¿Hay afirmaciones sin respaldo, contradicciones o saltos de lógica?
- ¿Los datos/cifras tienen fuente o al menos se marcan como estimación?
  (NOTA: los buenos artículos de Teilur ya hacen esto — ej. el de "toptal-cost" cita
   Glassdoor, Reddit, HackerNoon. Es el estándar a mantener.)

### B. ¿Es genérico? (anti-"AI slop", el criterio más importante para la manager)
- ¿Aporta algo único o es relleno que cualquiera podría escribir?
- Señales de genérico: párrafos vagos, listas obvias, frases hechas, cero ejemplos
  concretos, cero datos propios, conclusión que no concluye nada.
- ¿Usa ejemplos reales, casos, números específicos? (eso = NO genérico)
- Prueba clave: "¿este párrafo se podría copiar tal cual en la web de un competidor?
  Si sí → es genérico."

### C. Posicionamiento (la marca de Teilur)
- ¿Refleja el diferenciador central: TRANSPARENT PRICING / "the first transparent pricing
  model in global hiring"? (este es EL mensaje de marca; ver contexto abajo)
- ¿El tono es coherente con Teilur (profesional, directo, mission-driven, honesto)?
- ¿Conecta el tema con la propuesta de valor de Teilur sin sonar a publicidad forzada?
- ¿Menciona/enlaza a las páginas clave cuando es relevante (pricing, how-it-works)?

### D. SEO (optimización para buscadores)
- TÍTULO: ¿tiene la keyword principal? ¿es atractivo (genera ganas de hacer clic)?
- META DESCRIPTION: ¿existe? ¿140-160 caracteres? ¿con gancho + keyword?
- ESTRUCTURA: ¿un solo H1? ¿H2/H3 en orden lógico con keywords?
- KEYWORD: ¿la keyword objetivo aparece en título, primer párrafo, algún H2, natural
  (sin "keyword stuffing")?
- ENLACES INTERNOS: ¿enlaza a otras páginas relevantes de Teilur? (clave: la auditoría
  encontró que muchos artículos están "huérfanos" sin enlaces internos → el agente debe
  exigir 2-3 enlaces internos por artículo).
- LONGITUD: ¿suficiente para el tema (no thin content)?
- CTA: ¿termina con una llamada a la acción que lleve al funnel? (la auditoría + el bot de
  marketing confirmaron que las páginas SIN CTA convierten 0 → criterio CRÍTICO).
- FECHAS: ¿menciona años desactualizados? (ej. "2025" cuando estamos en 2026 → marcar).

### E. Extras útiles (bonus que la manager agradecería)
- Detectar enlaces que podrían estar rotos (a páginas que ya no existen).
- Sugerir el "search intent": ¿a quién le sirve este artículo y qué busca esa persona?
- Dar un PUNTAJE por dimensión (Sentido / Genérico / Posicionamiento / SEO) + uno global.
- Listar 3-5 acciones concretas priorizadas para mejorar ESE artículo.

═══════════════════════════════════════════════════════════════
## 3. CONTEXTO DE TEILUR (para que el agente "entienda" la marca)
═══════════════════════════════════════════════════════════════
El agente DEBE conocer esto para evaluar bien posicionamiento y relevancia:

- QUÉ ES TEILUR: empresa de hiring/staffing que conecta empresas (sobre todo de US) con
  talento tech remoto pre-vetteado de Latinoamérica (Colombia, Argentina, México, Brasil,
  Costa Rica, Perú, Chile). +10,000 profesionales en la red.
- DIFERENCIADOR CENTRAL (el corazón de la marca): TRANSPARENT PRICING.
  Cobran un fee plano del 20% del salario, mostrado abiertamente. El 80% va al talento.
  Tagline aprobado: "The first transparent pricing model in global hiring."
  Contraste con competidores: Toptal/agencias cobran hasta 50% oculto.
- AUDIENCIA: empresas US (startups a Fortune 500) que buscan contratar tech talent y que
  están MUY sensibles al precio (buscan en Google "toptal pricing", "bairesdev pricing"...).
- COMPETIDORES que aparecen en su contenido: Toptal, BairesDev, Turing, Upwork, Andela,
  Fiverr, Revelo, Near, Lemon.io, Globant, Arc.dev.
- LÍNEA EDITORIAL QUE FUNCIONA (validado con datos): los artículos que más tráfico traen son
  los de "precios de competidores" y "X vs Y" (toptal cost, upwork pricing, etc.). El ángulo
  ganador es: "cuánto cobra REALMENTE el competidor + cómo Teilur es transparente".
- ESTRUCTURA TÍPICA de sus artículos buenos: intro → entender el modelo del competidor →
  qué se sabe de sus costos (con fuentes) → comparación con Teilur transparente → conclusión
  → FAQs → CTA. (Este patrón se puede usar como plantilla de referencia.)
- El blog vive en Webflow, colección CMS "Blog Posts" (slug /insights). Campos relevantes:
  meta-title, meta-description, post-body, secciones, FAQs.

═══════════════════════════════════════════════════════════════
## 4. CÓMO CONSTRUIRLO — 3 NIVELES (de menos a más esfuerzo)
═══════════════════════════════════════════════════════════════

### NIVEL 1 — "Prompt-receta" (lo más simple, recomendado para empezar)
Un prompt estructurado y reutilizable. La redactora o la manager pega el borrador (de Google
Docs/Word) en Claude (o el bot) con ese prompt, y recibe el reporte de revisión.
- Pro: cero infraestructura, funciona hoy, gratis.
- Contra: manual (alguien tiene que pegar el texto cada vez).
- ENTREGABLE: un archivo .md con el prompt maestro + instrucciones de uso.
- ESTE ES EL MEJOR PUNTO DE PARTIDA para validar si el feedback es útil.

### NIVEL 2 — Agente conectado a Google Docs
Un agente que lee directamente el Google Doc donde la redactora escribe (vía Google Docs API
o compartiendo el link) y deja el feedback como comentarios o un doc nuevo.
- Pro: encaja con el flujo actual (ya trabajan en Google Docs).
- Contra: requiere conectar Google Docs API; algo de setup.
- Buena opción si el Nivel 1 demuestra valor.

### NIVEL 3 — Agente conectado a Webflow (revisa lo YA publicado)
Un agente que lee los 314 artículos del CMS de Webflow (vía API/MCP, que YA está disponible —
se usó en esta auditoría) y audita el blog existente en lote.
- Pro: revisa todo el catálogo histórico, no solo lo nuevo. Encuentra los que hay que
  actualizar/mejorar (ej. los que dicen "2025", los sin CTA, los huérfanos).
- Contra: es para el contenido viejo, no para el flujo de revisión de borradores nuevos.
- IDEAL como complemento: Nivel 1/2 para lo nuevo + Nivel 3 (una vez) para limpiar lo viejo.

RECOMENDACIÓN: construir Nivel 1 primero (el prompt-receta). Si funciona, sumar Nivel 3
(barrido del blog existente vía Webflow MCP) como proyecto único de limpieza, y considerar
Nivel 2 si el equipo quiere automatizar el flujo de borradores.

═══════════════════════════════════════════════════════════════
## 5. FORMATO DE SALIDA SUGERIDO (cómo debe entregar el feedback)
═══════════════════════════════════════════════════════════════
Para cada artículo revisado, el agente entrega:

```
ARTÍCULO: [título]
PUNTAJE GLOBAL: X/10

| Dimensión        | Puntaje | Veredicto corto |
|------------------|---------|-----------------|
| Tiene sentido    | X/10    | ...             |
| No genérico      | X/10    | ...             |
| Posicionamiento  | X/10    | ...             |
| SEO              | X/10    | ...             |

✅ LO QUE ESTÁ BIEN: (2-3 puntos)
🔴 PROBLEMAS CRÍTICOS: (lo que hay que arreglar sí o sí antes de publicar)
🟡 MEJORAS SUGERIDAS: (nice to have)
📋 ACCIONES CONCRETAS (priorizadas): (3-5 cosas específicas y accionables)
```

Esto le da a la manager un veredicto rápido + a la redactora una lista clara de qué arreglar.

═══════════════════════════════════════════════════════════════
## 6. CÓMO VALIDAR QUE FUNCIONA (antes de invertir en construirlo grande)
═══════════════════════════════════════════════════════════════
Test de calibración: tomar 2-3 artículos que la MANAGER ya revisó manualmente, pasarlos por
el agente, y comparar. ¿El agente detecta lo mismo que ella detectó? ¿Coincide su criterio?
- Si SÍ → el agente está calibrado, se puede confiar y escalar.
- Si NO → ajustar el prompt con los ejemplos de ella hasta que coincida.
Esto es clave: el agente debe pensar COMO la manager, no como un revisor genérico.
Pídele a la manager 2-3 ejemplos de blogs con sus correcciones para calibrar.

═══════════════════════════════════════════════════════════════
## 7. CONEXIÓN CON LO YA EXISTENTE EN TEILUR
═══════════════════════════════════════════════════════════════
- Ya hay un BOT de marketing en Slack con acceso a Search Console, Analytics, Google Ads,
  Notion. Ese bot tiene los NÚMEROS (qué artículo trae tráfico/convierte).
- El agente de contenido tendría la CALIDAD (por qué un artículo es bueno o malo).
- COMBO IDEAL: el bot dice "este artículo tiene 500 visitas pero 0 conversiones" y el agente
  de contenido dice "porque no tiene CTA, está genérico y desactualizado". Juntos = diagnóstico
  completo. Vale la pena que, si se construye, pueda alimentarse de los datos del bot.
- Webflow MCP YA está disponible y se usó en esta auditoría → el Nivel 3 (leer los blogs del
  CMS) es técnicamente viable de inmediato.

═══════════════════════════════════════════════════════════════
## 8. RESUMEN PARA EL QUE LO CONSTRUYA (TL;DR)
═══════════════════════════════════════════════════════════════
Construir un agente que revise borradores de blog REPLICANDO el criterio de la manager de
Teilur, que evalúa: (1) que tenga sentido, (2) que no sea genérico, (3) posicionamiento de
marca, (4) SEO. Empezar por un PROMPT-RECETA reutilizable (Nivel 1) sobre el texto del
borrador. Calibrarlo con 2-3 ejemplos ya revisados por la manager. Darle el contexto de marca
de Teilur (transparent pricing, audiencia US sensible al precio, competidores, línea editorial
de "precios de competidores"). Salida: puntaje por dimensión + acciones concretas priorizadas.
Opcionalmente, sumar un barrido del blog existente vía Webflow MCP (Nivel 3) y conectarlo con
los datos del bot de marketing para cruzar calidad con rendimiento real.

DOCUMENTOS RELACIONADOS (en esta misma carpeta de auditoría, por si el constructor los necesita):
- ../INFORME-EJECUTIVO-FINAL.md (auditoría web general + contexto de marca)
- ../04-contenido-marca/RESULTADOS-SEARCHCONSOLE.md (qué artículos traen tráfico)
- ../09-funnel-leads/ANALISIS-FUNNEL.md (por qué el contenido sin CTA no convierte)
- ../06-webflow/CONTEXTO-WEBFLOW.md (cómo está montado el CMS del blog)
