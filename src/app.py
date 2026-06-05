import streamlit as st
import os
from agents import procesar_pregunta
from skill_receta import generar_pdf_receta

st.set_page_config(page_title="Asistente Gastronómico Vzla", page_icon="🍲")
st.title("🍲 Asistente IA: Gastronomía Venezolana")
st.markdown("Pregunta sobre recetas, historia o tips de cocina criolla venezolana.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Cómo se hace la arepa Reina Pepiada?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando agentes y RAG..."):
            respuesta = procesar_pregunta(prompt)
            st.markdown(respuesta)

    if respuesta and "Error" not in respuesta:
        try:
            path_pdf = generar_pdf_receta("Receta Consultada", respuesta)
            if os.path.exists(path_pdf):
                with open(path_pdf, "rb") as file:
                    st.download_button(
                        label="📄 Descargar Receta en PDF",
                        data=file,
                        file_name="receta_venezolana.pdf",
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f"No se pudo generar el PDF: {e}")

    st.session_state.messages.append({"role": "assistant", "content": respuesta})