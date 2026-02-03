"""
Generate PDF from the baggage damage policy document
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

def generate_policy_pdf():
    # Read the source file
    source_path = os.path.join(os.path.dirname(__file__), 
                               "sample_docs", 
                               "airline_checked_baggage_damage_refund_policy_v1.txt")
    
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Output path
    output_path = os.path.join(os.path.dirname(__file__), 
                               "sample_docs", 
                               "airline_checked_baggage_damage_refund_policy_v1.pdf")
    
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
        fontSize=14,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor='#1a1a2e'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=6,
        textColor='#16213e'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=10,
        spaceBefore=8,
        spaceAfter=4,
        textColor='#0f3460'
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
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
            continue
        
        # Title (first line with AIRLINE CHECKED BAGGAGE)
        if line.startswith('AIRLINE CHECKED BAGGAGE'):
            story.append(Paragraph(line, title_style))
        # Version/Date/Owner info
        elif line.startswith('Version:') or line.startswith('Effective Date:') or line.startswith('Owner:') or line.startswith('Applies To:'):
            story.append(Paragraph(line, body_style))
        # Main section headers (numbered)
        elif line and line[0].isdigit() and '.' in line[:3] and line.split('.')[0].isdigit():
            parts = line.split(' ', 1)
            if len(parts) > 1 and parts[1].isupper():
                story.append(Paragraph(line, heading_style))
            else:
                story.append(Paragraph(line, body_style))
        # Subsection headers (like 5.1, 9.2)
        elif line and len(line) > 3 and line[0].isdigit() and line[1] == '.' and line[2].isdigit():
            story.append(Paragraph(line, subheading_style))
        # Bullet points
        elif line.startswith('- '):
            story.append(Paragraph('• ' + line[2:], bullet_style))
        # Lettered items (A), B), etc.)
        elif line and line[0] in 'ABCDE' and line[1] == ')':
            story.append(Paragraph(line, bullet_style))
        # END OF POLICY
        elif line == 'END OF POLICY':
            story.append(Spacer(1, 20))
            story.append(Paragraph(line, title_style))
        # Regular text
        else:
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_policy_pdf()
