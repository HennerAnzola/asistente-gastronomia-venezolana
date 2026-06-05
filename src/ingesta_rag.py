import os
import faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
carpeta_data = os.path.join(BASE_DIR, "data")

def dividir_en_chunks(texto, fuente):
    """Divide un documento en fragmentos con solapamiento."""
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + CHUNK_SIZE, len(texto))
        fragmento = texto[inicio:fin].strip()
        if fragmento:
            chunks.append({"fuente": fuente, "contenido": fragmento})
        # Avanzar siempre hacia adelante garantizando progreso
        inicio += CHUNK_SIZE - CHUNK_OVERLAP
        if inicio >= len(texto):
            break
    return chunks

_index_faiss = None
_corpus_chunks = None

def obtener_base_vectorial():
    """Carga la base vectorial solo una vez y la reutiliza."""
    global _index_faiss, _corpus_chunks

    if _index_faiss is not None:
        return _index_faiss, _corpus_chunks

    todos_los_chunks = []
    textos = []

    for archivo in sorted(os.listdir(carpeta_data)):
        if archivo.endswith(".txt"):
            ruta = os.path.join(carpeta_data, archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            chunks = dividir_en_chunks(contenido, archivo)
            todos_los_chunks.extend(chunks)
            textos.extend([c["contenido"] for c in chunks])

    embeddings = model.encode(textos, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    _index_faiss = index
    _corpus_chunks = todos_los_chunks

    return _index_faiss, _corpus_chunks

def buscar_en_rag(query, k=5):
    """Busca los k chunks mas similares usando similitud coseno."""
    index_faiss, corpus_chunks = obtener_base_vectorial()

    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)

    scores, indices = index_faiss.search(query_embedding, k)

    contexto = ""
    fuentes = []
    for i, idx in enumerate(indices[0]):
        if idx < len(corpus_chunks):
            chunk = corpus_chunks[idx]
            contexto += f"--- Fuente: {chunk['fuente']} ---\n{chunk['contenido']}\n\n"
            if chunk['fuente'] not in fuentes:
                fuentes.append(chunk['fuente'])

    return contexto, fuentes