import wikipedia

# Configurar idioma español para la API de Wikipedia
wikipedia.set_lang("es")

def consultar_servidor_mcp(termino_busqueda):
    """
    Servidor MCP (Model Context Protocol) de contexto cultural e histórico externo.
    Utiliza búsqueda previa (search) para evitar errores de página inexistente o desambiguación.
    """
    if not termino_busqueda or not termino_busqueda.strip():
        return ""

    try:
        # 1. Buscar títulos reales en Wikipedia en español
        query = f"Gastronomia de Venezuela {termino_busqueda}"
        resultados = wikipedia.search(query, results=3)
        
        if not resultados:
            # Reintentar buscando el término directo
            resultados = wikipedia.search(termino_busqueda, results=3)
            
        if resultados:
            for titulo in resultados:
                try:
                    resumen = wikipedia.summary(titulo, sentences=3, auto_suggest=False)
                    if resumen and len(resumen) > 30:
                        return resumen
                except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                    continue
        return ""
    except Exception as e:
        print(f"[MCP Wikipedia Error]: {e}")
        return ""