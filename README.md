# SaborCriollo AI — Asistente Gastronómico Venezolano

[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://henneranzola-asistente-gastronomia-venezolana.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq-LLM-7C3AED?logo=groq)](https://groq.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector-007EC6)](https://faiss.ai)

> Un asistente conversacional que combina una arquitectura multi-agente con un motor RAG para responder recetas de cocina tradicional venezolana. Desplegado en Streamlit Cloud.

**[App en vivo](https://henneranzola-asistente-gastronomia-venezolana.streamlit.app)**

---

## Arquitectura

```
Pregunta del usuario
        │
        ▼
┌──────────────────┐
│  Agente Buscador │  ← Clasifica (receta vs. historia)
│     (ReAct)      │  ← Busca en FAISS local
│                  │  ← Consulta Wikipedia si es necesario
└────────┬─────────┘
         │ contexto + fuentes
         ▼
┌──────────────────┐
│  Agente Redactor │  ← Formatea respuesta con citations
│     (Chain)      │  ← Gestiona historial conversacional
└────────┬─────────┘
         │ respuesta formateada
         ▼
   Streamlit UI + PDF
```

### Componentes

| Archivo | Rol |
|---------|-----|
| `src/app.py` | Interfaz Streamlit — layout de dos paneles, chat + lienzo de receta |
| `src/agents.py` | Pipeline multi-agente: Buscador (ReAct) → Redactor (Chain) |
| `src/ingesta_rag.py` | Motor RAG: embeddings con FAISS + búsqueda híbrida (léxica + semántica) |
| `src/mcp_server.py` | Conector a Wikipedia en español para contexto cultural |
| `src/skill_receta.py` | Generación de PDF con fpdf2 |

---

## Despliegue

La aplicación está desplegada en **Streamlit Cloud**. Para ejecutar localmente:

```bash
# 1. Clonar
git clone https://github.com/HennerAnzola/asistente-gastronomia-venezolana.git
cd asistente-gastronomia-venezolana

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# Editar .env con tu GROQ_API_KEY (https://console.groq.com/keys)

# 5. Ejecutar
streamlit run src/app.py
```

---

## Stack

- **LLM:** Groq (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`)
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector DB:** FAISS (IndexFlatIP con similitud coseno)
- **UI:** Streamlit
- **PDF:** fpdf2
- **Datos:** 14 recetarios en texto plano (`data/*.txt`)

---

## Licencia

Proyecto académico — Universidad Tecnológica del Perú (UTP).
