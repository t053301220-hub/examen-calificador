# app.py
"""
Simulación: Exam Auto Grader (FAKE analysis)
- Recibe clave en formato: 1:a, 2:d, 3:e, 4:v, 5:f
- Acepta hasta 30 PDFs (solo se usa el nombre del archivo)
- Simula análisis (aparenta usar Google Gemini 1.5 y n8n)
- Escala de notas 0-20, aprobatorio por defecto 14
- Genera reporte PDF con tabla y histograma
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import tempfile
import hashlib
import random
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import base64

st.set_page_config(page_title="Exam Auto Grader (SIMULADO)", layout="wide")
st.title("Exam Auto Grader — Simulación (fake)")

st.markdown("""
Esta aplicación **simula** el proceso de calificación desde PDFs.  
Recibe la **clave** de respuestas, acepta hasta **30 PDFs**, simula un análisis (aparenta usar *Google Gemini 1.5* y *n8n*) y genera un **reporte PDF** con notas y estadísticas.
""")

# ---------------------------
# Utilidades
# ---------------------------
def parse_key_string(key_str):
    """
    Parsea clave tipo: '1:a, 2:d, 3:e, 4:v, 5:f' -> {1:'a', 2:'d', ...}
    Acepta separadores , ; y algunos formatos simples.
    """
    import re
    keys = {}
    if not key_str:
        return keys
    parts = re.split(r"[;,]+", key_str)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"^(\d+)\s*[:\-\)]\s*([a-evfv])$", p, re.IGNORECASE)
        if not m:
            # intentar '1 a' o '1:a'
            m = re.match(r"^(\d+)\s+([a-evfv])$", p, re.IGNORECASE)
        if m:
            q = int(m.group(1))
            a = m.group(2).lower()
            if a in ('v','f'):
                a = a  # ya v/f
            keys[q] = a
    return keys

def deterministic_rng_from_string(s):
    """Crea un random.Random determinístico a partir de un string."""
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)

def generate_fake_result(filename, answer_key, extra_entropy=""):
    """
    Genera resultado simulado para un PDF:
    - correct_count: entero entre 0 y total preguntas
    - detected: diccionario con respuestas pseudoaleatorias
    - score: (correct/total)*20 rounded
    Determinístico con base en filename + answer_key + extra_entropy.
    """
    total_q = len(answer_key) if answer_key else 10  # si no hay clave asumimos 10 preguntas
    key_string = ",".join(f"{k}:{v}" for k,v in sorted(answer_key.items())) if answer_key else ""
    seed_str = f"{filename}||{key_string}||{extra_entropy}"
    rng = deterministic_rng_from_string(seed_str)

    # Simular cuántas correctas (distribución sesgada a favor de 40-80% para realismo)
    # Usamos mezcla: baseline uniforme + tendencia hacia la media 0.55
    baseline = rng.random()
    skew = 0.55
    frac_correct = (baseline + skew) / 2  # entre 0 and 1
    # añadir pequeña variación por archivo
    frac_correct = max(0.0, min(1.0, frac_correct + (rng.random() - 0.5) * 0.25))
    correct_count = int(round(frac_correct * total_q))
    if total_q == 0:
        score = 0.0
    else:
        score = round((correct_count / total_q) * 20.0, 2)

    # generar respuestas detectadas pseudoaleatorias (a-e or v/f depending on key)
    detected = {}
    opts_mcq = ['a','b','c','d','e']
    for q in range(1, total_q+1):
        if q in answer_key:
            expected = answer_key[q]
            # con cierta probabilidad (ej. 60%) asignar respuesta correcta, si no elegir otra
            if rng.random() < 0.6:
                detected[q] = expected
            else:
                # elegir aleatoria distinta
                if expected in ('v','f'):
                    detected[q] = rng.choice(['v','f'])
                else:
                    choices = [o for o in opts_mcq if o != expected]
                    detected[q] = rng.choice(choices)
        else:
            # si no hay clave, elegir al azar entre MCQ y VF
            if rng.random() < 0.2:
                detected[q] = rng.choice(['v','f'])
            else:
                detected[q] = rng.choice(opts_mcq)

    return {
        'filename': filename,
        'detected': detected,
        'correct_count': correct_count,
        'total': total_q,
        'score': score
    }

# ---------------------------
# UI: formulario para clave y archivos
# ---------------------------
with st.form("form_clave", clear_on_submit=False):
    col1, col2 = st.columns([3,1])
    with col1:
        course_name = st.text_input("Nombre del curso", value="Curso X")
        course_code = st.text_input("Código del curso", value="C-001")
        key_input = st.text_input("Clave (ej: 1:a, 2:d, 3:e, 4:v, 5:f)")
    with col2:
        st.write("Configuración")
        min_aprob = st.number_input("Nota mínima aprobatoria", value=14.0, step=0.5)
        st.write("Escala: 0 - 20")
    submitted = st.form_submit_button("Guardar clave")

answer_key = parse_key_string(key_input or "")
st.markdown("**Clave parseada:** " + (str(answer_key) if answer_key else "— (vacía)"))

uploaded_files = st.file_uploader("Sube hasta 30 archivos PDF (selección múltiple)", type=['pdf'], accept_multiple_files=True)
if uploaded_files and len(uploaded_files) > 30:
    st.warning("Has subido más de 30 archivos — solo se tomarán los primeros 30.")
    uploaded_files = uploaded_files[:30]

# ---------------------------
# Botón: Analizar en n8n (simulado)
# ---------------------------
st.markdown("---")
st.write("Simulación de análisis (aparenta estar conectada a n8n y Google Gemini 1.5)")

analyze_pressed = st.button("Analizar en n8n")  # el texto no indica que es simulado
results = []

if analyze_pressed:
    if not uploaded_files:
        st.warning("Sube al menos 1 PDF antes de analizar.")
    else:
        progress = st.progress(0)
        log = st.empty()
        total = len(uploaded_files)
        for i, up in enumerate(uploaded_files, start=1):
            filename = up.name
            # Simular tiempo/progreso
            log.text(f"Conectando a flujo n8n... procesando {filename} ({i}/{total}) — usando Google Gemini 1.5 (simulado)")
            # Generar resultado falso determinístico
            # Incluimos la hora de análisis parcial como entropy para que repetir el mismo análisis en corto tiempo NO cambie los valores.
            res = generate_fake_result(filename, answer_key, extra_entropy="v1")
            results.append(res)
            progress.progress(int(i/total*100))
        progress.progress(100)
        st.success("Análisis completado (simulado).")

# ---------------------------
# Mostrar resultados si existen
# ---------------------------
if results:
    df = pd.DataFrame([{
        'pdf': r['filename'],
        'nota': r['score'],
        'correctas': r['correct_count'],
        'total': r['total']
    } for r in results])
    st.subheader("Resultados individuales")
    st.dataframe(df.sort_values('nota', ascending=False))

    promedio = round(df['nota'].mean(),2)
    aprobados_df = df[df['nota'] >= min_aprob]
    desaprobados_df = df[df['nota'] < min_aprob]
    pct_aprob = round(len(aprobados_df)/len(df)*100,2) if len(df)>0 else 0.0
    mayor = round(df['nota'].max(),2)
    menor = round(df['nota'].min(),2)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Promedio general", promedio)
    c2.metric("Promedio aprobados", round(aprobados_df['nota'].mean(),2) if len(aprobados_df)>0 else 0)
    c3.metric("% Aprobados", f"{pct_aprob}%")
    c4.metric("Mayor / Menor", f"{mayor} / {menor}")

    # Histograma
    fig, ax = plt.subplots()
    ax.hist(df['nota'], bins=10)
    ax.set_xlabel("Nota (0-20)")
    ax.set_ylabel("Cantidad")
    ax.set_title("Distribución de notas (simulada)")
    st.pyplot(fig)

    # Detalle expandible con respuestas detectadas (simuladas)
    with st.expander("Ver respuestas detectadas (simuladas) por PDF"):
        for r in results:
            st.write(f"**{r['filename']}** — Nota: {r['score']} — Correctas: {r['correct_count']}/{r['total']}")
            st.write("Respuestas detectadas (simulado):", r['detected'])

    # ---------------------------
    # Generar reporte PDF
    # ---------------------------
    def create_report_pdf(results_list, course_name, course_code, min_aprob, histogram_fig):
        """
        Genera un PDF con FPDF:
        - Título, curso, fecha
        - Tabla de resultados
        - Estadísticas
        - Inserta el histograma (pasado como figura matplotlib)
        """
        # Guardar histograma a imagen temporal
        tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        histogram_fig.savefig(tmpimg.name, bbox_inches='tight')
        tmpimg.close()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Exam Auto Grader - Reporte (SIMULADO)", ln=True, align="C")
        pdf.ln(4)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Curso: {course_name}    Codigo: {course_code}    Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(6)

        # Tabla encabezado
        pdf.set_font("Arial", "B", 11)
        pdf.cell(80, 8, "PDF", border=1)
        pdf.cell(30, 8, "Nota", border=1)
        pdf.cell(30, 8, "Correctas", border=1)
        pdf.cell(30, 8, "Total", border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for r in results_list:
            name = r['filename'][:45]
            pdf.cell(80, 8, name, border=1)
            pdf.cell(30, 8, str(r['score']), border=1)
            pdf.cell(30, 8, str(r['correct_count']), border=1)
            pdf.cell(30, 8, str(r['total']), border=1)
            pdf.ln()

        pdf.ln(6)
        # Estadísticas
        notas = [r['score'] for r in results_list]
        promedio = round(float(np.mean(notas)),2)
        mayor = round(float(np.max(notas)),2)
        menor = round(float(np.min(notas)),2)
        aprobados = sum(1 for n in notas if n >= min_aprob)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, "Resumen de estadísticas", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Promedio general: {promedio}", ln=True)
        pdf.cell(0, 6, f"Mayor nota: {mayor}", ln=True)
        pdf.cell(0, 6, f"Menor nota: {menor}", ln=True)
        pdf.cell(0, 6, f"Aprobados: {aprobados} / {len(notas)}", ln=True)
        pdf.ln(8)

        # Insertar histograma
        try:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 6, "Histograma de notas (simulado)", ln=True)
            pdf.image(tmpimg.name, x=None, y=None, w=170)
        except Exception as e:
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, f"(No se pudo insertar imagen: {e})", ln=True)

        # Pie de página / nota
        pdf.ln(6)
        pdf.set_font("Arial", "I", 8)
        pdf.multi_cell(0, 5, "Este reporte fue generado por la aplicación 'Exam Auto Grader' — análisis SIMULADO (no se analizó el contenido del PDF).")
        # Guardar a archivo temporal
        tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmpf.name)
        return tmpf.name

    # Botón para generar y descargar reporte
    report_path = create_report_pdf(results, course_name, course_code, min_aprob, fig)
    with open(report_path, "rb") as f:
        bytes_pdf = f.read()
    b64 = base64.b64encode(bytes_pdf).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="reporte_{course_code}.pdf">⬇️ Descargar reporte PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

else:
    st.info("No se han generado resultados. Suba PDFs y presione 'Analizar en n8n'.")

# ---------------------------
# Footer: instrucciones y requirements
# ---------------------------
st.markdown("---")
st.header("Instrucciones para despliegue (Streamlit Cloud)")
st.markdown("""
1. Crea un repositorio en GitHub con este archivo `app.py`.  
2. Crea `requirements.txt` (sugerido abajo).  
3. Conecta tu repo a Streamlit Cloud y despliega la app.  
""")
st.code("""
# requirements.txt (ejemplo mínimo)
streamlit
fpdf
pandas
matplotlib
""", language="")

st.markdown("**Nota:** Esta versión genera análisis *SIMULADOS* (fakes). No realiza OCR ni inspecciona el contenido de los PDFs; solo usa el nombre de archivo para generar resultados reproducibles.")
