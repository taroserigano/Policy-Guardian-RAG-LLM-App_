"""Generate Amoozon Retail Category Manager Regulation PDF"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import datetime

# Output file
pdf_file = 'sample_docs/amoozon_category_manager_regulation.pdf'

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
    fontSize=22,
    textColor='#1a1a1a',
    spaceAfter=20,
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
story.append(Paragraph('AMOOZON RETAIL CATEGORY MANAGER', title_style))
story.append(Paragraph('OPERATIONAL REGULATION', title_style))
story.append(Spacer(1, 0.2*inch))

# Metadata
story.append(Paragraph(f'Effective Date: {datetime.date.today().strftime("%B %d, %Y")}', body_style))
story.append(Paragraph('Document ID: ACM-REG-2026-001', body_style))
story.append(Paragraph('Classification: Internal Use Only', body_style))
story.append(Spacer(1, 0.3*inch))

# Section 1
story.append(Paragraph('1. PURPOSE AND SCOPE', heading_style))
story.append(Paragraph(
    'This regulation defines the operational standards, responsibilities, and compliance requirements for '
    'Category Managers within Amoozon Retail operations. Category Managers are responsible for driving business '
    'growth, managing vendor relationships, and ensuring product catalog quality across assigned categories. '
    'This regulation applies to all Category Managers, Senior Category Managers, and Category Leadership roles.',
    body_style
))

# Section 2
story.append(Paragraph('2. VENDOR MANAGEMENT STANDARDS', heading_style))
story.append(Paragraph(
    '2.1 Vendor Onboarding: Category Managers must complete vendor onboarding within 14 business days of initial '
    'contact. All new vendors must be registered in Vendor Central with complete business documentation including '
    'tax identification, banking details, and product liability insurance certificates.',
    body_style
))
story.append(Paragraph(
    '2.2 Vendor Performance Reviews: Quarterly business reviews must be conducted with all strategic vendors '
    'representing more than $500K annual revenue. Performance metrics including order defect rate, late shipment '
    'rate, and customer satisfaction scores must be reviewed and documented.',
    body_style
))
story.append(Paragraph(
    '2.3 Vendor Communication: All vendor negotiations and agreements must be documented in the vendor management '
    'system within 48 hours. Category Managers must respond to vendor inquiries within 2 business days.',
    body_style
))

# Section 3
story.append(Paragraph('3. PRODUCT CATALOG MANAGEMENT', heading_style))
story.append(Paragraph(
    '3.1 Product Listing Standards: All product listings must include minimum of 5 high-quality images, detailed '
    'bullet points (minimum 4, maximum 10), and comprehensive product descriptions exceeding 200 characters. '
    'Product titles must follow category-specific naming conventions and not exceed 200 characters.',
    body_style
))
story.append(Paragraph(
    '3.2 Content Quality Control: Category Managers must review and approve all new product listings within 72 hours. '
    'Products failing to meet content quality standards must be suppressed until corrections are made. Monthly audits '
    'of at least 5% of category ASINs are mandatory.',
    body_style
))
story.append(Paragraph(
    '3.3 Product Classification: All products must be assigned to the most specific browse node available. Category '
    'Managers are responsible for ensuring proper categorization, attribute completion, and keyword optimization for '
    'search discoverability.',
    body_style
))

# Section 4
story.append(Paragraph('4. PRICING AND PROMOTION MANAGEMENT', heading_style))
story.append(Paragraph(
    '4.1 Pricing Strategy: Category Managers must maintain competitive pricing positioning within top 3 competitors '
    'for designated strategic ASINs. Price changes exceeding 15% require senior leadership approval. Automated pricing '
    'tools must be configured with appropriate min/max price guardrails.',
    body_style
))
story.append(Paragraph(
    '4.2 Promotional Planning: Promotional events must be planned minimum 6 weeks in advance with complete deal '
    'structures submitted to merchandising team. Lightning Deals require minimum 20% discount and sufficient inventory '
    'to support 4-hour run time. Deal acceptance rate target is 85% or higher.',
    body_style
))
story.append(Paragraph(
    '4.3 Margin Protection: Category Managers must maintain minimum category gross margin of 25% unless specifically '
    'approved for strategic loss-leader positioning. Weekly margin reviews are required with variance explanations '
    'documented for any category falling below threshold.',
    body_style
))

# Section 5
story.append(Paragraph('5. INVENTORY AND SUPPLY CHAIN COMPLIANCE', heading_style))
story.append(Paragraph(
    '5.1 Inventory Health: Category Managers must maintain in-stock rate above 95% for top 100 revenue-generating '
    'ASINs. Out-of-stock duration exceeding 72 hours requires root cause analysis and corrective action plan. '
    'Aged inventory exceeding 90 days must be addressed through promotions or vendor returns.',
    body_style
))
story.append(Paragraph(
    '5.2 Demand Forecasting: Monthly demand forecasts must be submitted to supply chain team by the 15th of each month. '
    'Forecast accuracy must exceed 80% measured against actual sales. Category Managers are responsible for communicating '
    'significant demand shifts to vendors and logistics partners.',
    body_style
))
story.append(Paragraph(
    '5.3 Vendor Lead Times: Standard lead times must be documented for all active vendors. Purchase orders must be '
    'placed with sufficient lead time to prevent stockouts. Emergency expedited shipping costs require finance approval '
    'and are tracked against category P&L.',
    body_style
))

# Section 6
story.append(Paragraph('6. PERFORMANCE METRICS AND REPORTING', heading_style))
story.append(Paragraph(
    '6.1 Weekly Business Reviews: Category Managers must submit weekly business reports by Monday 10 AM including '
    'sales performance, traffic metrics, conversion rates, and top performer/decliner analysis. Reports must include '
    'week-over-week and year-over-year comparisons.',
    body_style
))
story.append(Paragraph(
    '6.2 KPI Targets: Mandatory KPI targets include: (a) Revenue growth 15% YoY minimum, (b) Unit sales growth 12% YoY '
    'minimum, (c) Conversion rate above category benchmark, (d) Customer review rating 4.0+ average, (e) Return rate '
    'below 8%. Consecutive quarters below targets trigger performance improvement plan.',
    body_style
))
story.append(Paragraph(
    '6.3 Competitive Intelligence: Monthly competitive analysis reports must document pricing positioning, assortment '
    'gaps, and promotional activity of top 3 competitors. New product launches by competitors must be flagged within '
    '48 hours with recommended counter-strategy.',
    body_style
))

# Section 7
story.append(Paragraph('7. BRAND AND PRODUCT LAUNCHES', heading_style))
story.append(Paragraph(
    '7.1 Launch Planning: New brand or product line launches require comprehensive launch plans submitted 8 weeks prior '
    'to go-live date. Plans must include marketing strategy, inventory positioning, promotional calendar, and success '
    'metrics. Cross-functional review with marketing, merchandising, and operations teams is mandatory.',
    body_style
))
story.append(Paragraph(
    '7.2 Launch Execution: During 30-day post-launch period, Category Managers must monitor daily performance metrics '
    'and provide weekly status updates. Product detail page optimization and promotional adjustments must be made within '
    '72 hours if performance falls below projections.',
    body_style
))

# Section 8
story.append(Paragraph('8. COMPLIANCE AND QUALITY ASSURANCE', heading_style))
story.append(Paragraph(
    '8.1 Regulatory Compliance: Category Managers must ensure all products meet applicable safety standards, '
    'certifications, and regulatory requirements (FDA, FCC, CPSC, etc.). Products requiring special handling or '
    'documentation must be properly flagged in catalog systems. Non-compliant products must be removed within 4 hours.',
    body_style
))
story.append(Paragraph(
    '8.2 Customer Experience Standards: Products with customer review ratings below 3.5 stars must be evaluated for '
    'quality issues. Category Managers must work with vendors to address systematic quality problems or discontinue '
    'problematic ASINs. Customer complaint patterns must be analyzed monthly.',
    body_style
))
story.append(Paragraph(
    '8.3 Intellectual Property: Category Managers must verify vendor authorization to sell branded products. Suspected '
    'counterfeit or unauthorized products must be reported to Brand Protection team immediately. IP complaints must be '
    'addressed within 24 hours with vendor investigation and resolution.',
    body_style
))

# Section 9
story.append(Paragraph('9. DATA SECURITY AND CONFIDENTIALITY', heading_style))
story.append(Paragraph(
    '9.1 Confidential Information: All vendor pricing agreements, margin data, and strategic planning documents are '
    'classified as confidential. Category Managers must not disclose competitive information between vendors. '
    'Vendor business data must be accessed only for legitimate business purposes.',
    body_style
))
story.append(Paragraph(
    '9.2 System Access: Category Managers have access to sensitive retail systems including Vendor Central, retail '
    'analytics platforms, and pricing tools. Access credentials must not be shared. Unusual system activity or suspected '
    'data breaches must be reported to IT Security immediately.',
    body_style
))

# Section 10
story.append(Paragraph('10. ESCALATION AND EXCEPTION HANDLING', heading_style))
story.append(Paragraph(
    '10.1 Decision Authority: Category Managers have autonomous decision authority for tactical operational decisions '
    'within established guardrails. Strategic decisions affecting annual category P&L by more than $100K require senior '
    'leadership approval. New vendor contracts exceeding $1M annual commitment require legal review.',
    body_style
))
story.append(Paragraph(
    '10.2 Exception Requests: Exceptions to standard policies must be submitted via formal exception request process '
    'with business justification and risk assessment. Temporary exceptions are valid for maximum 90 days and must be '
    'documented in category compliance log.',
    body_style
))

# Revision History
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph('11. REVISION HISTORY', heading_style))
story.append(Paragraph('Version 1.0 - Initial release (February 2026)', body_style))
story.append(Paragraph('Version 1.1 - Updated vendor management standards (Planned Q2 2026)', body_style))

# Contact
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    'For questions or clarifications regarding this regulation, contact Category Management Leadership at '
    'cm-leadership@amoozon.com or your assigned Retail Operations Manager.',
    body_style
))

# Build PDF
doc.build(story)
print(f'✅ Generated: {pdf_file}')
