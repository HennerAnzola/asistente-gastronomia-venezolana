from fpdf import FPDF
import os

def generar_pdf_receta(nombre_receta, contenido):
    """Genera dinámicamente un PDF con la receta"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Receta: {nombre_receta}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    texto_limpio = contenido.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=texto_limpio)
    if not os.path.exists("data"):
        os.makedirs("data")
    file_path = f"data/receta_consultada.pdf"
    pdf.output(file_path)
    return file_path 