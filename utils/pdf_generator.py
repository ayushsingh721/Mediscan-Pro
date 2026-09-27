# ============================================================
# utils/pdf_generator.py — Clinical Health Report PDF Generator
# ============================================================

import io
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count,
    along with running header and footer on every page.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_width, page_height = self._pagesize

        # Running Top Border Line (pages > 1)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor('#0891b2'))
            self.setLineWidth(1)
            self.line(36, page_height - 30, page_width - 36, page_height - 30)

            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor('#0f172a'))
            self.drawString(36, page_height - 24, "MEDISCAN PRO — DIGITAL HEALTH REPORT")

            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor('#64748b'))
            self.drawRightString(page_width - 36, page_height - 24, "CONFIDENTIAL MEDICAL SCREENING")

        # Running Bottom Footer (all pages)
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.75)
        self.line(36, 40, page_width - 36, 40)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(36, 26, "MediScan Pro Clinical Intelligence • Screening Tool Only • Not a Final Medical Diagnosis")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - 36, 26, page_str)
        self.restoreState()


def generate_pdf_report(user,
                        prediction,
                        user_profile: Optional[Any] = None,
                        insights: Optional[Dict[str, Any]] = None) -> io.BytesIO:
    """
    Generates a professional, multi-page ready clinical PDF report.
    Returns an in-memory BytesIO buffer.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # ── Custom Typography Styles ──────────────────────────────
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f2744')
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0891b2')
    )

    section_heading = ParagraphStyle(
        'SecHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f2744'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569')
    )

    value_text = ParagraphStyle(
        'ValueText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=14
    )

    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#475569')
    )

    story = []

    # ── 1. HEADER BANNER TABLE ────────────────────────────────
    report_id = f"RPT-{prediction.id:05d}"
    gen_time = datetime.utcnow().strftime("%B %d, %Y · %I:%M %p UTC")

    header_left = [
        Paragraph("<b>MEDISCAN PRO</b>", title_style),
        Paragraph("AI-POWERED CLINICAL RISK ASSESSMENT REPORT", subtitle_style),
        Paragraph("Secure Healthcare Intelligence System", body_style),
    ]

    header_right = [
        Paragraph(f"<b>Report ID:</b> {report_id}", bold_label),
        Paragraph(f"<b>Generated:</b> {gen_time}", body_style),
        Paragraph(f"<b>Status:</b> Completed & Verified", body_style),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[330, 190]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0891b2'), spaceBefore=4, spaceAfter=10))

    # ── 2. PATIENT INFORMATION SECTION ────────────────────────
    story.append(Paragraph("PATIENT DEMOGRAPHICS & CLINICAL VITALS", section_heading))

    age_str = f"{user.age} years" if user.age else "Not provided"
    gender_str = user.gender if user.gender else "Not specified"
    height_str = f"{user_profile.height_cm} cm" if (user_profile and user_profile.height_cm) else "—"
    weight_str = f"{user_profile.weight_kg} kg" if (user_profile and user_profile.weight_kg) else "—"

    if user_profile and user_profile.bmi:
        bmi_cat = user.bmi_category['label']
        bmi_str = f"<b>{user_profile.bmi}</b> ({bmi_cat})"
    else:
        bmi_str = "—"

    blood_str = user_profile.blood_group if (user_profile and user_profile.blood_group) else "—"
    activity_str = user_profile.activity_level if (user_profile and user_profile.activity_level) else "—"

    patient_data = [
        [
            Paragraph("<b>Full Name:</b>", bold_label), Paragraph(user.full_name, value_text),
            Paragraph("<b>Patient Email:</b>", bold_label), Paragraph(user.email, value_text)
        ],
        [
            Paragraph("<b>Age:</b>", bold_label), Paragraph(age_str, value_text),
            Paragraph("<b>Gender:</b>", bold_label), Paragraph(gender_str, value_text)
        ],
        [
            Paragraph("<b>Height:</b>", bold_label), Paragraph(height_str, value_text),
            Paragraph("<b>Weight:</b>", bold_label), Paragraph(weight_str, value_text)
        ],
        [
            Paragraph("<b>BMI (Body Mass Index):</b>", bold_label), Paragraph(bmi_str, value_text),
            Paragraph("<b>Blood Group:</b>", bold_label), Paragraph(blood_str, value_text)
        ]
    ]

    patient_table = Table(patient_data, colWidths=[120, 140, 110, 150])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))

    # ── 3. PREDICTION VERDICT CARD ────────────────────────────
    story.append(Paragraph("PREDICTION ASSESSMENT SUMMARY", section_heading))

    risk_level = prediction.risk_level or 'Low'
    confidence = prediction.confidence_pct or 0.0

    if risk_level == 'High':
        risk_bg = colors.HexColor('#fee2e2')
        risk_border = colors.HexColor('#ef4444')
        risk_color_name = '#b91c1c'
    elif risk_level == 'Moderate':
        risk_bg = colors.HexColor('#fef3c7')
        risk_border = colors.HexColor('#f59e0b')
        risk_color_name = '#b45309'
    else:
        risk_bg = colors.HexColor('#dcfce7')
        risk_border = colors.HexColor('#22c55e')
        risk_color_name = '#15803d'

    verdict_title = ParagraphStyle(
        'VerdictTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor(risk_color_name)
    )

    verdict_sub = ParagraphStyle(
        'VerdictSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937')
    )

    verdict_card_data = [
        [
            Paragraph(f"<b>Evaluated Disease Module:</b> {prediction.disease_name}", bold_label),
            Paragraph(f"<b>Assessment Date:</b> {prediction.created_at.strftime('%B %d, %Y · %I:%M %p')}", bold_label)
        ],
        [
            Paragraph(f"Risk Classification: <b>{risk_level.upper()} RISK</b>", verdict_title),
            Paragraph(f"Model Result: <b>{prediction.result}</b>", verdict_title)
        ],
        [
            Paragraph(
                f"Calibrated Risk Probability: <b>{confidence:.1f}%</b> &nbsp;|&nbsp; "
                f"Methodology: <b>{prediction.model_used or 'Clinical Ensemble'}</b>",
                verdict_sub
            ),
            Paragraph(
                "Classification based on validated clinical parameters & ML screening models.",
                verdict_sub
            )
        ]
    ]

    verdict_table = Table(verdict_card_data, colWidths=[260, 260])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_bg),
        ('BOX', (0, 0), (-1, -1), 1, risk_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, risk_border),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, risk_border),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 10))

    # ── 4. CLINICAL PARAMETERS TABLE ──────────────────────────
    story.append(Paragraph("CLINICAL PARAMETERS ANALYZED", section_heading))

    import json
    try:
        input_data = json.loads(prediction.input_data or '{}')
    except Exception:
        input_data = {}

    param_rows = [
        [
            Paragraph("<b>Parameter</b>", bold_label),
            Paragraph("<b>Recorded Value</b>", bold_label),
            Paragraph("<b>Clinical Relevance</b>", bold_label)
        ]
    ]

    for key, value in input_data.items():
        label = key.replace('_', ' ').title()
        val_str = f"<b>{value}</b>"
        relevance = "Standard model predictor parameter"
        param_rows.append([
            Paragraph(label, value_text),
            Paragraph(val_str, value_text),
            Paragraph(relevance, body_style)
        ])

    if len(param_rows) > 1:
        param_table = Table(param_rows, colWidths=[180, 110, 230])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2744')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 1), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        # Style headers in white
        for c in range(3):
            param_rows[0][c].style.textColor = colors.white
        story.append(param_table)
    else:
        story.append(Paragraph("No input parameters recorded.", body_style))

    story.append(Spacer(1, 10))

    # ── 5. EDUCATIONAL INSIGHTS & WELLNESS ACTIONS ────────────
    if insights:
        story.append(Paragraph("EDUCATIONAL HEALTH INSIGHTS & ACTIONS", section_heading))
        story.append(Paragraph(insights.get('summary', ''), body_style))
        story.append(Spacer(1, 4))

        recs = insights.get('recommendations', [])
        if recs:
            story.append(Paragraph("<b>Recommended Wellness Actions:</b>", bold_label))
            for item in recs[:4]:
                story.append(Paragraph(f"• {item}", bullet_style))
            story.append(Spacer(1, 4))

        questions = insights.get('questions_for_doctor', [])
        if questions:
            story.append(Paragraph("<b>Informed Questions to Discuss with Your Physician:</b>", bold_label))
            for q in questions[:3]:
                story.append(Paragraph(f"• {q}", bullet_style))
            story.append(Spacer(1, 6))

    # ── 6. OFFICIAL CLINICAL DISCLAIMER BOX ───────────────────
    disclaimer_text = (
        "<b>IMPORTANT CLINICAL & LEGAL DISCLAIMER:</b><br/>"
        "This health report is generated by an automated machine-learning screening algorithm intended exclusively "
        "for academic, wellness-tracking, and educational screening purposes. It DOES NOT constitute a formal medical diagnosis, "
        "prescriptive advice, or medical intervention. Physiological conditions can only be confirmed through diagnostic "
        "evaluations conducted by a licensed healthcare provider. Never discontinue or adjust prescribed treatments without "
        "direct physician consultation. If you are experiencing acute, severe, or emergency symptoms, immediately call your "
        "local emergency services or visit the nearest emergency healthcare facility."
    )

    disclaimer_box = Table(
        [[Paragraph(disclaimer_text, disclaimer_style)]],
        colWidths=[520]
    )
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(KeepTogether([disclaimer_box]))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
