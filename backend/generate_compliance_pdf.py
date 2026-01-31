"""
Generate PDF for workplace compliance policy
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

def generate_compliance_pdf():
    # Read the source file
    source_path = os.path.join(os.path.dirname(__file__), 
                               "sample_docs", 
                               "workplace_compliance_policy.txt")
    
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Output path
    output_path = os.path.join(os.path.dirname(__file__), 
                               "sample_docs", 
                               "workplace_compliance_policy.pdf")
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor='#1a1a2e',
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor='#555555'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=14,
        spaceAfter=6,
        textColor='#16213e',
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading3'],
        fontSize=10,
        spaceBefore=10,
        spaceAfter=4,
        textColor='#0f3460',
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        spaceBefore=2,
        spaceAfter=4,
        leading=12
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=9,
        leftIndent=20,
        spaceBefore=1,
        spaceAfter=1,
        leading=11
    )
    
    # Build content
    story = []
    
    lines = content.split('\n')
    in_header = True
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
            continue
        
        # Main title
        if i == 0:
            story.append(Paragraph(line, title_style))
            continue
        
        # Header metadata (Version, Effective Date, etc.)
        if in_header and (line.startswith('Version:') or 
                          line.startswith('Effective Date:') or 
                          line.startswith('Last Updated:') or
                          line.startswith('Document Owner:') or
                          line.startswith('Review Cycle:')):
            story.append(Paragraph(line, subtitle_style))
            continue
        
        if line.startswith('---'):
            story.append(Spacer(1, 12))
            in_header = False
            continue
        
        # Section headings (numbered like "1. PURPOSE")
        if line[0].isdigit() and '. ' in line[:5]:
            story.append(Paragraph(line, heading1_style))
            in_header = False
        # Subsection headings (like "3.1 General Safety")
        elif line[0].isdigit() and '.' in line[:6] and line.split()[0].count('.') == 1:
            story.append(Paragraph(line, heading2_style))
        # Bullet points
        elif line.startswith('•'):
            story.append(Paragraph(line, bullet_style))
        # Regular text
        else:
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"✅ PDF generated: {output_path}")

if __name__ == "__main__":
    generate_compliance_pdf()
