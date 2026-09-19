"""
Módulo de Ingesta y Recuperación RAG para Gastronomía Venezolana.
Segmenta los documentos por recetas completas y realiza búsqueda híbrida (léxica + semántica).
"""

import os
import re
import faiss
from sentence_transformers import SentenceTransformer

# Modelo ligero de embeddings multilingüe/inglés de alto rendimiento
modelo_embeddings = SentenceTransformer("all-MiniLM-L6-v2")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATA = os.path.join(BASE_DIR, "data")

# Caché en memoria para no reconstruir el índice en cada consulta
_indice_faiss = None
_corpus_recetas = None


def dividir_en_recetas(texto: str, fuente: str) -> list[dict]:
    """
    Segmentación por receta completa.
    Divide el documento usando los saltos de línea dobles entre recetas.
    Cada bloque contiene: Título, Ingredientes, Preparación, Región, Tiempo y Porciones.
    """
    texto_normalizado = texto.replace("\r\n", "\n").strip()
    if not texto_normalizado:
        return []

    # Extraer y filtrar bloques de texto que cumplan con la longitud mínima
    bloques = (b.strip() for b in re.split(r'\n\s*\n', texto_normalizado))
    recetas = [
        {"fuente": fuente, "contenido": bloque}
        for bloque in bloques
        if len(bloque) > 20
    ]

    # Respaldo en caso de documento de una sola receta sin doble salto o bloques cortos
    return recetas if recetas else [{"fuente": fuente, "contenido": texto_normalizado}]


def obtener_base_vectorial():
    """Carga los recetarios, segmenta por receta e indexa en FAISS con similitud coseno."""
    global _indice_faiss, _corpus_recetas

    if _indice_faiss is not None:
        return _indice_faiss, _corpus_recetas

    todas_las_recetas = []
    textos_para_vectorizar = []

    for archivo in sorted(os.listdir(CARPETA_DATA)):
        if archivo.endswith(".txt"):
            ruta = os.path.join(CARPETA_DATA, archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            recetas_doc = dividir_en_recetas(contenido, archivo)
            todas_las_recetas.extend(recetas_doc)
            textos_para_vectorizar.extend([r["contenido"] for r in recetas_doc])

    # Generar embeddings y normalizar L2 para similitud coseno
    embeddings = modelo_embeddings.encode(textos_para_vectorizar, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    indice = faiss.IndexFlatIP(dimension)
    indice.add(embeddings)

    _indice_faiss = indice
    _corpus_recetas = todas_las_recetas

    return _indice_faiss, _corpus_recetas


def buscar_en_rag(consulta: str, k: int = 5):
    """
    Búsqueda híbrida:
    1. Búsqueda léxica directa por palabras clave en los títulos de recetas.
    2. Búsqueda semántica vectorial con FAISS (similitud coseno).
    Concatena el contexto agrupado por fuente bibliográfica.
    """
    indice_faiss, corpus_recetas = obtener_base_vectorial()

    resultados_por_fuente = {}

    def agregar_receta(receta):
        fuente = receta["fuente"]
        contenido = receta["contenido"]
        if fuente not in resultados_por_fuente:
            resultados_por_fuente[fuente] = []
        if contenido not in resultados_por_fuente[fuente]:
            resultados_por_fuente[fuente].append(contenido)

    # 1. Búsqueda léxica (palabras clave en el título de cada receta)
    palabras_clave = [p.lower() for p in re.findall(r'\w+', consulta) if len(p) >= 3]
    for receta in corpus_recetas:
        linea_titulo = receta["contenido"].split("\n")[0].lower()
        if any(palabra in linea_titulo for palabra in palabras_clave):
            agregar_receta(receta)

    # 2. Búsqueda semántica con FAISS
    vector_consulta = modelo_embeddings.encode([consulta], convert_to_numpy=True)
    faiss.normalize_L2(vector_consulta)
    _, indices = indice_faiss.search(vector_consulta, k)

    for idx in indices[0]:
        if 0 <= idx < len(corpus_recetas):
            agregar_receta(corpus_recetas[idx])

    # 3. Construir contexto y lista de fuentes
    contexto = ""
    fuentes = list(resultados_por_fuente.keys())
    for fuente in fuentes:
        texto_recetas = "\n\n".join(resultados_por_fuente[fuente])
        contexto += f"--- Fuente: {fuente} ---\n{texto_recetas}\n\n"

    return contexto, fuentes