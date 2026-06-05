import os
from groq import Groq
from dotenv import load_dotenv
from ingesta_rag import buscar_en_rag
from mcp_server import consultar_servidor_mcp

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MAX_INTENTOS = 3
historial_conversacion = []

# ─────────────────────────────────────────────
# AGENTE 1 — BUSCADOR (ReAct)
# ─────────────────────────────────────────────
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
    # Si lo es, ir directo al MCP sin esperar que el RAG falle
    clasificacion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Solo responde SI o NO."},
            {"role": "user", "content": (
                f"¿La siguiente pregunta es sobre historia, origen, cultura o tradicion "
                f"de la gastronomia venezolana, y NO sobre como preparar una receta? '{pregunta_original}'"
            )}
        ],
        temperature=0,
        max_tokens=5
    )
    es_historica = "SI" in clasificacion.choices[0].message.content.upper()
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
        else:
            evaluacion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Solo responde SI o NO."},
                    {"role": "user",   "content": (
                        f"¿El siguiente contexto menciona algo relacionado con '{pregunta}'? "
                        f"Responde SI si hay aunque sea algo relevante.\n\n"
                        f"CONTEXTO:\n{contexto_acumulado}"
                    )}
                ],
                temperature=0,
                max_tokens=5
            )
            contexto_suficiente = "SI" in evaluacion.choices[0].message.content.upper()
            print(f"[Buscador ReAct] ¿RAG suficiente? {contexto_suficiente}")

        # ACTUA: consultar MCP si RAG no fue suficiente o es pregunta historica
        if not contexto_suficiente and "Wikipedia (Servidor MCP)" not in fuentes_acumuladas:
            print(f"[Buscador ReAct] Consultando MCP...")
            contexto_mcp = consultar_servidor_mcp(pregunta)
            if contexto_mcp:
                contexto_acumulado += f"\n--- Fuente: Wikipedia (Servidor MCP) ---\n{contexto_mcp}\n"
                fuentes_acumuladas.append("Wikipedia (Servidor MCP)")

                # OBSERVA de nuevo: evaluar si MCP complemento suficientemente
                evaluacion_mcp = client.chat.completions.create( 
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "Solo responde SI o NO."},
                        {"role": "user",   "content": (
                            f"¿El siguiente contexto menciona algo relacionado con '{pregunta}'? "
                            f"Responde SI si hay aunque sea algo relevante.\n\n"
                            f"CONTEXTO:\n{contexto_acumulado}"
                        )}
                    ],
                    temperature=0,
                    max_tokens=5
                )
                contexto_suficiente = "SI" in evaluacion_mcp.choices[0].message.content.upper()
                print(f"[Buscador ReAct] ¿RAG + MCP suficiente? {contexto_suficiente}")
                # Una vez consultado el MCP en pregunta historica, continuar al Redactor
                es_historica = False

        if contexto_suficiente:
            break

        # RAZONA: reformular si no es el ultimo intento
        if intento + 1 < MAX_INTENTOS:
            print(f"[Buscador ReAct] Reformulando pregunta...")
            reformulacion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": (
                        "Reformula la pregunta de forma mas corta y especifica. "
                        "Usa terminos venezolanos correctos como caraotas, pabellon, cachapas, arepas. "
                        "Responde SOLO con la nueva pregunta, sin explicaciones."
                    )},
                    {"role": "user", "content": f"Reformula de forma corta y especifica: '{pregunta}'"}
                ],
                temperature=0.3,
                max_tokens=50
            )
            pregunta = reformulacion.choices[0].message.content.strip()
            print(f"[Buscador ReAct] Nueva pregunta: '{pregunta}'")

    return contexto_acumulado, fuentes_acumuladas

# ─────────────────────────────────────────────
# AGENTE 2 — REDACTOR (Chain)
# ─────────────────────────────────────────────
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
                "Eres el Agente Chef Redactor de cocina venezolana. "
                "Responde SIEMPRE con este formato exacto cuando sea una receta:\n"
                "1. Nombre del plato como titulo\n"
                "2. Seccion 'Ingredientes:' con lista completa\n"
                "3. Seccion 'Preparacion:' con pasos numerados\n"
                "4. Seccion 'Region:' y 'Tiempo de preparacion:' si estan disponibles\n"
                "5. Al final SIEMPRE '📚 Fuentes consultadas:' listando TODOS los archivos usados\n\n"
                "Si la pregunta es sobre historia o cultura: responde en narrativa y al final lista las fuentes.\n"
                "Si la pregunta es sobre diferencias: usa comparacion y al final lista las fuentes.\n"
                "NUNCA empieces con 'Segun la receta proporcionada' ni frases similares.\n"
                "NUNCA menciones las fuentes al inicio, solo al final.\n"
                "Ve directo al contenido."
            )
        },
        *historial_conversacion,
        {
            "role": "user",
            "content": (
                f"USA EXACTAMENTE esta informacion del corpus para responder:\n\n"
                f"{contexto}\n\n"
                f"PREGUNTA: {pregunta_original}\n\n"
                f"IMPORTANTE: Usa solo los ingredientes y pasos que aparecen arriba. No agregues nada extra."
            )
        }
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes,
            temperature=0.1,
            max_tokens=1000
        )
        respuesta = completion.choices[0].message.content

        historial_conversacion.append({"role": "user",      "content": pregunta_original})
        historial_conversacion.append({"role": "assistant", "content": respuesta})

        if len(historial_conversacion) > 6:
            del historial_conversacion[:2]

    except Exception as e:
        respuesta = f"Error en el Agente Redactor: {str(e)}"

    return respuesta

# ─────────────────────────────────────────────
# FUNCION PRINCIPAL
# ─────────────────────────────────────────────
def procesar_pregunta(pregunta: str) -> str:
    """Coordina los dos agentes: Buscador ReAct -> Redactor Chain."""
    contexto, fuentes = agente_buscador(pregunta)
    respuesta = agente_redactor(pregunta, contexto, fuentes)
    return respuesta 