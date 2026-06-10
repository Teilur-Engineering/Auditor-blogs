# Arquitectura y decisiones de diseño

## Principio rector

**El motor de revisión está separado de las interfaces.** El `ReviewEngine` recibe un borrador y un proveedor de LLM, y devuelve un `ReviewResult` validado. No sabe nada de CLI, Slack ni Webflow. Cualquier interfaz futura (bot de Slack en Fase 2, barrido batch de Webflow en Fase 3) reutiliza el mismo motor sin modificarlo.

```
fuente (.md/.docx/gdoc) → loaders → texto plano
                                        │
prompts (rúbrica + marca) ──────────────┤
                                        ▼
                                  ReviewEngine ──→ LLMProvider (OpenAI)
                                        │
                                        ▼
                            ReviewResult (Pydantic, validado)
                                        │
                                        ▼
                            report.py → reporte Markdown
```

## Decisiones y su porqué

### Python
Todo el ecosistema existente de Teilur/Sotant (scripts de Ads, Analytics, GSC, Notion) es Python, y las librerías necesarias (openai, python-docx, httpx, typer) son maduras.

### El criterio vive en archivos Markdown, no en código
`prompts/system_prompt.md` (la rúbrica) y `prompts/brand_context.md` (la marca) son archivos de texto empaquetados con la librería. La calibración con la manager va a requerir iterar el criterio muchas veces; editar un .md es más seguro y revisable que tocar strings dentro de Python.

### Proveedor de LLM detrás de un Protocol
`llm/base.py` define el contrato (`generate_json`); `OpenAIProvider` es la única implementación hoy. El modelo es un string configurable (`OPENAI_MODEL` o `--model`) para poder bajar de gpt-5.4 a un modelo más barato sin tocar código. Si algún día se quiere otro proveedor, se implementa el Protocol y se inyecta al motor.

### `json_object` + validación Pydantic (en vez de structured outputs estrictos)
El modo `response_format={"type": "json_object"}` funciona igual en todos los modelos de OpenAI, lo que mantiene la libertad de cambiar de modelo. La garantía de esquema la da Pydantic en el motor: si la respuesta no valida, se reintenta UNA vez informando el error; si vuelve a fallar, se lanza `ReviewParseError` con el detalle. Nunca se entrega un reporte construido sobre datos inválidos.

### Google Docs por link público, sin OAuth
`gdoc_loader.py` usa el endpoint de exportación (`/export?format=txt`), que funciona con docs compartidos como "cualquiera con el enlace". Evita todo el setup de Google Cloud/OAuth en Fase 1. Si el equipo necesita docs privados, ese módulo es el punto de extensión para la API oficial.

### Validaciones en los bordes
- `config.py` falla al arranque si no hay API key (mensaje con instrucciones).
- Los loaders validan existencia, formato y encoding, con errores accionables (`LoaderError`).
- El motor rechaza borradores de menos de 300 caracteres antes de gastar tokens.
- Toda excepción esperable hereda de `BlogAuditorError` y la CLI la muestra amigable (exit code 1).

### Inmutabilidad
`Settings` y `ArticleDraft` son dataclasses congeladas; los modelos Pydantic usan `frozen=True`. Un resultado de revisión no se modifica después de creado.

## Cómo extender

| Quiero... | Toco... |
|---|---|
| Ajustar el criterio de revisión | `prompts/system_prompt.md` |
| Actualizar contexto de marca | `prompts/brand_context.md` |
| Soportar otro formato de borrador | nuevo loader en `loaders/` + registrarlo en `dispatch.py` |
| Agregar otro proveedor de LLM | nueva clase que cumpla `llm/base.py` |
| Agregar comando (batch, calibrate...) | nueva función `@app.command()` en `cli.py` |
| Cambiar el formato del reporte | `review/report.py` |

## Fase 2 y 3 (previstas, no construidas)

- **Slack (Fase 2):** un handler de Slack que reciba el texto/link, llame a `ReviewEngine` y responda con el reporte. Candidato a desplegarse en el VPS donde ya corre el bot de marketing de Teilur.
- **Webflow batch (Fase 3):** comando `batch` que lea la colección "Blog Posts" del CMS de Webflow (la API/MCP ya se usó en la auditoría previa), pase cada artículo por el motor y genere un ranking de los que necesitan actualización. Solo tiene sentido DESPUÉS de calibrar el criterio.
