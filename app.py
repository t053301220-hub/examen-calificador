import streamlit as st
import pandas as pd
import random
import time
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import base64

# --- Configuración de la página ---
st.set_page_config(
    page_title="Simulador Calificador de Exámenes IA",
    layout="wide",
    page_icon="🧠"
)

# --- Encabezado ---
st.title("🧠 Calificador Automático de Exámenes (Simulación IA + n8n)")
st.markdown("""
Esta aplicación **simula** la corrección automática de exámenes escaneados 📄  
usando supuestamente *Google Gemini 1.5* y un flujo en **n8n (/examenes-calificar)**  
> ⚙️ Nota: Todo el procesamiento es **simulado**, sin conexión real a ningún servicio externo.
""")

# --- Sidebar: Datos del examen ---
st.sidebar.header("📝 Configuración del examen")
curso = st.sidebar.text_input("Nombre del curso", "Inteligencia Artificial")
codigo = st.sidebar.text_input("Código del curso", "IA101")
claves_input = st.sidebar.text_area(
    "Claves de respuestas (ejemplo: 1:a, 2:d, 3:e, 4:v, 5:f)",
    "1:a, 2:d, 3:e, 4:v, 5:f"
)

uploaded_pdfs = st.sidebar.file_uploader(
    "Subir exámenes en PDF (máx. 30)",
    type=["pdf"],
    accept_multiple_files=True
)

# --- Botón de simulación ---
if st.sidebar.button("🚀 Analizar en IA + n8n"):
    if not uploaded_pdfs:
        st.warning("Por favor, sube al menos un PDF antes de analizar.")
    else:
        # Simula el procesamiento
        with st.spinner("🔄 Enviando a flujo /examenes-calificar..."):
            time.sleep(2)
        st.success("✅ Procesamiento completado (simulado con éxito).")

        # --- Parsear número de preguntas ---
        try:
            total_preguntas = len([p for p in claves_input.split(",") if ":" in p])
        except:
            total_preguntas = 10  # fallback

        resultados = []
        for pdf in uploaded_pdfs:
            correctas = random.randint(int(total_preguntas * 0.3), total_preguntas)
            incorrectas = total_preguntas - correctas
            nota = round((correctas / total_preguntas) * 20, 2)

            resultados.append({
                "nombre_pdf": pdf.name,
                "correctas": correctas,
                "incorrectas": incorrectas,
                "nota": nota
            })

        df = pd.DataFrame(resultados)

        # --- Métricas globales ---
        promedio = df["nota"].mean()
        aprobados = len(df[df["nota"] >= 14])
        desaprobados = len(df[df["nota"] < 14])
        mayor = df["nota"].max()
        menor = df["nota"].min()

        # --- Mostrar resultados ---
        st.subheader("📊 Resultados simulados")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Promedio general", f"{promedio:.2f}")
        col2.metric("Aprobados", f"{aprobados}")
        col3.metric("Desaprobados", f"{desaprobados}")
        col4.metric("Mayor nota", f"{mayor:.2f}")
        col5.metric("Menor nota", f"{menor:.2f}")

        st.markdown("### 📄 Detalle por PDF")
        st.dataframe(df, use_container_width=True)

        # --- Gráfico ---
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df["nombre_pdf"], df["nota"])
        ax.set_title("Distribución de notas (simulada)")
        ax.set_ylabel("Nota (0-20)")
        ax.set_xticklabels(df["nombre_pdf"], rotation=45, ha="right")
        st.pyplot(fig)

        # --- Generar PDF del reporte ---
        st.markdown("### 📤 Exportar reporte PDF")

        def generar_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Reporte de Resultados - {curso}", 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Código del curso: {codigo}", 0, 1, 'C')
            pdf.cell(0, 10, "Simulado con IA + n8n", 0, 1, 'C')
            pdf.ln(10)

            # Tabla de resultados
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(80, 10, "Nombre del PDF", 1)
            pdf.cell(30, 10, "Correctas", 1)
            pdf.cell(30, 10, "Incorrectas", 1)
            pdf.cell(30, 10, "Nota", 1)
            pdf.ln()
            pdf.set_font("Arial", '', 12)

            for _, row in df.iterrows():
                pdf.cell(80, 10, row["nombre_pdf"][:25], 1)
                pdf.cell(30, 10, str(row["correctas"]), 1)
                pdf.cell(30, 10, str(row["incorrectas"]), 1)
                pdf.cell(30, 10, f"{row['nota']:.2f}", 1)
                pdf.ln()

            pdf.ln(8)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Resumen General", 0, 1)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"Promedio general: {promedio:.2f}", 0, 1)
            pdf.cell(0, 8, f"Aprobados: {aprobados}", 0, 1)
            pdf.cell(0, 8, f"Desaprobados: {desaprobados}", 0, 1)
            pdf.cell(0, 8, f"Mayor nota: {mayor:.2f}", 0, 1)
            pdf.cell(0, 8, f"Menor nota: {menor:.2f}", 0, 1)

            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            return pdf_output

        pdf_bytes = generar_pdf()
        b64 = base64.b64encode(pdf_bytes.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="Reporte_Resultados.pdf">📥 Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
