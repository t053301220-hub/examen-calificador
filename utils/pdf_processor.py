import fitz
import re
from PIL import Image
import io
import numpy as np

class PDFProcessor:
    def __init__(self):
        self.opciones_multiple = ['a', 'b', 'c', 'd', 'e']
        self.opciones_binarias = ['v', 'f']
    
    def extraer_respuestas(self, pdf_file):
        respuestas = {}
        
        try:
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)
            
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                respuestas_texto = self._extraer_por_texto(text)
                respuestas.update(respuestas_texto)
                
                if len(respuestas) == 0:
                    respuestas_imagen = self._extraer_por_imagen(page)
                    respuestas.update(respuestas_imagen)
            
            doc.close()
            
        except Exception as e:
            print(f"Error procesando PDF: {str(e)}")
        
        return respuestas
    
    def _extraer_por_texto(self, text):
        respuestas = {}
        
        text = text.upper()
        lines = text.split('\n')
        
        numero_pregunta = 0
        
        for i, line in enumerate(lines):
            match_pregunta = re.search(r'^\s*(\d+)[\.\)]\s*', line)
            if match_pregunta:
                numero_pregunta = int(match_pregunta.group(1))
                continue
            
            if numero_pregunta > 0:
                for opcion in ['A', 'B', 'C', 'D', 'E']:
                    pattern = rf'{opcion}[\)\.].*?X'
                    if re.search(pattern, line):
                        respuestas[numero_pregunta] = opcion.lower()
                        numero_pregunta = 0
                        break
                
                if 'V' in line and 'X' in line and line.index('V') < line.index('X'):
                    if 'F' not in line[:line.index('X')]:
                        respuestas[numero_pregunta] = 'v'
                        numero_pregunta = 0
                elif 'F' in line and 'X' in line and line.index('F') < line.index('X'):
                    if 'V' not in line[:line.index('X')]:
                        respuestas[numero_pregunta] = 'f'
                        numero_pregunta = 0
        
        return respuestas
    
    def _extraer_por_imagen(self, page):
        respuestas = {}
        
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            img_gray = img.convert('L')
            img_array = np.array(img_gray)
            
            height, width = img_array.shape
            
            region_height = height // 20
            
            for region_idx in range(15):
                y_start = region_idx * region_height
                y_end = y_start + region_height
                
                if y_end > height:
                    break
                
                region = img_array[y_start:y_end, :]
                
                dark_threshold = 100
                dark_pixels = np.sum(region < dark_threshold)
                
                if dark_pixels > 50:
                    for x in range(5):
                        x_start = int(width * x / 5)
                        x_end = int(width * (x + 1) / 5)
                        sub_region = region[:, x_start:x_end]
                        
                        dark_in_sub = np.sum(sub_region < dark_threshold)
                        if dark_in_sub > 30:
                            respuestas[region_idx + 1] = self.opciones_multiple[x]
                            break
            
        except Exception as e:
            print(f"Error en extracción por imagen: {str(e)}")
        
        return respuestas
    
    def _buscar_x_en_linea(self, line, opciones):
        line_upper = line.upper()
        
        for opcion in opciones:
            patterns = [
                rf'{opcion.upper()}\).*?X',
                rf'{opcion.upper()}\].*?X',
                rf'{opcion.upper()}\..*?X',
                rf'{opcion.upper()}\s+.*?X'
            ]
            
            for pattern in patterns:
                if re.search(pattern, line_upper):
                    return opcion.lower()
        
        return None
