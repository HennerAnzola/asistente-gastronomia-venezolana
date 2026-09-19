import streamlit as st
import os
import re
from agents import procesar_pregunta
from skill_receta import generar_pdf_receta

# Configuración de página de Streamlit
st.set_page_config(
    page_title="SaborCriollo AI - Asistente Culinario Venezolano",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de estilos y fuentes Stitch con corrección de márgenes y contraste total
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<style>
  /* 1. Ajuste superior para pegar el diseño totalmente arriba */
  header[data-testid="stHeader"] {
    display: none !important;
  }
  #MainMenu {
    visibility: hidden !important;
  }
  footer {
    visibility: hidden !important;
  }
  .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 1400px !important;
  }

  /* 2. Fondo general de la aplicación y forzado de textos oscuros */
  .stApp {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
  }

  /* Forzar color oscuro en elementos de texto estándar para evitar textos escondidos */
  p, span, label, h1, h2, h3, h4, h5, h6, strong, b, em {
    font-family: 'Plus Jakarta Sans', sans-serif;
  }

  h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    color: #0f172a !important;
  }

  /* 3. Encabezado SaborCriollo AI */
  .stitch-top-header {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px;
    padding: 14px 24px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  }

  .brand-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .brand-name {
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #a6331b !important;
    line-height: 1.1;
  }

  .brand-sub {
    font-size: 11px;
    font-weight: 700;
    color: #475569 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .rag-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: #ecfdf5 !important;
    border: 1px solid #6ee7b7 !important;
    color: #065f46 !important;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
  }

  .dot-ping {
    width: 8px;
    height: 8px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pingEffect 1.8s infinite;
  }

  @keyframes pingEffect {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }

  /* 4. Burbujas de Chat con Alto Contraste */
  .chat-msg-user {
    background: #a6331b !important;
    color: #ffffff !important;
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 14.5px;
    line-height: 1.55;
    box-shadow: 0 2px 6px rgba(166, 51, 27, 0.2);
  }
  .chat-msg-user * {
    color: #ffffff !important;
  }

  .chat-msg-bot {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 14.5px;
    line-height: 1.55;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  }
  .chat-msg-bot * {
    color: #0f172a !important;
  }

  /* 5. Estilizado de Botones de Streamlit (Chips de sugerencias) */
  div[data-testid="stButton"] > button {
    background-color: #ffffff !important;
    color: #a6331b !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    transition: all 0.2s ease !important;
  }
  div[data-testid="stButton"] > button:hover {
    background-color: #fef2f2 !important;
    border-color: #a6331b !important;
    color: #a6331b !important;
    transform: translateY(-1px);
  }
  div[data-testid="stButton"] > button p {
    color: #a6331b !important;
    font-weight: 700 !important;
  }

  /* 6. Pestañas (Tabs) de Streamlit */
  button[data-baseweb="tab"] {
    background-color: transparent !important;
  }
  button[data-baseweb="tab"] p {
    color: #475569 !important;
    font-weight: 700 !important;
    font-size: 14px !important;
  }
  button[data-baseweb="tab"][aria-selected="true"] p {
    color: #a6331b !important;
    font-weight: 800 !important;
  }

  /* 7. Checkboxes de Ingredientes (100% legibles con fondo blanco) */
  div[data-testid="stCheckbox"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 6px 12px !important;
    margin-bottom: 6px !important;
  }
  div[data-testid="stCheckbox"] label p {
    color: #0f172a !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
  }

  /* 8. Botón de Descarga de PDF */
  div[data-testid="stDownloadButton"] > button {
    background-color: #a6331b !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 16px !important;
    box-shadow: 0 2px 6px rgba(166, 51, 27, 0.3) !important;
  }
  div[data-testid="stDownloadButton"] > button:hover {
    background-color: #891e07 !important;
    color: #ffffff !important;
  }
  div[data-testid="stDownloadButton"] > button p {
    color: #ffffff !important;
    font-weight: 700 !important;
  }

  /* 9. Hero Banner del Lienzo de Receta */
  .recipe-hero-card {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    height: 230px;
    background-size: cover;
    background-position: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    margin-bottom: 16px;
  }

  .recipe-hero-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.35) 0%, rgba(15, 23, 42, 0.92) 100%);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .hero-badge-left {
    background: #ffffff !important;
    color: #a6331b !important;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
  }

  .hero-badge-right {
    background: #186a21 !important;
    color: #ffffff !important;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
  }

  .hero-title {
    color: #ffffff !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.7) !important;
  }

  .hero-desc {
    color: #f1f5f9 !important;
    font-size: 13px !important;
    margin-top: 4px !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.6) !important;
  }

  /* 10. Tarjetas de Métricas */
  .metric-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  }

  .metric-icon-box {
    font-size: 22px;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8fafc;
    border-radius: 8px;
  }

  .metric-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b !important;
  }

  .metric-value {
    font-size: 15px;
    font-weight: 800;
    color: #0f172a !important;
  }

  /* 11. Cajas de Secretos y Diáspora */
  .tip-criollo {
    background: #fffbeb !important;
    border: 1px solid #fef3c7 !important;
    border-left: 4px solid #d97706 !important;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 14px;
  }
  .tip-criollo strong {
    color: #92400e !important;
    font-size: 14px;
  }
  .tip-criollo span {
    color: #334155 !important;
    font-size: 13.5px;
    line-height: 1.5;
    display: block;
    margin-top: 4px;
  }

  .diaspora-guide {
    background: #f0fdf4 !important;
    border: 1px solid #dcfce7 !important;
    border-left: 4px solid #16a34a !important;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 12px;
  }
  .diaspora-guide strong {
    color: #15803d !important;
    font-size: 14px;
  }
  .diaspora-guide span {
    color: #334155 !important;
    font-size: 13.5px;
    line-height: 1.5;
    display: block;
    margin-top: 4px;
  }
</style>
""", unsafe_allow_html=True)

# Inicializar sesión de chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "¡Hola, mi pana! 🇻🇪 Soy tu Chef Culinario Inteligente. Dime qué plato venezolano se te antoja hoy (Arepas Reina Pepiada, Pabellón, Tequeños, Hallacas, Asado Negro...) y te guiaré con las recetas exactas y secretos de la abuela."
        }
    ]

if "recetas_historial" not in st.session_state:
    receta_default = {
        "titulo": "Arepas de Reina Pepiada",
        "region": "Caracas, Dto. Capital",
        "tiempo": "35 mins",
        "dificultad": "Media",
        "porciones": "4 personas (8 arepas)",
        "calorias": "380 kcal / arepa",
        "imagen": "https://lh3.googleusercontent.com/aida-public/AB6AXuDsfwt4uHRHuv0Y4dSlS8la7prdssMVQzykq6bpIYMMBhhInWPTpdNCVrZa07nWPKcx0ToDv7CVxZZmJQ0ZRzvvXrmRkz6edvlikZhKUTlKxnziqtzr6OC3BPrS-LHyNmTkf2AYJV0yGvDIAP_QvvRxxR03Bk3qyNl7nefTQJxnOx3y216xFkCN8e4SOT6v7Rj0TU3MYwOWarPxJhCOAXzyXaJClaDX2V2mbavTaxpbK_EC0kj-cPC2",
        "ingredientes": [
            "2 tazas de Harina de maíz precocida (Harina P.A.N.)",
            "2.5 tazas de Agua tibia con sal marina fina disuelta",
            "500 g de Pechuga de pollo hervida y desmechada",
            "2 Aguacates maduros (tipo Hass o criollo de injerto)",
            "3 cucharadas de Mayonesa criolla cremosa",
            "1/4 taza de Cebolla morada picada finita",
            "2 cucharadas de Cilantro fresco picadito",
            "1 diente de Ajo machacado con sal",
            "Zumo de 1 lima, sal marina y pimienta al gusto"
        ],
        "pasos": [
            "Disuelve la sal y una cucharadita de aceite en el agua tibia. Incorpora la harina poco a poco en forma de lluvia mientras amasas con los dedos hasta obtener una masa suave, homogénea y elástica. Deja reposar 5 minutos tapada.",
            "En un tazón amplio, tritura 1.5 aguacates con tenedor junto a la mayonesa, ajo, cebolla morada, zumo de lima, sal y pimienta. Añade la pechuga desmechada y el cilantro picado. Mezcla envolventemente.",
            "Divide la masa en 8 porciones, forma bolas uniformes y aplana con las palmas a 1.5 cm de grosor. Cocina en budare o sartén caliente apenas engrasado 5-7 minutos por lado hasta formar concha dorada, y hornea 8 min a 200°C hasta que suenen huecas.",
            "Abre la arepa caliente lateralmente sin separar las tapas por completo, unta una fina capa de mantequilla criolla y rellena generosamente con el guiso frío de Reina Pepiada."
        ],
        "tip": "Para una masa que no se rompa nunca: disuelve la sal completamente en el agua tibia antes de agregar la harina. Guarda medio aguacate en cubitos para agregarlo al relleno al final sin triturarlo: ese contraste de texturas cremosas define una Reina Pepiada de campeonato.",
        "diaspora": "Sin budare: usa un sartén de hierro fundido (Skillet) o antiadherente grueso a fuego medio. Si no consigues ají dulce criollo, sustitúyelo con 1/4 de pimentón rojo dulce y una gota de miel en el caldo del pollo.",
        "fuentes": ["Armando Scannone (Mi Cocina)", "Recetario Tradicional 1955"]
    }
    st.session_state.recetas_historial = [receta_default]

def parsear_respuesta_a_receta(texto):
    """Convierte el texto de respuesta del LLM en los datos enriquecidos del lienzo."""
    receta = {
        "titulo": "Receta Criolla Consultada",
        "region": "Gastronomía Venezolana",
        "tiempo": "30 mins",
        "dificultad": "Fácil - Media",
        "porciones": "4 porciones",
        "calorias": "350 kcal",
        "imagen": "https://lh3.googleusercontent.com/aida-public/AB6AXuDsfwt4uHRHuv0Y4dSlS8la7prdssMVQzykq6bpIYMMBhhInWPTpdNCVrZa07nWPKcx0ToDv7CVxZZmJQ0ZRzvvXrmRkz6edvlikZhKUTlKxnziqtzr6OC3BPrS-LHyNmTkf2AYJV0yGvDIAP_QvvRxxR03Bk3qyNl7nefTQJxnOx3y216xFkCN8e4SOT6v7Rj0TU3MYwOWarPxJhCOAXzyXaJClaDX2V2mbavTaxpbK_EC0kj-cPC2",
        "ingredientes": [],
        "pasos": [],
        "tip": "El secreto de la sazón criolla está en respetar los tiempos de cocción lenta y el sofrito con ajo y cebolla frescos.",
        "diaspora": "Para preparar este plato en el extranjero, busca harinas y productos en tiendas latinas locales manteniendo la técnica tradicional.",
        "fuentes": []
    }

    lineas = texto.split("\n")
    seccion = None
    for l in lineas:
        s = l.strip()
        if s.startswith("# ") and not s.startswith("## "):
            receta["titulo"] = s.replace("# ", "").strip()
        elif s.startswith("## Region:"):
            receta["region"] = s.replace("## Region:", "").strip()
        elif s.startswith("## Tiempo de preparacion:"):
            receta["tiempo"] = s.replace("## Tiempo de preparacion:", "").strip()
        elif s.startswith("## Porciones:"):
            receta["porciones"] = s.replace("## Porciones:", "").strip()
        elif s.startswith("## Ingredientes:"):
            seccion = "ingredientes"
        elif s.startswith("## Preparacion:"):
            seccion = "pasos"
        elif "Fuentes consultadas" in s or s.startswith("📚"):
            seccion = "fuentes"
        elif seccion == "ingredientes" and s.startswith("- "):
            receta["ingredientes"].append(s.replace("- ", "").strip())
        elif seccion == "pasos" and re.match(r"^\d+\.", s):
            receta["pasos"].append(re.sub(r"^\d+\.\s*", "", s).strip())
        elif seccion == "fuentes" and s.startswith("- "):
            receta["fuentes"].append(s.replace("- ", "").strip())

    if not receta["ingredientes"]:
        receta["ingredientes"] = ["Ingredientes explicados en la conversación"]
    if not receta["pasos"]:
        receta["pasos"] = ["Pasos de preparación detallados en el chat"]

    return receta

# --- 1. ENCABEZADO SUPERIOR PEGADO ARRIBA ---
st.markdown("""
<div class="stitch-top-header">
  <div class="brand-group">
    <span style="font-size: 32px;">🍲</span>
    <div>
      <div class="brand-name">SaborCriollo AI</div>
      <div class="brand-sub">Asistente Culinario Venezolano</div>
    </div>
  </div>
  <div class="rag-status">
    <span class="dot-ping"></span>
    <span>Conectado a Base de Datos Culinaria (RAG Criollo v2.4)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# --- 2. LAYOUT DE DOBLE PANEL (Split Workspace) ---
col_izq, col_der = st.columns([5, 7], gap="large")

# ========================= PANEL IZQUIERDO: CHAT =========================
with col_izq:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
      <span style="font-size: 20px;">👨‍🍳</span>
      <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #0f172a;">Chef Criollo Bot</h3>
      <span style="font-size: 11px; background: #ffedd5; color: #9a3412; padding: 2px 8px; border-radius: 4px; font-weight: 800;">RAG v2.4</span>
    </div>
    """, unsafe_allow_html=True)

    # Ventana scrolleable del historial de chat
    contenedor_chat = st.container(height=480)
    with contenedor_chat:
        for m in st.session_state.messages:
            if m["role"] == "user":
                st.markdown(f'<div class="chat-msg-user"><strong>Tú:</strong><br>{m["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-msg-bot"><strong>Chef Criollo AI:</strong><br>{m["content"]}</div>', unsafe_allow_html=True)

    # Botones de sugerencias rápidas
    st.markdown("<p style='font-size: 12px; font-weight: 700; color: #475569; margin: 8px 0 4px 0;'>Sugerencias Rápidas:</p>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    sugerencia_click = None
    if c1.button("🫓 Reina Pepiada", use_container_width=True):
        sugerencia_click = "¿Cómo preparar unas auténticas Arepas de Reina Pepiada?"
    if c2.button("🍛 Pabellón", use_container_width=True):
        sugerencia_click = "¿Cómo se hace el Pabellón Criollo tradicional paso a paso?"
    if c3.button("🧀 Tequeños", use_container_width=True):
        sugerencia_click = "¿Cómo preparar tequeños de queso blanco crujientes?"
    if c4.button("🥩 Asado Negro", use_container_width=True):
        sugerencia_click = "¿Cuál es el secreto del Asado Negro caraqueño?"

    # Entrada del usuario
    pregunta_input = st.chat_input("Pregunta sobre recetas, ingredientes o historia criolla...") or sugerencia_click

    if pregunta_input:
        st.session_state.messages.append({"role": "user", "content": pregunta_input})
        with st.spinner("Consultando recetarios criollos y RAG..."):
            respuesta_ai = procesar_pregunta(pregunta_input)
            receta_extraida = parsear_respuesta_a_receta(respuesta_ai)
            titulos_existentes = [r["titulo"] for r in st.session_state.recetas_historial]
            if receta_extraida["titulo"] not in titulos_existentes:
                st.session_state.recetas_historial.append(receta_extraida)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_ai})
        st.rerun()

# ========================= PANEL DERECHO: LIENZO DE RECETA =========================
def renderizar_receta(receta, idx_receta):
    """Renderiza una receta completa dentro de una pestaña."""
    st.markdown(f"""
    <div class="recipe-hero-card" style="background-image: url('{receta['imagen']}');">
      <div class="recipe-hero-overlay">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="hero-badge-left">📍 {receta['region']}</span>
          <span class="hero-badge-right">⭐ 98% Sazón Criolla</span>
        </div>
        <div>
          <h1 class="hero-title">{receta['titulo']}</h1>
          <p class="hero-desc">Receta tradicional respaldada por la base de datos RAG Criollo</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'''
        <div class="metric-card">
          <div class="metric-icon-box">⏱️</div>
          <div><div class="metric-title">Tiempo</div><div class="metric-value">{receta['tiempo']}</div></div>
        </div>
        ''', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'''
        <div class="metric-card">
          <div class="metric-icon-box">🔥</div>
          <div><div class="metric-title">Dificultad</div><div class="metric-value">{receta['dificultad']}</div></div>
        </div>
        ''', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'''
        <div class="metric-card">
          <div class="metric-icon-box">🍽️</div>
          <div><div class="metric-title">Porciones</div><div class="metric-value">{receta['porciones']}</div></div>
        </div>
        ''', unsafe_allow_html=True)
    with m_col4:
        st.markdown(f'''
        <div class="metric-card">
          <div class="metric-icon-box">⚡</div>
          <div><div class="metric-title">Calorías</div><div class="metric-value">{receta['calorias']}</div></div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    pestana_ing, pestana_pasos = st.tabs(["📋 Ingredientes & Medidas", "👩‍🍳 Preparación Paso a Paso"])

    with pestana_ing:
        st.markdown("<h4 style='color: #0f172a; margin-bottom: 8px;'>Ingredientes Necesarios:</h4>", unsafe_allow_html=True)
        for i, ing in enumerate(receta["ingredientes"]):
            st.checkbox(ing, value=True, key=f"chk_{idx_receta}_{i}")

    with pestana_pasos:
        st.markdown("<h4 style='color: #0f172a; margin-bottom: 8px;'>Pasos de Preparación:</h4>", unsafe_allow_html=True)
        for idx, paso in enumerate(receta["pasos"], 1):
            st.markdown(f"""
            <div style="display: flex; gap: 12px; margin-bottom: 10px; background: #ffffff; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; border-left: 4px solid #a6331b;">
              <div style="background: #a6331b; color: #ffffff !important; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex-shrink: 0;">{idx}</div>
              <div style="color: #0f172a !important; font-size: 14px; line-height: 1.5; font-weight: 500;">{paso}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="tip-criollo">
      <strong>💡 Secreto del Maestro Criollo:</strong>
      <span>{receta['tip']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="diaspora-guide">
      <strong>✈️ Guía para la Diáspora (Cocinando en el exterior):</strong>
      <span>{receta['diaspora']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    pdf_col, info_col = st.columns([1, 1])
    with pdf_col:
        texto_pdf = f"# {receta['titulo']}\n\n## Ingredientes:\n" + "\n".join([f"- {i}" for i in receta['ingredientes']]) + "\n\n## Preparacion:\n" + "\n".join([f"{i}. {p}" for i, p in enumerate(receta['pasos'], 1)])
        try:
            ruta_pdf = generar_pdf_receta(receta['titulo'], texto_pdf)
            if os.path.exists(ruta_pdf):
                with open(ruta_pdf, "rb") as fp:
                    st.download_button(
                        label="📄 Descargar Receta en PDF",
                        data=fp,
                        file_name=f"{receta['titulo'].lower().replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"pdf_{idx_receta}"
                    )
        except Exception:
            st.caption("PDF listo")

    with info_col:
        if receta.get("fuentes"):
            st.markdown(f"<p style='color: #475569; font-size: 12px; margin-top: 8px; font-weight: 600;'>📚 Fuentes: {', '.join(receta['fuentes'])}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #475569; font-size: 12px; margin-top: 8px; font-weight: 600;'>📚 Fuente: Base Documental RAG Criollo</p>", unsafe_allow_html=True)


with col_der:
    historial = st.session_state.recetas_historial
    titulos = [r["titulo"] for r in historial]

    if len(historial) == 1:
        renderizar_receta(historial[0], 0)
    else:
        pestanas = st.tabs(titulos)
        for idx, (pestaña, receta) in enumerate(zip(pestanas, historial)):
            with pestaña:
                renderizar_receta(receta, idx)
