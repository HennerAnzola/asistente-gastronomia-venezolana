# 🇻🇪 Chef Asistente Gastronómico Virtual

Un sistema conversacional avanzado e inteligente especializado en la cocina tradicional y la cultura culinaria venezolana. Este proyecto implementa una arquitectura **Multi-Agente** propia y un motor de recuperación **RAG (Retrieval-Augmented Generation)** optimizado sobre memoria RAM para garantizar respuestas verídicas, contextualizadas y libres de alucinaciones.

---

## 🚀 Características Principales

- **Arquitectura Multi-Agente Nativa:** Flujo de trabajo coordinado mediante dos agentes con roles acoplados y responsabilidades totalmente segregadas (Buscador + Redactor).
- **Orquestación ReAct (Reasoning & Acting):** El agente de búsqueda evalúa semánticamente la intención del usuario y decide dinámicamente qué herramientas utilizar.
- **Motor RAG con FAISS:** Indexación local de documentos con segmentación de texto por ventanas deslizantes (*chunking* con solapamiento) y cálculo de similitud coseno de alta velocidad.
- **Conectividad MCP (Model Context Protocol):** Integración en tiempo real con un servidor externo de Wikipedia para la resolución de consultas históricas y de contexto cultural.
- **Skill de Exportación Dinámica:** Generación automatizada y descarga de recetas consultadas en formato PDF.

---

## 🛠️ Arquitectura del Sistema

El proyecto está diseñado bajo un pipeline secuencial de procesamiento donde el estado es compartido de forma determinista entre los componentes:

1. **Agente 1: Buscador (ReAct):**
   - *Razona:* Clasifica si la pregunta es técnica (receta) o histórica.
   - *Actúa:* Recupera embeddings vectoriales de la base local de FAISS.
   - *Observa:* Evalúa a través de un LLM si los datos recopilados son suficientes. Si se requiere información complementaria, consume el servidor MCP de Wikipedia.
   - *Re-Razona:* Optimiza y reformula la consulta si la búsqueda inicial no arroja resultados satisfactorios.
2. **Agente 2: Redactor (Chain):**
   - Toma el contexto crudo consolidado por el buscador.
   - Aplica restricciones estrictas de formato (Ingredientes, Preparación, Región).
   - Gestiona la memoria a corto plazo e historial conversacional del chat.

---

## 📦 Requisitos Previos e Instalación

Para clonar y ejecutar este proyecto localmente, sigue estos pasos estructurados:

### 1. Clonar el repositorio y acceder a la carpeta
```bash
git clone <URL_DEL_REPOSITORIO>
cd asistente-gastronomia

instalar dependencias
pip install -r requirements.txt

Para iniciar la app y ver la interfaz grafica
streamlit run src/app.py

Automaticamente esta pestaña de abrira en tu navegador
http://localhost:8501

Uso del Chat y Funcionalidades
Consulta de Recetas: Redacta solicitudes gastronómicas de platos tradicionales venezolanos (ej: ¿Cómo preparar una Arepa Reina Pepiada?). El sistema extraerá de forma semántica la información del recetario local indexado en FAISS.

Información Cultural: El agente recurrirá al protocolo MCP con Wikipedia en tiempo real ante dudas históricas de los platos.

Descarga de PDF (Skill): En la interfaz interactiva, utiliza el botón de exportación para generar dinámicamente un documento PDF limpio y listo para imprimir con la receta generada.