# Blog Auditor — Teilur Talent

Agente de IA que revisa **borradores de artículos de blog antes de publicarlos**, replicando el criterio de la manager de contenido de Teilur Talent. Recibe un borrador (Markdown, Word o Google Docs) y entrega un reporte con puntaje por dimensión y acciones concretas para la redactora.

**No es un auditor del sitio en vivo**: es un revisor de borradores, igual que la manager, que trabaja sobre el documento antes de publicar.

## Qué evalúa

| Dimensión | Pregunta que responde |
|---|---|
| **Tiene sentido** | ¿Es coherente, bien argumentado, con datos respaldados por fuentes? |
| **No genérico** | ¿Aporta algo único o es relleno "AI slop"? *(el criterio más importante)* |
| **Posicionamiento** | ¿Refleja la marca Teilur y su diferenciador de transparent pricing? |
| **SEO** | ¿Título, meta description, keyword, enlaces internos, CTA, fechas al día? |

El reporte sale en español con: puntaje global, tabla por dimensión, lo que está bien, problemas críticos, mejoras sugeridas y 3-5 acciones priorizadas. El formato exacto está definido en [src/blog_auditor/review/report.py](src/blog_auditor/review/report.py).

## Inicio rápido

Requisitos: Python 3.10+ y una API key de OpenAI.

```bash
# 1. Clonar e instalar
git clone https://github.com/Teilur-Engineering/Auditor-blogs.git
cd Auditor-blogs
python -m venv .venv
.venv\Scripts\activate          # Windows  (en Linux/Mac: source .venv/bin/activate)
pip install -e ".[dev]"

# 2. Configurar
copy .env.example .env          # y poner tu OPENAI_API_KEY dentro

# 3. Revisar un borrador
blog-auditor review examples/borrador-ejemplo.md
```

## Uso

```bash
# Archivo local (.md, .txt, .docx o .pdf)
blog-auditor review borrador.docx

# Google Doc compartido como "cualquiera con el enlace puede ver"
# (formato preferido: es el único que conserva los hipervínculos, así el
#  agente verifica de verdad los enlaces internos en vez de adivinar)
blog-auditor review "https://docs.google.com/document/d/XXXX/edit"

# Indicando la keyword SEO objetivo (si no, el revisor la infiere)
blog-auditor review borrador.md --keyword "toptal pricing"

# Cambiar de modelo puntualmente (ej. para abaratar)
blog-auditor review borrador.md --model gpt-5.3

# Solo imprimir, sin guardar reporte
blog-auditor review borrador.md --no-save

# Iniciar el bot de Slack (requiere tokens, ver docs/DESPLIEGUE-SLACK.md)
blog-auditor slack
```

Por defecto cada reporte se guarda en `reports/` (carpeta ignorada por git porque contiene contenido del cliente).

### Desde Slack (para la redactora y la manager)

Con el bot corriendo (guía completa en [docs/DESPLIEGUE-SLACK.md](docs/DESPLIEGUE-SLACK.md)), basta con enviarle un DM o mencionarlo con: el link de un Google Doc público, un archivo adjunto (`.docx`, `.pdf`, `.md`, `.txt`) o el texto pegado. Responde en el hilo con el resumen de puntajes y el reporte completo adjunto. Keyword opcional: `keyword: toptal pricing` en el mismo mensaje.

## Configuración

Variables de entorno (archivo `.env`, ver [.env.example](.env.example)):

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `OPENAI_API_KEY` | Sí | — | API key de OpenAI |
| `OPENAI_MODEL` | No | `gpt-5.4` | Modelo a usar; se puede bajar a uno más barato sin tocar código |
| `REPORTS_DIR` | No | `reports` | Carpeta donde se guardan los reportes |
| `SLACK_BOT_TOKEN` | Solo modo Slack | — | Bot User OAuth Token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Solo modo Slack | — | App-Level Token con `connections:write` (`xapp-...`) |

## Mapa del proyecto

Guía rápida de dónde está cada cosa (para humanos y para IAs):

```
src/blog_auditor/
├── cli.py                  # Interfaz de línea de comandos (typer)
├── config.py               # Carga y validación de .env (Settings inmutable)
├── exceptions.py           # Jerarquía de errores de la app
├── llm/
│   ├── base.py             # Protocolo LLMProvider (contrato de cualquier proveedor)
│   └── openai_provider.py  # Implementación sobre la API de OpenAI
├── loaders/
│   ├── dispatch.py         # Decide qué loader usar según la fuente
│   ├── text_loader.py      # .txt / .md (UTF-8 con fallback cp1252)
│   ├── docx_loader.py      # .docx (convierte headings de Word a Markdown)
│   ├── pdf_loader.py       # .pdf (pypdf; pierde jerarquía de headings y enlaces)
│   ├── gdoc_loader.py      # Google Docs vía link público (HTML, sin OAuth)
│   └── html_extract.py     # extrae texto, headings y enlaces del HTML de Google Docs
├── review/
│   ├── engine.py           # Orquesta: prompts + LLM + validación (con 1 reintento)
│   ├── models.py           # Esquema Pydantic del resultado (contrato con el LLM)
│   └── report.py           # Renderiza el reporte Markdown final
├── slack/
│   ├── app.py              # Arranque del bot (Socket Mode)
│   ├── handlers.py         # Mensajes entrantes → motor → respuesta en hilo
│   └── formatting.py       # ReviewResult → bloques de resumen de Slack
└── prompts/
    ├── system_prompt.md    # LA RÚBRICA: el criterio de la manager, dimensión por dimensión
    └── brand_context.md    # Contexto de marca de Teilur (transparent pricing, etc.)

deploy/slack-app-manifest.yaml  # Manifest para crear la Slack app en 5 minutos
```

**Para ajustar el criterio de revisión** (lo que se hará durante la calibración): editar [src/blog_auditor/prompts/system_prompt.md](src/blog_auditor/prompts/system_prompt.md). **Para actualizar el contexto de marca**: [src/blog_auditor/prompts/brand_context.md](src/blog_auditor/prompts/brand_context.md). No hay que tocar código Python para ninguna de las dos cosas.

Más detalle de decisiones de diseño en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Calibración (paso obligatorio antes de confiar en el agente)

El agente debe pensar **como la manager**, no como un revisor genérico. Antes de usarlo en serio hay que pasarle 2-3 artículos que ella ya revisó y comparar veredictos. El proceso completo está en [docs/CALIBRACION.md](docs/CALIBRACION.md).

## Desarrollo

```bash
.venv\Scripts\python -m pytest --cov=blog_auditor    # tests + cobertura (mín. 80%)
.venv\Scripts\python -m ruff check src tests          # linter
.venv\Scripts\python -m ruff format src tests         # formateo
```

Los tests no llaman a OpenAI: el motor se prueba con un proveedor falso ([tests/test_engine.py](tests/test_engine.py)).

## Roadmap

- **Fase 1 (hecha):** motor + CLI. Calibración en curso con artículos reales de la manager (ver [docs/CALIBRACION.md](docs/CALIBRACION.md)).
- **Fase 2 (hecha, pendiente de desplegar):** bot de Slack para la redactora y la manager (ver [docs/DESPLIEGUE-SLACK.md](docs/DESPLIEGUE-SLACK.md)).
- **Fase 3:** comando `batch` que audite los ~314 artículos ya publicados en el CMS de Webflow (colección "Blog Posts", slug `/insights`) y cruce calidad con los datos de tráfico del bot de marketing. Se hará después de calibrar.

La idea original y todo el contexto de negocio están en [docs/PROPUESTA-AGENTE-CALIDAD-BLOGS.md](docs/PROPUESTA-AGENTE-CALIDAD-BLOGS.md).
