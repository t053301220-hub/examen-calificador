# app.py
# Versión: Fake Auto Grader (simula n8n + IA, NO usa OCR ni APIs externas)
# Requisitos (añadir a requirements.txt): streamlit, pandas, matplotlib, fpdf, pillow
# Ejemplo requirements.txt:
# streamlit
# pandas
# matplotlib
# fpdf
# pillow

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
from PIL import Image

# ---------------- Page config & CSS ----------------
st.set_page_config(page_title="Sistema de Calificación Automática (Fake)", layout="wide")
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

st.markdown('<div class="main-header"><h2>📝 Sistema de Calificación Automática</h2><div>Interfaz integrada con flujo n8n: <code>/examenes-calificar</code></div></div>', unsafe_allow_html=True)

# ---------------- Session state initialization ----------------
if 'results' not in st.session_state:
    st.session_state['results'] = []
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'key' not in st.session_state:
    st.session_state['key'] = {}

# ---------------- Utilities ----------------
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
    """
    Deterministically generate a plausible result for `filename` given answer_key dict.
    Returns dict with filename, detected (simulated), correct_count, total, score (0-20).
    """
    key_str = ",".join(f"{k}:{v}" for k,v in sorted(answer_key.items()))
    rng = deterministic_rng(filename, key_str)
    total = len(answer_key) if answer_key else rng.randint(8, 12)
    # simulate a student's correctness proportion (centered around 0.55 with variability)
    base = rng.normalvariate(0.55, 0.18)
    base = max(0.0, min(1.0, base))
    correct_count = int(round(base * total))
    # small random tweak per student
    if rng.random() < 0.15:
        correct_count = max(0, min(total, correct_count + rng.choice([-1,1])))
    score = round((correct_count / total) * 20.0, 2) if total > 0 else 0.0

    # generate pseudo 'detected' answers: match some of the key, miss others
    detected = {}
    options = ['a','b','c','d','e']
    for q in range(1, total+1):
        if q in answer_key:
            correct = answer_key[q]
            # chance to be correct proportional to base
            if rng.random() < base:
                detected[q] = correct
            else:
                if correct in ['v','f']:
                    detected[q] = rng.choice(['v','f'])
                else:
                    choices = [o for o in options if o != correct]
                    detected[q] = rng.choice(choices)
        else:
            # no key: random
            if rng.random() < 0.2:
                detected[q] = rng.choice(['v','f'])
            else:
                detected[q] = rng.choice(options)
    return {
        'nombre_pdf': filename,
        'detected': detected,
        'correctas': correct_count,
        'total': total,
        'nota': score
    }

def generate_report_pdf(results_list, course_name, course_code, key, min_pass=14.0):
    """Generate PDF report with table and histogram, return BytesIO"""
    # create histogram image
    notas = [r['nota'] for r in results_list] if results_list else [0]
    fig, ax = plt.subplots(figsize=(6,3))
    ax.hist(notas, bins=10)
    ax.set_xlabel('Nota (0-20)')
    ax.set_ylabel('Cantidad')
    ax.set_title('Distribución de Notas')
    tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmpimg.name, bbox_inches='tight')
    plt.close(fig)

    # create PDF with FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Sistema de Calificación Automática", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Curso: {course_name}    Código: {course_code}    Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(6)

    # Table header
    pdf.set_font("Arial", "B", 11)
    pdf.cell(80, 8, "PDF", 1)
    pdf.cell(30, 8, "Nota", 1)
    pdf.cell(30, 8, "Correctas", 1)
    pdf.cell(30, 8, "Total", 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for r in results_list:
        name = r['nombre_pdf'][:45]
        pdf.cell(80, 8, name, 1)
        pdf.cell(30, 8, f"{r['nota']:.2f}", 1)
        pdf.cell(30, 8, str(r['correctas']), 1)
        pdf.cell(30, 8, str(r['total']), 1)
        pdf.ln()

    pdf.ln(6)
    # Stats
    df = pd.DataFrame(results_list)
    promedio = round(df['nota'].mean(),2) if not df.empty else 0.0
    mayor = round(df['nota'].max(),2) if not df.empty else 0.0
    menor = round(df['nota'].min(),2) if not df.empty else 0.0
    aprobados = len(df[df['nota'] >= min_pass]) if not df.empty else 0
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Resumen de Estadísticas", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(1)
    pdf.cell(0, 6, f"Promedio general: {promedio}", ln=True)
    pdf.cell(0, 6, f"Promedio aprobados: {round(df[df['nota']>=min_pass]['nota'].mean(),2) if aprobados>0 else 0}", ln=True)
    pdf.cell(0, 6, f"Mayor nota: {mayor}", ln=True)
    pdf.cell(0, 6, f"Menor nota: {menor}", ln=True)
    pdf.cell(0, 6, f"Aprobados: {aprobados} / {len(results_list)}", ln=True)
    pdf.ln(8)
    # insert histogram
    try:
        pdf.image(tmpimg.name, x=20, w=170)
    except Exception:
        pass

    pdf.ln(6)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Nota: Este reporte fue generado por el sistema. Los resultados son simulados (datos generados internamente).")

    # return BytesIO
    bio = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    return bio

# ---------------- Layout: Inputs ----------------
st.sidebar.markdown("### ⚙️ Conexión")
st.sidebar.success("✅ Conectado al flujo n8n: `/examenes-calificar`")
st.sidebar.markdown("---")
st.sidebar.info("Escala 0-20 — Nota aprobatoria por defecto: 14")

st.header("1️⃣ Datos del Curso")
c1, c2 = st.columns(2)
with c1:
    course_name = st.text_input("Nombre del curso", value="Curso X")
with c2:
    course_code = st.text_input("Código del curso", value="C-001")

st.subheader("🔑 Clave de respuestas")
st.markdown("Formato: `1:a, 2:d, 3:e, 4:v, 5:f`  (use `v` y `f` para Verdadero/Falso)")
key_input = st.text_area("Ingresa la clave:", height=90, placeholder="Ej: 1:a, 2:b, 3:c, 4:v, 5:f")
if key_input:
    key = parse_key_string(key_input)
    st.session_state['key'] = key
    st.success(f"Clave cargada: {len(key)} preguntas")
else:
    key = st.session_state.get('key', {})

st.markdown("---")
st.header("2️⃣ Carga de PDFs")
uploaded = st.file_uploader("Sube hasta 30 PDFs (select multiple)", accept_multiple_files=True, type=['pdf'])
if uploaded:
    if len(uploaded) > 30:
        st.error("Máximo 30 PDFs. Reduce la selección.")
        uploaded = uploaded[:30]
    else:
        st.info(f"{len(uploaded)} archivos listos para analizar")
        with st.expander("Ver archivos cargados"):
            for i,f in enumerate(uploaded, start=1):
                st.write(f"{i}. {f.name} — {f.size/1024:.1f} KB")

st.markdown("---")
st.header("3️⃣ Analizar (envío a n8n)")

can_analyze = all([course_name.strip(), course_code.strip(), key and len(key)>0, uploaded and len(uploaded)>0])
if not can_analyze:
    missing = []
    if not course_name.strip(): missing.append("curso")
    if not course_code.strip(): missing.append("código")
    if not (key and len(key)>0): missing.append("clave")
    if not (uploaded and len(uploaded)>0): missing.append("PDFs")
    st.warning("Completa: " + ", ".join(missing))

if st.button("🚀 Analizar con n8n", disabled=not can_analyze):
    # pretend to send to backend
    st.markdown('<div class="processing-box"><h4>📡 Enviando exámenes al servidor n8n...</h4><div>Flujo: <code>/examenes-calificar</code></div></div>', unsafe_allow_html=True)
    progress = st.progress(0)
    status = st.empty()
    results = []
    total = len(uploaded)
    for i, f in enumerate(uploaded, start=1):
        status.info(f"⚙️ Procesando {f.name} ({i}/{total}) — Enviado al flujo `/examenes-calificar`")
        # small visual delay to simulate processing
        time.sleep(0.55)
        # generate deterministic fake result
        res = fake_grade_for_file(f.name, key)
        results.append(res)
        progress.progress(i/total)
    progress.progress(1.0)
    st.success("✅ Análisis completado")
    st.session_state['results'] = results
    st.session_state['processed'] = True
    st.session_state['course_name'] = course_name
    st.session_state['course_code'] = course_code
    st.balloons()

# ---------------- Show results ----------------
if st.session_state.get('processed') and st.session_state.get('results'):
    st.markdown("---")
    st.header("4️⃣ Resultados")
    df = pd.DataFrame(st.session_state['results'])
    # metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Promedio general", f"{df['nota'].mean():.2f}")
    with col2:
        aprob = len(df[df['nota']>=14])
        pct = (aprob/len(df))*100 if len(df)>0 else 0
        st.metric("Aprobados", f"{aprob}", delta=f"{pct:.1f}%")
    with col3:
        des = len(df[df['nota']<14])
        pctd = (des/len(df))*100 if len(df)>0 else 0
        st.metric("Desaprobados", f"{des}", delta=f"-{pctd:.1f}%")
    with col4:
        st.metric("Total PDFs", f"{len(df)}")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        if aprob>0:
            st.metric("Promedio aprobados", f"{df[df['nota']>=14]['nota'].mean():.2f}")
        else:
            st.metric("Promedio aprobados", "N/A")
    with col6:
        st.metric("Mayor nota", f"{df['nota'].max():.2f}")
    with col7:
        st.metric("Menor nota", f"{df['nota'].min():.2f}")
    with col8:
        st.metric("Total preguntas (clave)", f"{len(key)}")

    st.markdown("---")
    st.subheader("Detalle por PDF")
    df_display = df[['nombre_pdf','correctas','incorrectas','nota']].copy()
    df_display['estado'] = df_display['nota'].apply(lambda x: "Aprobado" if x>=14 else "Desaprobado")
    df_display = df_display.sort_values('nota', ascending=False).reset_index(drop=True)
    df_display.index += 1
    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")
    st.header("5️⃣ Exportar reporte")
    if st.button("📄 Generar Reporte PDF"):
        with st.spinner("Generando reporte..."):
            pdf_bytes = generate_report_pdf(st.session_state['results'], st.session_state['course_name'], st.session_state['course_code'], key)
            filename = f"reporte_{st.session_state['course_code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.download_button("⬇️ Descargar reporte PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("<div style='text-align:center; color: #888;'>Sistema de Calificación Automática • Interfaz (simulada) • n8n flow: /examenes-calificar</div>", unsafe_allow_html=True)
