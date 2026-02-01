"""Generate a workplace safety regulation PDF"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import datetime

# Output file
pdf_file = 'sample_docs/workplace_safety_regulation.pdf'

# Create PDF
doc = SimpleDocTemplate(
    pdf_file,
    pagesize=letter,
    rightMargin=72,
    leftMargin=72,
    topMargin=72,
    bottomMargin=18
)

# Styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor='#1a1a1a',
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)
heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor='#2d3748',
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)
body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    textColor='#4a5568',
    alignment=TA_JUSTIFY,
    spaceAfter=12,
    leading=14
)

# Build content
story = []

# Title
story.append(Paragraph('WORKPLACE SAFETY REGULATION', title_style))
story.append(Spacer(1, 0.2*inch))

# Metadata
story.append(Paragraph(f'Effective Date: {datetime.date.today().strftime("%B %d, %Y")}', body_style))
story.append(Paragraph('Document ID: WSR-2026-001', body_style))
story.append(Spacer(1, 0.3*inch))

# Section 1
story.append(Paragraph('1. PURPOSE AND SCOPE', heading_style))
story.append(Paragraph(
    'This regulation establishes comprehensive workplace safety requirements to protect employees, '
    'contractors, and visitors from occupational hazards. All personnel must comply with these safety '
    'standards at all facilities operated by the organization.',
    body_style
))

# Section 2
story.append(Paragraph('2. PERSONAL PROTECTIVE EQUIPMENT (PPE)', heading_style))
story.append(Paragraph(
    '2.1 Required PPE: All employees working in designated hazardous areas must wear appropriate personal '
    'protective equipment including safety glasses, hard hats, steel-toed boots, and high-visibility vests. '
    'Hearing protection is mandatory in areas exceeding 85 decibels.',
    body_style
))
story.append(Paragraph(
    '2.2 PPE Maintenance: Employees are responsible for inspecting PPE before each use and reporting any '
    'damage or defects immediately. Damaged equipment must be replaced within 24 hours.',
    body_style
))

# Section 3
story.append(Paragraph('3. EMERGENCY PROCEDURES', heading_style))
story.append(Paragraph(
    '3.1 Emergency Evacuation: In the event of fire, chemical spill, or other emergencies requiring evacuation, '
    'employees must proceed immediately to designated assembly points. Floor wardens will verify attendance and '
    'report to emergency coordinators.',
    body_style
))
story.append(Paragraph(
    '3.2 First Aid Response: At least one certified first aid responder must be present during all operational hours. '
    'First aid kits must be accessible within 100 feet of any work area and inspected monthly.',
    body_style
))

# Section 4
story.append(Paragraph('4. HAZARD COMMUNICATION', heading_style))
story.append(Paragraph(
    '4.1 Safety Data Sheets: Safety Data Sheets (SDS) for all hazardous materials must be maintained in accessible '
    'locations. Employees working with hazardous substances must complete training on proper handling, storage, and '
    'emergency response procedures.',
    body_style
))
story.append(Paragraph(
    '4.2 Warning Signage: Areas containing potential hazards must be clearly marked with appropriate warning signs '
    'meeting OSHA standards. Signs must be visible from all approach directions and maintained in good condition.',
    body_style
))

# Section 5
story.append(Paragraph('5. INCIDENT REPORTING', heading_style))
story.append(Paragraph(
    '5.1 Immediate Reporting: All workplace injuries, near-miss incidents, and safety violations must be reported '
    'to supervisors within one hour of occurrence. Failure to report incidents may result in disciplinary action.',
    body_style
))
story.append(Paragraph(
    '5.2 Investigation Protocol: Safety officers will investigate all incidents within 24 hours. Investigation reports '
    'must document root causes and corrective actions to prevent recurrence.',
    body_style
))

# Section 6
story.append(Paragraph('6. TRAINING REQUIREMENTS', heading_style))
story.append(Paragraph(
    '6.1 Initial Safety Training: New employees must complete comprehensive safety orientation within their first week '
    'of employment. Training covers emergency procedures, hazard recognition, and proper use of safety equipment.',
    body_style
))
story.append(Paragraph(
    '6.2 Refresher Training: Annual safety refresher training is mandatory for all employees. Additional training is '
    'required when new equipment or procedures are introduced.',
    body_style
))

# Section 7
story.append(Paragraph('7. WORKPLACE INSPECTIONS', heading_style))
story.append(Paragraph(
    '7.1 Regular Inspections: Safety officers conduct monthly workplace inspections to identify hazards and verify '
    'compliance with safety regulations. Inspection reports are reviewed by management and corrective actions tracked '
    'to completion.',
    body_style
))
story.append(Paragraph(
    '7.2 Self-Inspections: Department supervisors must perform weekly safety self-inspections of their work areas and '
    'document findings in the safety management system.',
    body_style
))

# Section 8
story.append(Paragraph('8. ENFORCEMENT AND COMPLIANCE', heading_style))
story.append(Paragraph(
    '8.1 Disciplinary Actions: Violations of safety regulations will result in progressive disciplinary action, including '
    'verbal warnings, written warnings, suspension, or termination depending on severity and frequency of violations.',
    body_style
))
story.append(Paragraph(
    '8.2 Management Accountability: Supervisors and managers are responsible for enforcing safety regulations within '
    'their areas of responsibility. Management performance evaluations include safety metrics.',
    body_style
))

# Revision History
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph('9. REVISION HISTORY', heading_style))
story.append(Paragraph('Version 1.0 - Initial release (February 2026)', body_style))

# Contact
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    'For questions regarding this regulation, contact the Safety Department at safety@company.com or extension 4444.',
    body_style
))

# Build PDF
doc.build(story)
print(f'✅ Generated: {pdf_file}')
