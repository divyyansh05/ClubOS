from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "clubos_work_plan_revised.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=8,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
        )
    )
    return styles


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = letter

    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, height - 0.78 * inch, width - doc.rightMargin, height - 0.78 * inch)

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#0F172A"))
    canvas.drawString(doc.leftMargin, height - 0.62 * inch, "ClubOS Work Plan")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(width - doc.rightMargin, height - 0.62 * inch, "Off-Pitch Analytics | Group E")

    canvas.line(doc.leftMargin, 0.68 * inch, width - doc.rightMargin, 0.68 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(width / 2, 0.48 * inch, "Prepared for project submission - revised professional version")
    canvas.restoreState()


def bullet_list(items, styles, left_indent=14):
    return ListFlowable(
        [
            ListItem(Paragraph(item, styles["BodySmall"]), leftIndent=4)
            for item in items
        ],
        bulletType="bullet",
        leftIndent=left_indent,
        bulletFontName="Helvetica",
        bulletFontSize=9,
        bulletOffsetY=1,
        spaceBefore=2,
        spaceAfter=6,
    )


def build_story(styles):
    story = []

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Work Plan: Project ClubOS (Group E)", styles["CoverTitle"]))
    story.append(
        Paragraph(
            "A revised work plan for the Real Madrid Group E project, positioning ClubOS as a recurring digital business operating system rather than only a static dashboard deliverable.",
            styles["Subtle"],
        )
    )

    sections = [
        (
            "1. Project Identity",
            [
                "<b>Consultancy Name:</b> Off-Pitch Analytics",
                "<b>Product Name:</b> ClubOS",
                "<b>Project Theme:</b> Group E - Historical Digital Business Data",
            ],
        ),
        (
            "2. Project Objective",
            [
                "Off-Pitch Analytics proposes <b>ClubOS</b>, a recurring monthly digital business operating system for the club's business and digital teams.",
                "Rather than delivering only a static dashboard, the project will transform the provided historical datasets into a reusable product workflow that can be refreshed each month as new files arrive.",
                "The MVP will focus on four product modules: <b>Priority Board</b>, <b>Command Center</b>, <b>Peer Benchmark Engine</b>, and <b>Commercial Signal Engine</b>. A supporting reporting layer will also be prepared for the formal visualization requirement.",
            ],
        ),
        (
            "3. Delivery Approach",
            [
                "<b>Data Platform Workstream:</b> build a reproducible Databricks pipeline using a Bronze / Silver / Gold structure for recurring monthly refreshes",
                "<b>Product Workstream:</b> design and prototype the ClubOS application experience around a decision-support workflow, not a chart collection",
                "<b>Reporting Workstream:</b> prepare a clean companion BI layer for summary and drill-down reporting where required",
                "This keeps the project aligned with the official brief while extending it into a more advanced and reusable SaaS-style solution.",
            ],
        ),
        (
            "4. Roles and Responsibilities",
            [
                "<b>Divyansh Shrivastava - Data Platform & Product Engineering Lead:</b> Own Databricks setup, data contracts, pipeline logic, Gold outputs, and core product architecture",
                "<b>Carlos Pineda - Visualization & Interface Lead:</b> Support screen structure, visual consistency, reporting layout, and demo-facing UI refinement",
                "<b>Riccardo Lusiani - Project Lead & Business Strategy Lead:</b> Own delivery coordination, documentation, milestone tracking, review preparation, and final presentation narrative",
            ],
        ),
        (
            "5. 8-Week Activity Plan",
            [
                "<b>Weeks 1-2:</b> Audit source files and benchmark coverage; lock product scope, work plan, and screen blueprint; set up Databricks environment and repository structure",
                "<b>Weeks 3-4:</b> Build Bronze and Silver data layers; standardize recurring monthly ingestion logic; define KPI health and benchmark-ready outputs",
                "<b>Weeks 5-6:</b> Build Gold outputs for Priority Board, Command Center, Peer Benchmark, and Signal Engine; connect outputs to the product mockup and reporting layer",
                "<b>Week 7:</b> Integration, QA, usability refinement, and optional monthly briefing automation; validate recurring-upload readiness",
                "<b>Week 8:</b> Finalize technical documentation and rehearse the final executive presentation and demo flow",
            ],
        ),
        (
            "6. Main Deliverables",
            [
                "Reproducible Databricks pipeline for recurring monthly refresh",
                "ClubOS product prototype focused on decision support",
                "Supporting reporting layer for formal visualization needs",
                "Technical documentation and final executive presentation",
            ],
        ),
        (
            "7. Proposed Tutoring Schedule",
            [
                "<b>Session 1 (End of Week 2 - 45 min):</b> Validate scope, data interpretation, and product direction",
                "<b>Session 2 (End of Week 4 - 60 min):</b> Review Databricks pipeline structure, data model, and KPI logic",
                "<b>Session 3 (Mid-Week 6 - 60 min):</b> Review Priority Board, benchmark outputs, and reporting structure",
                "<b>Session 4 (Mid-Week 7 - 45 min):</b> Pre-delivery review, final feedback, and presentation rehearsal",
            ],
        ),
        (
            "8. Closing Note",
            [
                "This work plan is designed to keep the project both <b>academically aligned</b> with the official brief and <b>professionally ambitious</b> as a reusable product concept for the club's future digital business workflow."
            ],
        ),
    ]

    for title, items in sections:
        story.append(Paragraph(title, styles["Section"]))
        story.append(bullet_list(items, styles))

    return story


def build_pdf():
    styles = build_styles()

    doc = BaseDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.9 * inch,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="workplan", frames=[frame], onPage=header_footer)])
    doc.build(build_story(styles))
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
