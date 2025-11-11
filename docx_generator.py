from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os
from templates.report_template import get_report_structure

def generate_report(student_data, classification):
    doc = Document()
    
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    structure = get_report_structure(student_data, classification)
    
    _render_header(doc, structure['header'], structure['metadata'])
    
    for section in structure['sections']:
        _render_section(doc, section)
    
    _render_footer(doc, structure['footer'])
    
    filename = _generate_filename(student_data['applicant_name'])
    filepath = os.path.join('/tmp', filename)
    doc.save(filepath)
    
    return filepath

def _render_header(doc, header, metadata):
    title = doc.add_heading(header['title'], 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_heading(header['subtitle'], level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    date_para = doc.add_paragraph()
    date_run = date_para.add_run(f"Fecha: {metadata['generated_date']}")
    date_run.bold = True
    
    doc.add_paragraph()

def _render_section(doc, section):
    doc.add_heading(section['title'], level=2)
    
    section_type = section['type']
    
    if section_type == 'key_value_pairs':
        _render_key_value_pairs(doc, section['content'])
    elif section_type == 'recommendation':
        _render_recommendation(doc, section['content'])
    elif section_type == 'paragraph':
        doc.add_paragraph(section['content'])
    elif section_type == 'subsections':
        _render_subsections(doc, section['content'])
    elif section_type == 'alert_box':
        _render_alert_box(doc, section['content'], section.get('alert_level', 'info'))
    
    doc.add_paragraph()

def _render_key_value_pairs(doc, pairs):
    for item in pairs:
        p = doc.add_paragraph()
        p.add_run(f"{item['label']}: ").bold = True
        p.add_run(item['value'])

def _render_recommendation(doc, content):
    level_data = content['level']
    level_para = doc.add_paragraph()
    level_para.add_run(f"{level_data['label']}: ").bold = True
    
    level_run = level_para.add_run(level_data['value'])
    level_run.bold = True
    level_run.font.size = Pt(14)
    
    if level_data.get('highlight') and level_data.get('color') == 'blue':
        level_run.font.color.rgb = RGBColor(0, 102, 204)
    
    doc.add_paragraph()
    
    programs_data = content['programs']
    programs_para = doc.add_paragraph()
    programs_para.add_run(f"{programs_data['label']}:").bold = True
    
    for program in programs_data['value']:
        doc.add_paragraph(f'• {program}', style='List Bullet')
    
    doc.add_paragraph()
    
    confidence_data = content['confidence']
    conf_para = doc.add_paragraph()
    conf_para.add_run(f"{confidence_data['label']}: ").bold = True
    conf_para.add_run(confidence_data['value'])
    
    if confidence_data.get('show_warning'):
        warning = doc.add_paragraph()
        warning_run = warning.add_run('⚠️ ATENCIÓN: Nivel de confianza bajo. Revisión manual recomendada.')
        warning_run.bold = True
        warning_run.font.color.rgb = RGBColor(204, 0, 0)

def _render_subsections(doc, subsections):
    for subsection in subsections:
        subtitle_para = doc.add_paragraph()
        subtitle_para.add_run(subsection['subtitle']).bold = True
        doc.add_paragraph(subsection['text'])
        doc.add_paragraph()

def _render_alert_box(doc, content, alert_level):
    alert_para = doc.add_paragraph(content)
    
    if alert_level == 'warning':
        alert_para.runs[0].font.color.rgb = RGBColor(204, 102, 0)
    elif alert_level == 'error':
        alert_para.runs[0].font.color.rgb = RGBColor(204, 0, 0)

def _render_footer(doc, footer):
    doc.add_paragraph()
    doc.add_paragraph('_' * 50)
    
    footer_para = doc.add_paragraph(footer['text'])
    footer_para.runs[0].font.size = Pt(9)
    footer_para.runs[0].font.italic = True
    
    if 'disclaimer' in footer:
        disclaimer_para = doc.add_paragraph(footer['disclaimer'])
        disclaimer_para.runs[0].font.size = Pt(8)
        disclaimer_para.runs[0].font.italic = True
        disclaimer_para.runs[0].font.color.rgb = RGBColor(128, 128, 128)

def _generate_filename(applicant_name):
    safe_name = applicant_name.replace(' ', '_').replace('/', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"Clasificacion_{safe_name}_{timestamp}.docx"