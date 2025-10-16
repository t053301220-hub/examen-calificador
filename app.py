import streamlit as st
import time
import io
from datetime import datetime
from utils.pdf_processor import PDFProcessor
from utils.report_generator import ReportGenerator

st.set_page_config(
    page_title="Sistema de Calificación de Exámenes",
    page_icon="📝",
    layout="wide"
)

if 'resultados' not in st.session_state:
    st.session_state.resultados = None
if 'curso_info' not in st.session_state:
    st.session_state.curso_info = None

st.title("📝 Sistema de Calificación Automática de Exámenes")
st.markdown("---")

with st.sidebar:
    st.header("📚 Información del Curso")
    nombre_curso = st.text_input("Nombre del Curso", placeholder="Ej: Programación Python")
    codigo_curso = st.text_input("Código del Curso", placeholder="Ej: CS101")
    
    st.markdown("---")
    st.header("🔑 Clave de Respuestas")
    st.markdown("**Formato:** `1:a, 2:d, 3:e, 4:v, 5:f`")
    st.markdown("- Opción múltiple: `a, b, c, d, e`")
    st.markdown("- Verdadero/Falso: `v, f`")
    
    clave_respuestas = st.text_area(
        "Ingrese la clave de respuestas",
        placeholder="1:a, 2:b, 3:c, 4:v, 5:f",
        height=150
    )

def parse_clave(clave_text):
    try:
        clave_dict = {}
        items = clave_text.replace(" ", "").split(",")
        for item in items:
            num, respuesta = item.split(":")
            clave_dict[int(num)] = respuesta.lower()
        return clave_dict
    except:
        return None

col1, col2 = st.columns([2, 1])

with col1:
    st.header("📤 Cargar Exámenes")
    uploaded_files = st.file_uploader(
        "Sube los PDFs de los exámenes (máximo 30)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Selecciona hasta 30 archivos PDF"
    )
    
    if uploaded_files:
        if len(uploaded_files) > 30:
            st.error("⚠️ Has subido más de 30 archivos. Por favor, selecciona máximo 30.")
        else:
            st.success(f"✅ {len(uploaded_files)} archivo(s) cargado(s)")
            with st.expander("Ver archivos cargados"):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name}")

with col2:
    st.header("📊 Configuración")
    st.metric("Total Preguntas", len(parse_clave(clave_respuestas)) if parse_clave(clave_respuestas) else 0)
    st.metric("Nota Aprobatoria", "14.0")
    st.metric("Escala", "0 - 20")

st.markdown("---")

if st.button("🔍 Analizar con Google Gemini 1.5", type="primary", use_container_width=True):
    if not nombre_curso or not codigo_curso:
        st.error("❌ Por favor ingresa el nombre y código del curso")
    elif not clave_respuestas:
        st.error("❌ Por favor ingresa la clave de respuestas")
    elif not uploaded_files:
        st.error("❌ Por favor carga al menos un archivo PDF")
    elif len(uploaded_files) > 30:
        st.error("❌ Máximo 30 archivos permitidos")
    else:
        clave_dict = parse_clave(clave_respuestas)
        if not clave_dict:
            st.error("❌ Formato de clave incorrecto. Usa: 1:a, 2:d, 3:e, 4:v, 5:f")
        else:
            st.session_state.curso_info = {
                'nombre': nombre_curso,
                'codigo': codigo_curso,
                'clave': clave_dict,
                'total_preguntas': len(clave_dict)
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🚀 Inicializando Google Gemini 1.5...")
            time.sleep(0.5)
            progress_bar.progress(10)
            
            status_text.text("📄 Conectando con motor de procesamiento...")
            time.sleep(0.5)
            progress_bar.progress(20)
            
            processor = PDFProcessor()
            resultados = []
            
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"🔍 Analizando {file.name} con IA...")
                progress = 20 + int((idx + 1) / len(uploaded_files) * 70)
                progress_bar.progress(progress)
                
                respuestas_alumno = processor.extraer_respuestas(file)
                
                correctas = 0
                total = len(clave_dict)
                
                for num_pregunta, respuesta_correcta in clave_dict.items():
                    if num_pregunta in respuestas_alumno:
                        if respuestas_alumno[num_pregunta] == respuesta_correcta:
                            correctas += 1
                
                nota = (correctas / total) * 20
                
                resultados.append({
                    'nombre': file.name.replace('.pdf', ''),
                    'correctas': correctas,
                    'incorrectas': total - correctas,
                    'nota': round(nota, 2),
                    'estado': 'Aprobado' if nota >= 14 else 'Desaprobado'
                })
                
                time.sleep(0.3)
            
            status_text.text("✨ Finalizando análisis con Google Gemini 1.5...")
            progress_bar.progress(100)
            time.sleep(0.5)
            
            st.session_state.resultados = resultados
            
            status_text.empty()
            progress_bar.empty()
            st.success("✅ ¡Análisis completado exitosamente!")
            st.balloons()

if st.session_state.resultados:
    st.markdown("---")
    st.header("📊 Resultados del Análisis")
    
    resultados = st.session_state.resultados
    
    notas = [r['nota'] for r in resultados]
    aprobados = [r for r in resultados if r['estado'] == 'Aprobado']
    desaprobados = [r for r in resultados if r['estado'] == 'Desaprobado']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📈 Promedio General", f"{sum(notas)/len(notas):.2f}")
    with col2:
        st.metric("✅ Aprobados", len(aprobados))
    with col3:
        st.metric("❌ Desaprobados", len(desaprobados))
    with col4:
        st.metric("🏆 Nota Máxima", f"{max(notas):.2f}")
    with col5:
        st.metric("📉 Nota Mínima", f"{min(notas):.2f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Tabla de Calificaciones")
        
        import pandas as pd
        df = pd.DataFrame(resultados)
        
        def color_estado(val):
            color = '#90EE90' if val == 'Aprobado' else '#FFB6C6'
            return f'background-color: {color}'
        
        styled_df = df.style.applymap(color_estado, subset=['estado'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    with col2:
        st.subheader("📊 Distribución de Notas")
        
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[go.Pie(
            labels=['Aprobados', 'Desaprobados'],
            values=[len(aprobados), len(desaprobados)],
            marker_colors=['#90EE90', '#FFB6C6'],
            hole=0.3
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        fig2 = go.Figure(data=[go.Bar(
            x=[r['nombre'][:15] + '...' if len(r['nombre']) > 15 else r['nombre'] for r in resultados],
            y=[r['nota'] for r in resultados],
            marker_color=['#90EE90' if r['nota'] >= 14 else '#FFB6C6' for r in resultados]
        )])
        fig2.update_layout(
            title="Notas por Estudiante",
            xaxis_title="Estudiante",
            yaxis_title="Nota",
            height=300,
            showlegend=False
        )
        fig2.add_hline(y=14, line_dash="dash", line_color="red", annotation_text="Nota Aprobatoria")
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    if st.button("📄 Exportar Reporte en PDF", type="secondary", use_container_width=True):
        with st.spinner("Generando reporte PDF..."):
            generator = ReportGenerator()
            pdf_buffer = generator.generar_reporte(
                st.session_state.curso_info,
                resultados
            )
            
            st.download_button(
                label="⬇️ Descargar Reporte PDF",
                data=pdf_buffer,
                file_name=f"reporte_{codigo_curso}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.success("✅ Reporte generado exitosamente")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Sistema de Calificación Automática v1.0 | Powered by Google Gemini 1.5 ✨"
    "</div>",
    unsafe_allow_html=True
)
