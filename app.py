import streamlit as st
import pandas as pd
import random
import time
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

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
usando supuestamente *Google Gemini 1.5* y un flujo en **n8n (/examenes-calificar)**.  
> ⚙️ Todo el procesamiento mostrado es **ficticio pero funcional**, sin conexión real.
""")

# --- Sidebar ---
st.sidebar.header("🧾 Configuración del examen")
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

# --- Simulación ---
if st.sidebar.button("🚀 Analizar con IA + n8n"):
    if not uploaded_pdfs:
        st.warning("Por favor, sube al menos un PDF antes de analizar.")
    else:
        total_pdfs = len(uploaded_pdfs)
        total_preguntas = len([p for p in claves_input.split(",") if ":" in p])

        st.subheader("🔄 Simulando conexión con n8n...")
        progress = st.progress(0)
        status_box = st.empty()

        resultados = []
        for i, pdf in enumerate(uploaded_pdfs, start=1):
            # Simular tiempo de análisis IA
            status_box.info(f"Analizando `{pdf.name}` ({i}/{total_pdfs}) con Gemini 1.5...")
            time.sleep(random.uniform(0.8, 1.5))
            progress.progress(i / total_pdfs)

            # Generar resultados coherentes (media centrada)
            correctas = int(random.gauss(mu=total_preguntas * 0.7, sigma=1.2))
            correctas = min(max(correctas, 0), total_preguntas)
            incorrectas = total_preguntas - correctas
            nota = round((correctas / total_preguntas) * 20, 2)

            resultados.append({
                "nombre_pdf": pdf.name,
                "correctas": correctas,
                "incorrectas": incorrectas,
                "nota": nota
            })

        status_box.success("✅ Análisis completado con éxito.")
        progress.empty()

        # Falsa respuesta de backend n8n
        st.code(
            """{
  "status": "ok",
  "processed": %d,
  "engine": "Gemini 1.5",
  "webhook": "/examenes-calificar"
}""" % total_pdfs, language="json"
        )

        # --- DataFrame final ---
        df = pd.DataFrame(resultados)
        promedio = df["nota"].mean()
        aprobados = len(df[df["nota"] >= 14])
        desaprobados = len(df[df["nota"] < 14])
        mayor = df["nota"].max()
        menor = df["nota"].min()

        # --- Mostrar métricas ---
        st.subheader("📊 Resultados Simulados")
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
        ax.bar(df["nombre_pdf"], df["nota"], color="#4B9CD3")
        ax.set_title("Distribución de notas (simulada con IA)", fontsize=12)
        ax.set_ylabel("Nota (0-20)")
        ax.set_ylim(0, 20)
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

        # --- Generar PDF del reporte ---
        st.markdown("### 📤 Exportar reporte PDF")

        def generar_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Reporte de Resultados - {curso}", 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Código: {codigo}", 0, 1, 'C')
            pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'C')
            pdf.cell(0, 10, "Motor: Gemini 1.5 (Simulado)", 0, 1, 'C')
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
