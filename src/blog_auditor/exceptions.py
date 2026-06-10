"""Jerarquía de errores del Blog Auditor.

Todos los errores esperables heredan de ``BlogAuditorError`` para que la CLI
pueda atraparlos en un solo punto y mostrar un mensaje amigable al usuario.
"""


class BlogAuditorError(Exception):
    """Error base de la aplicación."""


class ConfigError(BlogAuditorError):
    """Configuración inválida o incompleta (ej. falta la API key)."""


class LoaderError(BlogAuditorError):
    """No se pudo cargar el borrador desde la fuente indicada."""


class ProviderError(BlogAuditorError):
    """Fallo en la comunicación con el proveedor de LLM."""


class ReviewParseError(BlogAuditorError):
    """El LLM devolvió una respuesta que no cumple el esquema de revisión."""
