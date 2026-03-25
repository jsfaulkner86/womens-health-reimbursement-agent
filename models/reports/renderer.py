import os
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from models.schemas import ReimbursementPathwayReport

TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path("output/reports")


def render_pdf(report: ReimbursementPathwayReport) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("investor_brief.html")

    html_content = template.render(
        report=report,
        generated_at=report.generated_at.strftime("%B %d, %Y"),
        risk_color={
            "low": "#22c55e",
            "medium": "#f59e0b",
            "high": "#ef4444",
            "speculative": "#7c3aed",
        }.get(report.investor_risk_rating.value, "#6b7280"),
    )

    slug = report.company_name.lower().replace(" ", "_")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    html_path = OUTPUT_DIR / f"{slug}_{ts}.html"
    pdf_path = OUTPUT_DIR / f"{slug}_{ts}.pdf"

    html_path.write_text(html_content, encoding="utf-8")

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(str(pdf_path))
    except ImportError:
        pass

    return pdf_path
