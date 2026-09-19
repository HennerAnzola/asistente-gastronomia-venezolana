import os
import re
from fpdf import FPDF

def _limpiar_para_pdf(texto: str) -> str:
    """Elimina emojis y reemplaza caracteres incompatibles con fuentes estándar de PDF."""
    if not texto:
        return ""
    
    # Reemplazos de caracteres tipográficos comunes
    reemplazos = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "*", "…": "...", "🇻🇪": "", "🍲": "", "👨‍🍳": "", 
        "📋": "", "💡": "", "✈️": "", "📚": "", "🧀": "", "🥩": "", "🫓": ""
    }
    for orig, dest in reemplazos.items():
        texto = texto.replace(orig, dest)
        
    # Filtrar cualquier caracter fuera del rango Latin-1 (incluyendo otros emojis)
    return texto.encode("latin-1", "ignore").decode("latin-1")

def generar_pdf_receta(nombre_receta: str, contenido: str) -> str:
    """Genera dinámicamente un archivo PDF con el contenido estructurado de la receta."""
    pdf = FPDF()
    pdf.add_page()
    
    # Título principal
    pdf.set_font("Helvetica", "B", 16)
    titulo_limpio = _limpiar_para_pdf(f"Receta: {nombre_receta}")
    pdf.cell(0, 10, txt=titulo_limpio, ln=1, align="C")
    pdf.ln(6)
    
    # Contenido de la receta
    pdf.set_font("Helvetica", size=11)
    contenido_limpio = _limpiar_para_pdf(contenido)
    pdf.multi_cell(0, 7, txt=contenido_limpio)
    
    # Asegurar directorio de salida
    os.makedirs("data", exist_ok=True)
    ruta_archivo = os.path.join("data", "receta_consultada.pdf")
    pdf.output(ruta_archivo)
    
    return ruta_archivo
