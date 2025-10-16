# app.py
# Versión: Fake Auto Grader (Simulada - n8n /examenes-calificar)
# Funciona 100% online en Streamlit Cloud sin OCR ni APIs externas.

import streamlit as st
import pandas as pd
import numpy as np
import io
import time
import hashlib
import random
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile

# ---------------- CONFIGURACIÓN PÁGINA ----------------
st.set_page_config(page_title="Calificador Automático (Fake)", layout="wide")
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.6rem;
        border-radius: 10px;
        text-align: left;
        color: white;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg,#667eea,#764ba2);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem;
    }
    .processing-box {
        background: linear-gradient(135deg,#667eea,#764ba2);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h2>📝 Sistema de Calificación Automática</h2><div>Interfaz conectada con flujo n8n: <code>/examenes-calificar</code></div></div>', unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if 'results' not in st.session_state:
    st.session_state['results'] = []
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'key' not in st.session_state:
    st.session_state['key'] = {}

# ---------------- FUNCIONES ----------------
def parse_key_string(key_str):
    """Parse key like '1:a, 2:d, 3:e, 4:v, 5:f' -> {1:'a',...}"""
    import re
    keys = {}
    if not key_str:
        return keys
    parts = re.split(r'[;,]+', key_str)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'^(\d+)\s*[:\-\)]?\s*([a-evfv])$', p, re.IGNORECASE)
        if m:
            keys[int(m.group(1))] = m.group(2).lower()
    return keys

def deterministic_rng(filename, key_string, salt="v1"):
    """Return random.Random seeded deterministically from filename+key_string+salt"""
    h = hashlib.sha256((filename + "|" + key_string + "|" + salt).encode('utf-8')).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)

def fake_grade_for_file(filename, answer_key):
    """Simula una calificación verosímil"""
    key_str = ",".join(f"{k}:{v}" for k,v in sorted(answer_key.items()))
    rng = deterministic_rng(filename, key_str)
    total = len(answer_key) if answer_key else rng.randint(8, 12)
    base = rng.normalvariate(0.55, 0.18)
    base = max(0.0, min(1.0, base))
    correct_count = int(round(base * total))
    if rng.random() < 0.15:
        correct_count = max(0, min(total, correct_count + rng.choice([-1,1])))
    score = round((correct_count / total) * 20.0, 2) if total > 0 else 0.0
    return {
        'nombre_pdf': filename,
        'correctas': correct_count,
        'incorrectas': total - correct_count,
        'total': total,
        'nota': score
    }

def generate_report_pdf(results_list, course_name, course_code, key, min_pass=14.0):
    """Genera reporte PDF con tabla + histograma"""
    notas = [r['nota'] for r in results_list] if results_list else [0]
    fig, ax = plt.subplots(figsize=(6,3))
    ax.hist(notas, bins=10)
    ax.set_xlabel('Nota (0-20)')
    ax.set_ylabel('Cantidad')
    ax.set_title('Distribución de Notas')
    tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmpimg.name, bbox_inches='tight')
    plt.close(fig)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte de Calificación Automática", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Curso: {course_name}    Código: {course_code}", ln=True)
    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(6)

    # Tabla
    pdf.set_font("Arial", "B", 11)
    pdf.cell(80, 8, "PDF", 1)
    pdf.cell(25, 8, "Nota", 1)
    pdf.cell(25, 8, "Correctas", 1)
    pdf.cell(25, 8, "Incorrectas", 1)
    pdf.cell(25, 8, "Total", 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for r in results_list:
        name = r['nombre_pdf'][:45]
        pdf.cell(80, 8, name, 1)
        pdf.cell(25, 8, f"{r['nota']:.2f}", 1)
        pdf.cell(25, 8, str(r['correctas']), 1)
        pdf.cell(25, 8, str(r['incorrectas']), 1)
        pdf.cell(25, 8, str(r['total']), 1)
        pdf.ln()

    pdf.ln(6)
    df = pd.DataFrame(results_list)
    promedio = round(df['nota'].mean(),2)
    mayor = round(df['nota'].max(),2)
    menor = round(df['nota'].min(),2)
    aprobados = len(df[df['nota'] >= min_pass])
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Resumen de Estadísticas", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Promedio general: {promedio}", ln=True)
    pdf.cell(0, 6, f"Aprobados: {aprobados} / {len(df)}", ln=True)
    pdf.cell(0, 6, f"Mayor nota: {mayor}", ln=True)
    pdf.cell(0, 6, f"Menor nota: {menor}", ln=True)
    pdf.ln(4)
    pdf.image(tmpimg.name, x=20, w=170)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Notas simuladas para demostración. Flujo n8n: /examenes-calificar")
    return io.BytesIO(pdf.output(dest='S').encode('latin-1'))

# ---------------- INTERFAZ ----------------
st.sidebar.markdown("### ⚙️ Conexión")
st.sidebar.success("✅ Conectado al flujo n8n: `/examenes-calificar`")
st.sidebar.markdown("---")
st.sidebar.info("Escala 0-20 — Nota mínima aprobatoria: 14")

st.header("1️⃣ Datos del Curso")
c1, c2 = st.columns(2)
course_name = c1.text_input("Nombre del curso", value="Curso X")
course_code = c2.text_input("Código del curso", value="C-001")

st.subheader("🔑 Clave de respuestas")
st.markdown("Formato: `1:a, 2:d, 3:e, 4:v, 5:f`")
key_input = st.text_area("Ingresa la clave:", height=90, placeholder="Ej: 1:a, 2:b, 3:c, 4:v, 5:f")
if key_input:
    key = parse_key_string(key_input)
    st.session_state['key'] = key
    st.success(f"Clave cargada: {len(key)} preguntas")
else:
    key = st.session_state.get('key', {})

st.markdown("---")
st.header("2️⃣ Carga de PDFs")
uploaded = st.file_uploader("Sube hasta 30 PDFs", accept_multiple_files=True, type=['pdf'])
if uploaded:
    if len(uploaded) > 30:
        st.warning("Máximo 30 archivos permitidos.")
        uploaded = uploaded[:30]
    st.info(f"{len(uploaded)} archivos listos para analizar")

st.markdown("---")
st.header("3️⃣ Analizar (con n8n)")

if st.button("🚀 Analizar con n8n"):
    if not uploaded or not key or not course_name or not course_code:
        st.error("Completa todos los campos antes de analizar.")
    else:
        st.markdown('<div class="processing-box"><h4>📡 Enviando exámenes al servidor n8n...</h4><div>Flujo: <code>/examenes-calificar</code></div></div>', unsafe_allow_html=True)
        progress = st.progress(0)
        results = []
        total = len(uploaded)
        for i, f in enumerate(uploaded, start=1):
            time.sleep(0.5)
            res = fake_grade_for_file(f.name, key)
            results.append(res)
            progress.progress(i/total)
        st.session_state['results'] = results
        st.session_state['processed'] = True
        st.session_state['course_name'] = course_name
        st.session_state['course_code'] = course_code
        st.success("✅ Análisis completado exitosamente")
        st.balloons()

# ---------------- RESULTADOS ----------------
if st.session_state.get('processed'):
    st.markdown("---")
    st.header("4️⃣ Resultados Generales")
    df = pd.DataFrame(st.session_state['results'])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Promedio general", f"{df['nota'].mean():.2f}")
    aprob = len(df[df['nota']>=14])
    col2.metric("Aprobados", f"{aprob}")
    col3.metric("Desaprobados", f"{len(df)-aprob}")
    col4.metric("Total PDFs", f"{len(df)}")

    st.subheader("📋 Detalle por PDF")
    df_display = df[['nombre_pdf','correctas','incorrectas','nota']].copy()
    df_display['Estado'] = df_display['nota'].apply(lambda x: "Aprobado ✅" if x>=14 else "Desaprobado ❌")
    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")
    st.header("5️⃣ Exportar Reporte PDF")
    if st.button("📄 Generar Reporte PDF"):
        with st.spinner("Generando reporte..."):
            pdf_bytes = generate_report_pdf(st.session_state['results'], course_name, course_code, key)
            filename = f"reporte_{course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.download_button("⬇️ Descargar reporte PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<div style='text-align:center; color: #888;'>Sistema de Calificación Automática • Simulado • Flujo n8n: /examenes-calificar</div>", unsafe_allow_html=True)
