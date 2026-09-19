import os
import re
from groq import Groq
from ingesta_rag import buscar_en_rag
from mcp_server import consultar_servidor_mcp


def _get_api_key():
    try:
        import streamlit as st
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("GROQ_API_KEY")


client = Groq(api_key=_get_api_key())
MAX_INTENTOS = 3
historial_conversacion = []

MODELO_CLASIFICACION = "openai/gpt-oss-20b"
MODELO_EVALUACION = "openai/gpt-oss-20b"
MODELO_REDACTOR = "openai/gpt-oss-120b"


def limpiar_respuesta_llm(texto):
    """Elimina tags de razonamiento y extrae solo la respuesta final."""
    if not texto:
        return ""
    if "<think>" in texto:
        partes = texto.split("</think>")
        if len(partes) > 1:
            texto = partes[-1]
        else:
            return texto.strip()
    return texto.strip()


def llamar_llm(modelo, messages, temperature=0.1, max_tokens=1500):
    """Llamada segura a LLM con manejo de errores."""
    try:
        kwargs = {
            "model": modelo,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        completion = client.chat.completions.create(**kwargs)
        respuesta = completion.choices[0].message.content
        return limpiar_respuesta_llm(respuesta)
    except Exception as e:
        print(f"[LLM Error] Modelo {modelo}: {e}")
        return None


def agente_buscador(pregunta_original):
    """
    Arquitectura ReAct:
    Razona (clasifica tipo de pregunta) -> Actua (busca en RAG)
    -> Observa (evalua si es suficiente)
    -> si no: Actua (consulta MCP) -> Observa de nuevo
    -> si no: Razona (reformula) -> repite max 3 veces
    """
    pregunta = pregunta_original
    contexto_acumulado = ""
    fuentes_acumuladas = []

    # RAZONA: clasificar si la pregunta es historica o cultural
    respuesta_clasificacion = llamar_llm(
        MODELO_CLASIFICACION,
        [
            {"role": "system", "content": "Solo responde SI o NO."},
            {"role": "user", "content": (
                f"¿La siguiente pregunta es sobre historia, origen, cultura o tradicion "
                f"de la gastronomia venezolana, y NO sobre como preparar una receta? '{pregunta_original}'"
            )}
        ],
        temperature=0,
        max_tokens=50
    )
    es_historica = respuesta_clasificacion is not None and "SI" in respuesta_clasificacion.upper()
    print(f"[Buscador ReAct] ¿Es pregunta historica/cultural? {es_historica}")

    for intento in range(MAX_INTENTOS):
        print(f"\n[Buscador ReAct] Intento {intento + 1}/{MAX_INTENTOS}: '{pregunta}'")

        # ACTUA: buscar en RAG local con similitud coseno
        contexto_local, fuentes_locales = buscar_en_rag(pregunta, k=5)
        if contexto_local:
            contexto_acumulado += "\n" + contexto_local
            for f in fuentes_locales:
                if f not in fuentes_acumuladas:
                    fuentes_acumuladas.append(f)

        # OBSERVA: si es historica forzar MCP, si no evaluar normalmente
        if es_historica:
            contexto_suficiente = False
            print(f"[Buscador ReAct] Pregunta historica, forzando consulta MCP...")
        elif fuentes_locales:
            respuesta_evaluacion = llamar_llm(
                MODELO_EVALUACION,
                [
                    {"role": "system", "content": "Solo responde SI o NO."},
                    {"role": "user", "content": (
                        f"¿El siguiente contexto de recetas contiene información para responder a: '{pregunta}'?\n"
                        f"Responde SI si contiene la receta o ingredientes/preparación relevantes.\n\n"
                        f"CONTEXTO:\n{contexto_acumulado}"
                    )}
                ],
                temperature=0,
                max_tokens=50
            )
            # Si el evaluador responde SI o si el RAG local arrojó fuentes directas
            contexto_suficiente = (
                (respuesta_evaluacion is not None and "SI" in respuesta_evaluacion.upper())
                or bool(fuentes_locales and len(contexto_acumulado.strip()) > 80)
            )
            print(f"[Buscador ReAct] ¿RAG suficiente? {contexto_suficiente}")
        else:
            contexto_suficiente = False
            print(f"[Buscador ReAct] ¿RAG suficiente? False (sin coincidencias locales)")

        # ACTUA: consultar MCP si RAG no fue suficiente o es pregunta historica
        if not contexto_suficiente and "Wikipedia (Servidor MCP)" not in fuentes_acumuladas:
            print(f"[Buscador ReAct] Consultando MCP...")
            contexto_mcp = consultar_servidor_mcp(pregunta)
            if contexto_mcp:
                contexto_acumulado += f"\n--- Fuente: Wikipedia (Servidor MCP) ---\n{contexto_mcp}\n"
                fuentes_acumuladas.append("Wikipedia (Servidor MCP)")

                # OBSERVA de nuevo: evaluar si MCP complemento suficientemente
                respuesta_evaluacion_mcp = llamar_llm(
                    MODELO_EVALUACION,
                    [
                        {"role": "system", "content": "Solo responde SI o NO."},
                        {"role": "user", "content": (
                            f"¿El siguiente contexto menciona algo relacionado con '{pregunta}'? "
                            f"Responde SI si hay aunque sea algo relevante.\n\n"
                            f"CONTEXTO:\n{contexto_acumulado}"
                        )}
                    ],
                    temperature=0,
                    max_tokens=100
                )
                contexto_suficiente = respuesta_evaluacion_mcp is not None and "SI" in respuesta_evaluacion_mcp.upper()
                print(f"[Buscador ReAct] ¿RAG + MCP suficiente? {contexto_suficiente}")
                es_historica = False

        if contexto_suficiente:
            break

        # RAZONA: reformular si no es el ultimo intento
        if intento + 1 < MAX_INTENTOS:
            print(f"[Buscador ReAct] Reformulando pregunta...")
            respuesta_reformulacion = llamar_llm(
                MODELO_EVALUACION,
                [
                    {"role": "system", "content": (
                        "Reformula la pregunta de forma mas corta y especifica. "
                        "Usa terminos venezolanos correctos como caraotas, pabellon, cachapas, arepas. "
                        "Responde SOLO con la nueva pregunta, sin explicaciones."
                    )},
                    {"role": "user", "content": f"Reformula de forma corta y especifica: '{pregunta}'"}
                ],
                temperature=0.3,
                max_tokens=100
            )
            if respuesta_reformulacion:
                pregunta = respuesta_reformulacion.strip()
                print(f"[Buscador ReAct] Nueva pregunta: '{pregunta}'")

    return contexto_acumulado, fuentes_acumuladas


def agente_redactor(pregunta_original, contexto, fuentes):
    """
    Arquitectura Chain directa.
    Usa historial conversacional para mantener contexto entre preguntas.
    Genera respuesta final con citas obligatorias.
    """
    print(f"\n[Redactor] Generando respuesta final...")

    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres el Agente Chef Redactor de cocina venezolana.\n\n"
                "FORMATO OBLIGATORIO PARA RECETAS:\n"
                "# [Nombre del plato]\n\n"
                "## Ingredientes:\n"
                "- [ingrediente 1]\n"
                "- [ingrediente 2]\n\n"
                "## Preparacion:\n"
                "1. [paso 1]\n"
                "2. [paso 2]\n\n"
                "## Region: [region]\n"
                "## Tiempo de preparacion: [tiempo]\n"
                "## Porciones: [porciones]\n\n"
                "📚 Fuentes consultadas:\n"
                "- [nombre_archivo]\n\n"
                "REGLAS:\n"
                "- Los ingredientes van en lista con guion (-)\n"
                "- Los pasos van numerados (1. 2. 3.)\n"
                "- Si el corpus no tiene Region/Tiempo/Porciones, omite esas lineas\n"
                "- SIEMPRE incluye las fuentes al final\n"
                "- NUNCA empieces con 'Segun la receta' o similar\n"
                "- Ve directo al contenido, sin introducciones\n\n"
                "Para preguntas de historia/cultura: responde en parrafos normales y al final lista las fuentes.\n"
                "Para diferencias: usa formato comparativo y al final lista las fuentes."
            )
        },
        *historial_conversacion,
        {
            "role": "user",
            "content": (
                f"CONTEXTO DEL CORPUS:\n{contexto}\n\n"
                f"PREGUNTA: {pregunta_original}\n\n"
                f"INSTRUCCIONES:\n"
                f"- Extrae ingredientes y pasos EXACTAMENTE como aparecen en el contexto\n"
                f"- Numeras los pasos de preparacion (1. 2. 3.)\n"
                f"- Si hay Region, Tiempo o Porciones en el contexto, incluyelos\n"
                f"- Si falta informacion en el contexto, indica 'No disponible en la fuente'\n"
                f"- Lista las fuentes al final en formato: - [nombre_archivo]"
            )
        }
    ]

    respuesta = llamar_llm(MODELO_REDACTOR, mensajes, temperature=0.1, max_tokens=2000)

    if respuesta:
        historial_conversacion.append({"role": "user",      "content": pregunta_original})
        historial_conversacion.append({"role": "assistant", "content": respuesta})

        if len(historial_conversacion) > 6:
            del historial_conversacion[:2]
    else:
        respuesta = "Error: No se pudo generar una respuesta. Verifica la conexion con Groq."

    return respuesta


def procesar_pregunta(pregunta: str) -> str:
    """Coordina los dos agentes: Buscador ReAct -> Redactor Chain."""
    contexto, fuentes = agente_buscador(pregunta)
    respuesta = agente_redactor(pregunta, contexto, fuentes)
    return respuesta
