import os
import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from devlens.application.generate_career_report import GenerateCareerReportResult

_RADAR_AXIS_LABELS: dict[str, str] = {
    "programming": "Programming",
    "project_experience": "Project Experience",
    "software_engineering": "Software Engineering",
    "deployment_devops": "Deployment & DevOps",
    "documentation": "Documentation",
    "activity": "Activity",
}
_HEADER_COLOR = colors.HexColor("#2a78d6")
_GRID_COLOR = colors.HexColor("#c3c2b7")

_KOREAN_BODY_FONT = "KoreanBody"
_KOREAN_HEADING_FONT = "KoreanHeading"
# (regular, bold) TTF pairs to try, in order — covers this dev machine (Windows) and a
# common Docker/Linux setup (`apt-get install fonts-nanum`). If embedded, the PDF renders
# identically in any viewer since the glyph outlines travel with the file.
_CANDIDATE_FONT_PAIRS = (
    (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf"),
    (
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    ),
)


def _register_korean_fonts() -> tuple[str, str]:
    """Most of this report's content (skip reasons, AI commentary) is Korean, and the 14
    standard PDF fonts (Helvetica, Times, ...) have no Korean glyphs.

    Prefers embedding a real Korean TTF (found on this machine or a common Docker image) so
    the PDF is self-contained and renders correctly everywhere. Falls back to reportlab's
    built-in CID font (ships with reportlab, no file needed) if none is found — text content
    is still correct and searchable either way, but the CID path relies on the PDF viewer
    itself having a Korean font to substitute for un-embedded glyphs.
    """
    for regular_path, bold_path in _CANDIDATE_FONT_PAIRS:
        if os.path.isfile(regular_path) and os.path.isfile(bold_path):
            pdfmetrics.registerFont(TTFont(_KOREAN_BODY_FONT, regular_path))
            pdfmetrics.registerFont(TTFont(_KOREAN_HEADING_FONT, bold_path))
            return _KOREAN_BODY_FONT, _KOREAN_HEADING_FONT
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
    return "HYSMyeongJo-Medium", "HYGothic-Medium"


_BODY_FONT, _HEADING_FONT = _register_korean_fonts()

_TableRow = list[str | Paragraph]


def _build_styles() -> StyleSheet1:
    styles = getSampleStyleSheet()
    for name in ("Title", "Heading2", "Heading3"):
        styles[name].fontName = _HEADING_FONT
    for name in ("Normal", "BodyText"):
        styles[name].fontName = _BODY_FONT
    return styles


def build_pdf_report(result: GenerateCareerReportResult, username: str, career_goal: str) -> bytes:
    """Renders GenerateCareerReportResult into a downloadable PDF (no chart image — the radar
    is shown as a table here; the interactive chart lives in the Streamlit UI)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = _build_styles()
    profile = result.profile
    story: list[Flowable] = [
        Paragraph(f"DevLens Career Report — {username}", styles["Title"]),
        Paragraph(f"Target role: {career_goal}", styles["Normal"]),
        Spacer(1, 12),
    ]

    if result.partial:
        story.append(
            Paragraph(
                "⚠ GitHub API 요청 한도로 인해 일부 저장소만 분석된 부분(partial) 결과입니다.",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

    story.append(Paragraph("Developer Summary", styles["Heading2"]))
    story.append(Paragraph(f"Project level: {profile.project_level}", styles["Normal"]))
    story.append(Paragraph(f"Domains: {', '.join(profile.domains) or '-'}", styles["Normal"]))
    story.append(
        Paragraph(f"Repositories analyzed: {len(profile.repository_evidences)}", styles["Normal"])
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Career Radar (0-100, no single aggregate score)", styles["Heading2"]))
    radar_rows: list[_TableRow] = [["Axis", "Score"]]
    for key, label in _RADAR_AXIS_LABELS.items():
        radar_rows.append([label, f"{getattr(result.radar, key):.0f}"])
    story.append(_styled_table(radar_rows))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Best-Fit Roles", styles["Heading2"]))
    role_fit_rows: list[_TableRow] = [["Role", "Fit", "Matched skills"]]
    for fit in result.role_fit:
        role_fit_rows.append(
            [fit.role, f"{fit.fit_score * 100:.0f}%", _wrap(", ".join(fit.matched_skills), styles)]
        )
    if len(role_fit_rows) == 1:
        role_fit_rows.append(["(none)", "", ""])
    story.append(_styled_table(role_fit_rows, col_widths=[3.5 * cm, 2 * cm, 9.5 * cm]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Strengths", styles["Heading2"]))
    story.append(_bullet_list(result.strengths or ["(none identified)"], styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Growth Areas", styles["Heading2"]))
    story.append(_bullet_list(result.growth_areas or ["(none)"], styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Improvement Suggestions", styles["Heading2"]))
    suggestion_lines = [
        f"[{suggestion.repo_name}] {suggestion.message}" for suggestion in result.suggestions
    ]
    story.append(_bullet_list(suggestion_lines or ["(none)"], styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Skills", styles["Heading2"]))
    skill_rows: list[_TableRow] = [["Skill", "Proficiency", "Evidence repos"]]
    for skill in profile.skills:
        skill_rows.append(
            [skill.skill, skill.proficiency, _wrap(", ".join(skill.source_repos), styles)]
        )
    story.append(_styled_table(skill_rows, col_widths=[3.5 * cm, 3 * cm, 8.5 * cm]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Repository Filter Results", styles["Heading2"]))
    filter_rows: list[_TableRow] = [["Repository", "Admitted", "Reason"]]
    for filter_result in result.filter_results:
        filter_rows.append(
            [
                filter_result.repo_name,
                "Yes" if filter_result.accepted else "No",
                _wrap(filter_result.reason, styles),
            ]
        )
    story.append(_styled_table(filter_rows, col_widths=[3.5 * cm, 2.5 * cm, 9 * cm]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Recommendations", styles["Heading2"]))
    rec_rows: list[_TableRow] = [["Category", "Name", "Priority"]]
    for rec in result.recommendations.recommendations:
        rec_rows.append([rec.item.category, rec.item.name, f"{rec.priority_score:.2f}"])
    story.append(_styled_table(rec_rows))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Learning Roadmap", styles["Heading2"]))
    roadmap_text = " → ".join(result.recommendations.roadmap) or "(none)"
    story.append(Paragraph(roadmap_text, styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("AI Analysis", styles["Heading2"]))
    story.extend(_markdown_lite_to_flowables(result.ai_commentary, styles))

    doc.build(story)
    return buffer.getvalue()


def _styled_table(rows: list[_TableRow], col_widths: list[float] | None = None) -> Table:
    table = Table(rows, hAlign="LEFT", colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), _HEADING_FONT),
                ("FONTNAME", (0, 1), (-1, -1), _BODY_FONT),
                ("GRID", (0, 0), (-1, -1), 0.5, _GRID_COLOR),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _bullet_list(items: list[str], styles: StyleSheet1) -> ListFlowable:
    list_items = [ListItem(Paragraph(item, styles["Normal"])) for item in items]
    return ListFlowable(list_items, bulletType="bullet")  # type: ignore[arg-type]


def _wrap(text: str, styles: StyleSheet1) -> Paragraph:
    return Paragraph(text, styles["Normal"])


def _markdown_lite_to_flowables(text: str, styles: StyleSheet1) -> list[Flowable]:
    """Minimal **bold** / #heading handling for Gemini's markdown-flavored output.

    Not a full markdown parser — just enough to render the AI commentary readably without
    pulling in a markdown dependency for a handful of tags.
    """
    flowables: list[Flowable] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            flowables.append(Paragraph(block.lstrip("#").strip(), styles["Heading3"]))
            continue
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", block).replace("\n", "<br/>")
        flowables.append(Paragraph(html, styles["BodyText"]))
        flowables.append(Spacer(1, 6))
    return flowables
