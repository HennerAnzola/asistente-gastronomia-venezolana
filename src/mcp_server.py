import wikipedia

# Configurar idioma español para la API de Wikipedia
wikipedia.set_lang("es")

def consultar_servidor_mcp(termino_busqueda):
    """
    Servidor MCP (Model Context Protocol) dedicado.
    Expone Wikipedia como herramienta de contexto cultural e historico externo.
    Primero busca con contexto venezolano, si no encuentra busca directamente.
    Retorna vacio si no encuentra nada para no romper el flujo.
    """
    try:
        # Primero intenta con contexto gastronómico venezolano
        resultado = wikipedia.summary(
            f"Gastronomia de Venezuela {termino_busqueda}",
            sentences=3
        )
        return resultado
    except Exception:
        try:
            # Si no encuentra, busca el termino directamente
            resultado = wikipedia.summary(termino_busqueda, sentences=3)
            return resultado
        except Exception:
            return ""