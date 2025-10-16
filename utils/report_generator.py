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
        self.styles.add(ParagraphStyle(
            name='TituloPersonalizado',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtituloPersonalizado',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    def generar_reporte(self, curso_info, resultados):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        titulo = Paragraph(
            "SISTEMA DE CALIFICACIÓN AUTOMÁTICA",
            self.styles['TituloPersonalizado']
        )
        story.append(titulo)
        story.append(Spacer(1, 0.2*inch))
        
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
        
        subtitulo_stats = Paragraph("ESTADÍSTICAS GENERALES", self.styles['SubtituloPersonalizado'])
        story.append(subtitulo_stats)
        story.append(Spacer(1, 0.1*inch))
        
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
        
        story.append(self._crear_grafico_pastel(len(aprobados), len(desaprobados)))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(PageBreak())
        subtitulo_notas = Paragraph("CUADRO DE CALIFICACIONES", self.styles['SubtituloPersonalizado'])
        story.append(subtitulo_notas)
        story.append(Spacer(1, 0.1*inch))
        
        tabla_notas_data = [['N°', 'ESTUDIANTE', 'CORRECTAS', 'INCORRECTAS', 'NOTA', 'ESTADO']]
        
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
