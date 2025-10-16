import streamlit as st
import time
import io
from datetime import datetime
from utils.pdf_processor import PDFProcessor
from utils.report_generator import ReportGenerator

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Calificación de Exámenes",
    page_icon="📝",
    layout="wide"
)

# Inicializar session state
if 'resultados' not in st.session_state:
    st.session_state.resultados = None
if 'curso_info' not in st.session_state:
    st.session_state.curso_info = None

# Título principal
st.title("📝 Sistema de Calificación Automática de Exámenes")
st.markdown("---")

# Sidebar para información del curso
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

# Función para parsear clave de respuestas
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

# Sección principal
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

# Botón para analizar
if st.button("🔍 Analizar con Google Gemini 1.5", type="primary", use_container_width=True):
    # Validaciones
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
            # Guardar información del curso
            st.session_state.curso_info = {
                'nombre': nombre_curso,
                'codigo': codigo_curso,
                'clave': clave_dict,
                'total_preguntas': len(clave_dict)
            }
            
            # Simulación de procesamiento con Google Gemini
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🚀 Inicializando Google Gemini 1.5...")
            time.sleep(0.5)
            progress_bar.progress(10)
            
            status_text.text("📄 Conectando con motor de procesamiento...")
            time.sleep(0.5)
            progress_bar.progress(20)
            
            # Procesar PDFs
            processor = PDFProcessor()
            resultados = []
            
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"🔍 Analizando {file.name} con IA...")
                progress = 20 + int((idx + 1) / len(uploaded_files) * 70)
                progress_bar.progress(progress)
                
                # Procesar PDF
                respuestas_alumno = processor.extraer_respuestas(file)
                
                # Calcular nota
                correctas = 0
                total = len(clave_dict)
                
                for num_pregunta, respuesta_correcta in clave_dict.items():
                    if num_pregunta in respuestas_alumno:
                        if respuestas_alumno[num_pregunta] == respuesta_correcta:
                            correctas += 1
                
                # Calcular nota en escala 0-20
                nota = (correctas / total) * 20
                
                resultados.append({
                    'nombre': file.name.replace('.pdf', ''),
                    'correctas': correctas,
                    'incorrectas': total - correctas,
                    'nota': round(nota, 2),
                    'estado': 'Aprobado' if nota >= 14 else 'Desaprobado'
                })
                
                time.sleep(0.3)  # Simular procesamiento
            
            status_text.text("✨ Finalizando análisis con Google Gemini 1.5...")
            progress_bar.progress(100)
            time.sleep(0.5)
            
            st.session_state.resultados = resultados
            
            status_text.empty()
            progress_bar.empty()
            st.success("✅ ¡Análisis completado exitosamente!")
            st.balloons()

# Mostrar resultados
if st.session_state.resultados:
    st.markdown("---")
    st.header("📊 Resultados del Análisis")
    
    resultados = st.session_state.resultados
    
    # Calcular estadísticas
    notas = [r['nota'] for r in resultados]
    aprobados = [r for r in resultados if r['estado'] == 'Aprobado']
    desaprobados = [r for r in resultados if r['estado'] == 'Desaprobado']
    
    # Métricas principales
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
    
    # Tabla de resultados
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Tabla de Calificaciones")
        
        # Crear tabla con estilo
        import pandas as pd
        df = pd.DataFrame(resultados)
        
        # Aplicar estilo
        def color_estado(val):
            color = '#90EE90' if val == 'Aprobado' else '#FFB6C6'
            return f'background-color: {color}'
        
        styled_df = df.style.applymap(color_estado, subset=['estado'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    with col2:
        st.subheader("📊 Distribución de Notas")
        
        import plotly.graph_objects as go
        
        # Gráfico de pastel
        fig = go.Figure(data=[go.Pie(
            labels=['Aprobados', 'Desaprobados'],
            values=[len(aprobados), len(desaprobados)],
            marker_colors=['#90EE90', '#FFB6C6'],
            hole=0.3
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de barras de notas
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
    
    # Botón para exportar reporte
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

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Sistema de Calificación Automática v1.0 | Powered by Google Gemini 1.5 ✨"
    "</div>",
    unsafe_allow_html=True
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
    
    def _crear_estilos_personalizados(self):
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='TituloPersonalizado',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubtituloPersonalizado',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para información
        self.styles.add(ParagraphStyle(
            name='InfoStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    def generar_reporte(self, curso_info, resultados):
        """
        Genera un reporte PDF completo con todos los resultados
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # === ENCABEZADO ===
        titulo = Paragraph(
            "SISTEMA DE CALIFICACIÓN AUTOMÁTICA",
            self.styles['TituloPersonalizado']
        )
        story.append(titulo)
        story.append(Spacer(1, 0.2*inch))
        
        # Información del curso
        curso_data = [
            ['Curso:', curso_info['nombre']],
            ['Código:', curso_info['codigo']],
            ['Fecha:', datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
            ['Total de Preguntas:', str(curso_info['total_preguntas'])],
            ['Nota Aprobatoria:', '14.0'],
            ['Escala:', '0 - 20']
        ]
        
        curso_table = Table(curso_data, colWidths=[2*inch, 4*inch])
        curso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(curso_table)
        story.append(Spacer(1, 0.3*inch))
        
        # === ESTADÍSTICAS GENERALES ===
        subtitulo_stats = Paragraph("ESTADÍSTICAS GENERALES", self.styles['SubtituloPersonalizado'])
        story.append(subtitulo_stats)
        story.append(Spacer(1, 0.1*inch))
        
        # Calcular estadísticas
        notas = [r['nota'] for r in resultados]
        aprobados = [r for r in resultados if r['estado'] == 'Aprobado']
        desaprobados = [r for r in resultados if r['estado'] == 'Desaprobado']
        
        promedio_general = sum(notas) / len(notas)
        promedio_aprobados = sum([r['nota'] for r in aprobados]) / len(aprobados) if aprobados else 0
        promedio_desaprobados = sum([r['nota'] for r in desaprobados]) / len(desaprobados) if desaprobados else 0
        
        stats_data = [
            ['MÉTRICA', 'VALOR'],
            ['Total de Estudiantes', str(len(resultados))],
            ['Promedio General', f"{promedio_general:.2f}"],
            ['Estudiantes Aprobados', f"{len(aprobados)} ({len(aprobados)/len(resultados)*100:.1f}%)"],
            ['Estudiantes Desaprobados', f"{len(desaprobados)} ({len(desaprobados)/len(resultados)*100:.1f}%)"],
            ['Promedio de Aprobados', f"{promedio_aprobados:.2f}"],
            ['Promedio de Desaprobados', f"{promedio_desaprobados:.2f}"],
            ['Nota Máxima', f"{max(notas):.2f}"],
            ['Nota Mínima', f"{min(notas):.2f}"],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.3*inch))
        
        # === GRÁFICO DE PASTEL ===
        story.append(self._crear_grafico_pastel(len(aprobados), len(desaprobados)))
        story.append(Spacer(1, 0.3*inch))
        
        # === TABLA DE CALIFICACIONES ===
        story.append(PageBreak())
        subtitulo_notas = Paragraph("CUADRO DE CALIFICACIONES", self.styles['SubtituloPersonalizado'])
        story.append(subtitulo_notas)
        story.append(Spacer(1, 0.1*inch))
        
        # Crear tabla de notas
        tabla_notas_data = [['N°', 'ESTUDIANTE', 'CORRECTAS', 'INCORRECTAS', 'NOTA', 'ESTADO']]
        
        # Ordenar por nota (mayor a menor)
        resultados_ordenados = sorted(resultados, key=lambda x: x['nota'], reverse=True)
        
        for idx, resultado in enumerate(resultados_ordenados, 1):
            tabla_notas_data.append([
                str(idx),
                resultado['nombre'][:30] + '...' if len(resultado['nombre']) > 30 else resultado['nombre'],
                str(resultado['correctas']),
                str(resultado['incorrectas']),
                f"{resultado['nota']:.2f}",
                resultado['estado']
            ])
        
        tabla_notas = Table(tabla_notas_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch])
        
        # Estilo de la tabla con colores
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]
        
        # Colorear filas según estado
        for idx, resultado in enumerate(resultados_ordenados, 1):
            if resultado['estado'] == 'Aprobado':
                table_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#d1fae5')))
            else:
                table_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#fecaca')))
        
        tabla_notas.setStyle(TableStyle(table_style))
        story.append(tabla_notas)
        story.append(Spacer(1, 0.3*inch))
        
        # === GRÁFICO DE BARRAS ===
        story.append(self._crear_grafico_barras(resultados_ordenados[:10]))  # Top 10
        story.append(Spacer(1, 0.2*inch))
        
        # === PIE DE PÁGINA ===
        footer = Paragraph(
            f"<i>Reporte generado automáticamente por Sistema de Calificación v1.0 | Powered by Google Gemini 1.5</i>",
            self.styles['Normal']
        )
        story.append(Spacer(1, 0.3*inch))
        story.append(footer)
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _crear_grafico_pastel(self, aprobados, desaprobados):
        """
        Crea un gráfico de pastel para aprobados/desaprobados
        """
        drawing = Drawing(400, 200)
        
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 150
        pie.height = 150
        pie.data = [aprobados, desaprobados]
        pie.labels = ['Aprobados', 'Desaprobados']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor('#10b981')
        pie.slices[1].fillColor = colors.HexColor('#ef4444')
        
        drawing.add(pie)
        
        return drawing
    
    def _crear_grafico_barras(self, resultados):
        """
        Crea un gráfico de barras con las notas
        """
        if len(resultados) == 0:
            return Spacer(1, 0)
        
        drawing = Drawing(500, 250)
        
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 150
        bc.width = 400
        
        # Tomar solo los primeros 10 resultados
        data_to_plot = resultados[:10] if len(resultados) > 10 else resultados
        
        bc.data = [[r['nota'] for r in data_to_plot]]
        bc.categoryAxis.categoryNames = [r['nombre'][:10] + '...' if len(r['nombre']) > 10 else r['nombre'] for r in data_to_plot]
        bc.categoryAxis.labels.angle = 45
        bc.categoryAxis.labels.fontSize = 8
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 20
        bc.valueAxis.valueStep = 5
        
        # Colorear barras
        for i, resultado in enumerate(data_to_plot):
            if resultado['nota'] >= 14:
                bc.bars[0][i].fillColor = colors.HexColor('#10b981')
            else:
                bc.bars[0][i].fillColor = colors.HexColor('#ef4444')
        
        drawing.add(bc)
        
        return drawing