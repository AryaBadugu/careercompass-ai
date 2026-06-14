"""
FastAPI backend — connects React frontend to Azure AI Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import CareerCompassAgent
import csv
from datetime import datetime
import html
import json
import math
import re
import time
import traceback
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

app = FastAPI(title="CareerCompass AI API")

# Allow React to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Create agent once (not on every request — saves money)
print("Loading CareerCompass Agent...")
career_agent = CareerCompassAgent()
print("✅ Agent ready!")


class ProfileRequest(BaseModel):
    profile: str  # User's profile description


@app.get("/")
def root():
    return {"status": "CareerCompass AI is running ✅"}


@app.post("/analyze")
async def analyze_profile(request: ProfileRequest):
    """
    Main endpoint: takes user profile, returns 6-step analysis
    """
    if not request.profile or len(request.profile) < 20:
        raise HTTPException(status_code=400, detail="Please describe your profile in more detail")
    
    try:
        result = career_agent.analyze_profile(request.profile)
        return {
            "success": True,
            "steps": result["steps"],
            "full_response": result["full_response"],
            "steps_completed": result["steps_completed"]
        }
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
class FeedbackRequest(BaseModel):
    original_profile: str
    feedback: str

@app.post("/regenerate")
async def regenerate_with_feedback(request: FeedbackRequest):
    """
    User gives feedback → agent re-analyzes
    Shows adaptive reasoning
    """
    try:
        result = career_agent.regenerate_ranking(
            request.original_profile,
            request.feedback
        )
        return {
            "success": True,
            "regenerated_response": result["regenerated_response"],
            "feedback_applied": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ComparisonRequest(BaseModel):
    career1: str
    career2: str


class MarketDemandRequest(BaseModel):
    skills: list[str]


@app.post("/compare")
async def compare_careers(request: ComparisonRequest):
    """Compare two career paths"""
    try:
        result = career_agent.compare_two_careers(
            request.career1,
            request.career2
        )
        return {
            "success": True,
            "comparison": result["comparison"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _fetch_public_json(url: str, headers: dict | None = None, timeout: int = 10) -> dict | None:
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read().decode(charset)
            return json.loads(payload)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


_MARKET_CACHE: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, object]] = {}


def _fetch_public_json_cached(url: str, headers: dict | None = None, timeout: int = 10, ttl: int = 3600):
    header_items = tuple(sorted((headers or {}).items()))
    cache_key = (url, header_items)
    cached = _MARKET_CACHE.get(cache_key)
    now = time.time()

    if cached and now - cached[0] < ttl:
        return cached[1]

    payload = _fetch_public_json(url, headers=headers, timeout=timeout)
    _MARKET_CACHE[cache_key] = (now, payload)
    return payload


def _normalize_skill_query(skill: str) -> str:
    normalized = skill.strip().lower()
    alias_map = {
        "ui/ux": "ui ux",
        "ux/ui": "ui ux",
        "ai/ml": "ai ml",
        "node.js": "node js",
        "next.js": "next js",
        "react.js": "react js",
        "c#": "c sharp",
        "c++": "cpp",
        "fullstack": "full stack",
        "machine learning": "machine learning",
        "data analysis": "data analysis",
    }
    if normalized in alias_map:
        return alias_map[normalized]

    cleaned = re.sub(r"[^a-z0-9]+", " ", normalized)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or normalized


def _strip_html(text: str) -> str:
    """Remove HTML tags from text to improve keyword matching."""
    if not text:
        return ""
    stripped = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", stripped).strip()


def _skill_variants(skill: str) -> list[str]:
    normalized = skill.strip().lower()
    base = _normalize_skill_query(skill)
    alias_sets = {
        "ui/ux": ["ui ux", "ux", "ui design", "product design"],
        "ai/ml": ["ai ml", "machine learning", "artificial intelligence", "llm"],
        "node.js": ["node js", "nodejs", "javascript"],
        "next.js": ["next js", "nextjs", "react"],
        "react.js": ["react js", "reactjs", "frontend"],
        "c#": ["c sharp", "dotnet", ".net"],
        "c++": ["cpp", "c plus plus"],
        "devops": ["devops", "platform engineering", "sre", "cloud"],
        "data analysis": ["data analysis", "analytics", "business intelligence", "bi"],
        "full stack": ["full stack", "fullstack", "frontend backend"],
    }

    variants = [skill.strip(), normalized, base]
    variants.extend(alias_sets.get(normalized, []))

    unique_variants = []
    seen = set()
    for variant in variants:
        cleaned = variant.strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique_variants.append(cleaned)
    return unique_variants


def _extract_job_records(payload) -> list[dict]:
    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict) and payload[0].get("legal"):
            return [item for item in payload[1:] if isinstance(item, dict)]
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("jobs", "data", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def _job_record_text(record: dict) -> str:
    raw_desc = str(record.get("description", ""))
    categories = record.get("categories", [])
    parts = [
        str(record.get("title", "")),
        str(record.get("position", "")),
        str(record.get("company_name", record.get("companyName", record.get("company", "")))),
        " ".join(str(tag) for tag in record.get("tags", []) if tag),
        " ".join(str(cat) for cat in categories if cat) if isinstance(categories, list) else "",
        _strip_html(raw_desc),
        str(record.get("location", "")),
        str(record.get("candidate_required_location", "")),
        str(record.get("excerpt", "")),
    ]
    return " ".join(parts).lower()


def _count_matching_records(records: list[dict], variants: list[str]) -> tuple[int, list[dict]]:
    matches = []
    seen_keys = set()

    for record in records:
        text = _job_record_text(record)
        if not any(variant in text for variant in variants):
            continue

        key = record.get("url") or record.get("apply_url") or record.get("slug") or record.get("id")
        if key in seen_keys:
            continue

        seen_keys.add(key)
        matches.append(record)

    return len(matches), matches


def _format_role_sample(record: dict, source: str) -> str:
    title = str(record.get("title") or record.get("position") or "Role").strip()
    company = str(record.get("company_name") or record.get("company") or "").strip()
    role = title if not company else f"{title} · {company}"
    return f"{role} ({source})"


def _estimate_market_demand(skills: list[str]) -> dict:
    insights = []
    remote_ok_payload = _fetch_public_json_cached(
        "https://remoteok.com/api",
        headers={"Accept": "application/json", "User-Agent": "CareerCompass-AI"},
    )
    remote_ok_records = _extract_job_records(remote_ok_payload)

    for raw_skill in skills[:8]:
        skill = raw_skill.strip()
        if not skill:
            continue

        variants = _skill_variants(skill)
        search_term = quote_plus(_normalize_skill_query(skill) or skill)

        # --- Himalayas API (server-side search — the key data source) ---
        himalayas_url = f"https://himalayas.app/jobs/api/search?q={search_term}&limit=10"
        himalayas_data = _fetch_public_json_cached(
            himalayas_url,
            headers={"Accept": "application/json", "User-Agent": "CareerCompass-AI"}
        )
        himalayas_total_count = 0
        himalayas_matches: list[dict] = []
        if isinstance(himalayas_data, dict):
            himalayas_total_count = int(himalayas_data.get("totalCount", 0))
            himalayas_matches = himalayas_data.get("jobs", [])
            if not isinstance(himalayas_matches, list):
                himalayas_matches = []

        # --- Other job board APIs ---
        remotive_url = f"https://remotive.com/api/remote-jobs?search={search_term}"
        arbeitnow_url = f"https://www.arbeitnow.com/api/job-board-api?search={search_term}&remote=true"
        github_url = (
            "https://api.github.com/search/repositories"
            f"?q={quote_plus(skill + ' in:name,description,readme')}&per_page=1"
        )

        headers = {"Accept": "application/json", "User-Agent": "CareerCompass-AI"}
        remotive_data = _fetch_public_json_cached(remotive_url, headers=headers)
        arbeitnow_data = _fetch_public_json_cached(arbeitnow_url, headers=headers)
        github_data = _fetch_public_json_cached(
            github_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "CareerCompass-AI"
            }
        )

        remotive_records = _extract_job_records(remotive_data)
        arbeitnow_records = _extract_job_records(arbeitnow_data)
        remotive_jobs_count, remotive_matches = _count_matching_records(remotive_records, variants)
        arbeitnow_jobs_count, arbeitnow_matches = _count_matching_records(arbeitnow_records, variants)
        remote_ok_jobs_count, remote_ok_matches = _count_matching_records(remote_ok_records, variants)
        github_repo_count = (
            int(github_data.get("total_count", 0))
            if isinstance(github_data, dict) and isinstance(github_data.get("total_count", 0), int)
            else 0
        )

        # --- Sample roles from all sources ---
        sampled_titles = []
        seen_titles = set()
        for source_name, job_list in (
            ("Himalayas", himalayas_matches),
            ("Remotive", remotive_matches),
            ("RemoteOK", remote_ok_matches),
            ("Arbeitnow", arbeitnow_matches),
        ):
            for job in job_list[:3]:
                title = _format_role_sample(job, source_name)
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    sampled_titles.append(title)
                if len(sampled_titles) >= 6:
                    break
            if len(sampled_titles) >= 6:
                break

        # --- Scoring inputs ---
        board_postings = remotive_jobs_count + arbeitnow_jobs_count + remote_ok_jobs_count
        total_live_postings = board_postings + len(himalayas_matches)
        source_hits = sum(1 for value in (
            remotive_jobs_count, arbeitnow_jobs_count, remote_ok_jobs_count, len(himalayas_matches)
        ) if value > 0)

        freshness_bonus = 0
        all_recent = remotive_matches[:5] + arbeitnow_matches[:5] + remote_ok_matches[:5]
        for record in all_recent:
            date_value = str(record.get("publication_date") or record.get("date") or record.get("created_at") or "")
            if date_value[:4].isdigit() and int(date_value[:4]) >= 2025:
                freshness_bonus += 1
        # Himalayas records use epoch timestamps (pubDate)
        import time as _time
        cutoff_epoch = _time.time() - 90 * 86400  # last 90 days
        for record in himalayas_matches[:5]:
            pub_date = record.get("pubDate", 0)
            if isinstance(pub_date, (int, float)) and pub_date > cutoff_epoch:
                freshness_bonus += 1
        freshness_bonus = min(freshness_bonus * 2, 15)

        # --- Demand score formula (recalibrated) ---
        live_component = min(total_live_postings * 3, 40)
        himalayas_component = min(math.log10(himalayas_total_count + 1) * 15, 30) if himalayas_total_count > 0 else 0
        breadth_bonus = source_hits * 5
        repo_component = min(math.log10(github_repo_count + 1) * 8, 20)

        quality_floor = 15 if github_repo_count else 0
        if total_live_postings > 0:
            quality_floor = max(quality_floor, 30)

        demand_score = min(100, int(
            quality_floor + live_component + himalayas_component + breadth_bonus + repo_component + freshness_bonus
        ))

        if total_live_postings == 0 and github_repo_count > 0:
            demand_score = min(100, max(demand_score, 28 + int(repo_component)))
        if total_live_postings > 0:
            demand_score = max(demand_score, 35)
        if himalayas_total_count >= 50:
            demand_score = max(demand_score, 55)
        if himalayas_total_count >= 200:
            demand_score = max(demand_score, 70)

        if demand_score >= 70:
            demand_band = "High"
        elif demand_score >= 55:
            demand_band = "Moderate"
        elif demand_score >= 38:
            demand_band = "Emerging"
        else:
            demand_band = "Watch"

        insight = {
            "skill": skill,
            "demand_score": demand_score,
            "demand_band": demand_band,
            "job_postings": total_live_postings,
            "himalayas_total_count": himalayas_total_count,
            "github_repositories": github_repo_count,
            "sample_roles": sampled_titles,
            "signal_quality": (
                "Strong" if source_hits >= 3 and github_repo_count > 0
                else "Good" if source_hits >= 2 or himalayas_total_count > 20
                else "Partial"
            ),
            "source_breakdown": {
                "Himalayas": himalayas_total_count,
                "RemoteOK": remote_ok_jobs_count,
                "Remotive": remotive_jobs_count,
                "Arbeitnow": arbeitnow_jobs_count,
            },
            "freshness_bonus": freshness_bonus,
        }
        insights.append(insight)

    insights.sort(key=lambda item: item["demand_score"], reverse=True)
    average_score = int(sum(item["demand_score"] for item in insights) / len(insights)) if insights else 0
    strongest = insights[0]["skill"] if insights else "N/A"

    return {
        "analyzed_skills": len(insights),
        "average_demand_score": average_score,
        "strongest_market_skill": strongest,
        "skill_insights": insights,
        "methodology": (
            "Demand score combines server-side job search results from Himalayas (~98K global jobs), "
            "live public job-board matches from RemoteOK, Remotive, and Arbeitnow, "
            "with GitHub repository activity and recency signals."
        )
    }


@app.post("/market-demand")
async def market_demand(request: MarketDemandRequest):
    """
    Analyze live market demand for selected skills using public APIs.
    """
    cleaned = []
    seen = set()
    for skill in request.skills:
        normalized = skill.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)

    if not cleaned:
        raise HTTPException(status_code=400, detail="Please provide at least one valid skill")

    try:
        demand_report = _estimate_market_demand(cleaned)
        return {
            "success": True,
            **demand_report,
            "sources": [
                "Himalayas Remote Jobs API (server-side search)",
                "RemoteOK Public API",
                "Remotive Jobs API",
                "Arbeitnow Job Board API",
                "GitHub Search API"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse
import uuid


def _normalize_step_output(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"^STEP\s+\d+\s+COMPLETE:\s*", "", text.strip(), flags=re.IGNORECASE)


def _extract_step_outputs(steps: list) -> dict:
    return {item.get("step"): _normalize_step_output(item.get("output", "")) for item in steps}


def _parse_bracket_list(value: str) -> list:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_profile_summary(step_text: str) -> dict:
    skills_match = re.search(r"Skills=\[(.*?)\]", step_text, flags=re.IGNORECASE)
    goals_match = re.search(r"Goals=\[(.*?)\]", step_text, flags=re.IGNORECASE)
    education_match = re.search(r"Education=(.*?)(?:,\s*Experience=|$)", step_text, flags=re.IGNORECASE)
    experience_match = re.search(r"Experience=(.*)$", step_text, flags=re.IGNORECASE)

    return {
        "skills": _parse_bracket_list(skills_match.group(1)) if skills_match else [],
        "goals": _parse_bracket_list(goals_match.group(1)) if goals_match else [],
        "education": education_match.group(1).strip() if education_match else "",
        "experience": experience_match.group(1).strip() if experience_match else "",
    }


def _parse_career_list(step_text: str) -> list:
    careers_match = re.search(r"\[(.*?)\]", step_text)
    return _parse_bracket_list(careers_match.group(1)) if careers_match else []


def _parse_gap_lines(step_text: str) -> list:
    rows = []
    for line in step_text.split("\n"):
        cleaned = line.strip()
        if not cleaned.startswith("-"):
            continue
        stripped = re.sub(r"^-\s*", "", cleaned)
        if ":" in stripped:
            title, detail = stripped.split(":", 1)
            rows.append({"title": title.strip(), "detail": detail.strip()})
        else:
            rows.append({"title": "Skill Gap", "detail": stripped})
    return rows


def _parse_rankings(step_text: str) -> list:
    ranking_match = re.search(r"\[(.*?)\]", step_text)
    if not ranking_match:
        return []

    rankings = []
    for entry in ranking_match.group(1).split(","):
        item = entry.strip()
        if not item or ":" not in item:
            continue
        title, score_text = item.split(":", 1)
        score_match = re.search(r"(\d+)\s*/\s*10", score_text.strip())
        score = int(score_match.group(1)) if score_match else 0
        rankings.append(
            {
                "title": title.strip(),
                "score_text": score_text.strip(),
                "score": score,
            }
        )
    return rankings


def _parse_roadmap_items(step_text: str) -> list:
    roadmap_items = []
    for line in step_text.split("\n"):
        cleaned = line.strip()
        if not cleaned:
            continue
        if re.match(r"^[-*]\s+", cleaned):
            roadmap_items.append(re.sub(r"^[-*]\s+", "", cleaned))
            continue
        if re.match(r"^\d+[.)]\s+", cleaned):
            roadmap_items.append(re.sub(r"^\d+[.)]\s+", "", cleaned))
    return roadmap_items


def _safe_paragraph_text(text: str) -> str:
    return html.escape(text).replace("\n", "<br/>")

@app.post("/export-pdf")
async def export_career_plan(request: ProfileRequest):
    """
    Generate PDF of career plan
    """
    try:
        result = career_agent.analyze_profile(request.profile)
        step_outputs = _extract_step_outputs(result.get("steps", []))
        profile_summary = _parse_profile_summary(step_outputs.get(1, ""))
        careers = _parse_career_list(step_outputs.get(2, ""))
        gaps = _parse_gap_lines(step_outputs.get(3, ""))
        rankings = _parse_rankings(step_outputs.get(4, ""))
        roadmap_items = _parse_roadmap_items(step_outputs.get(5, ""))
        best_path = rankings[0]["title"] if rankings else "Not available"
        best_score = rankings[0]["score_text"] if rankings else "N/A"
        top_gap = gaps[0]["title"] if gaps else "Not available"
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )
        styles = getSampleStyleSheet()
        story = []
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0b5ea8'),
            spaceAfter=8,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=10,
            spaceAfter=8,
        )
        content_style = ParagraphStyle(
            'Content',
            parent=styles['BodyText'],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor('#111827'),
            spaceAfter=8,
        )
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=colors.HexColor('#475569'),
            spaceAfter=8,
        )
        
        story.append(Paragraph("CareerCompass AI - Career Strategy Report", title_style))
        story.append(
            Paragraph(
                f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')} | 6-step reasoning dossier",
                subtitle_style,
            )
        )

        summary_table = Table(
            [
                ["Best Path", best_path],
                ["Opportunity Score", best_score],
                ["Top Priority Skill Gap", top_gap],
                ["Total Recommended Paths", str(len(careers))],
            ],
            colWidths=[2.2 * inch, 4.5 * inch],
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#e0f2fe')),
                    ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#f8fafc')),
                    ('TEXTCOLOR', (0, 0), (1, -1), colors.HexColor('#0f172a')),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#94a3b8')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.16 * inch))

        story.append(Paragraph("User Profile Snapshot", section_style))
        story.append(Paragraph(f"<b>Education:</b> {_safe_paragraph_text(profile_summary.get('education', 'Not provided'))}", content_style))
        story.append(Paragraph(f"<b>Experience:</b> {_safe_paragraph_text(profile_summary.get('experience', 'Not provided'))}", content_style))
        story.append(Paragraph(f"<b>Skills:</b> {_safe_paragraph_text(', '.join(profile_summary.get('skills', [])) or 'Not provided')}", content_style))
        story.append(Paragraph(f"<b>Goals:</b> {_safe_paragraph_text(', '.join(profile_summary.get('goals', [])) or 'Not provided')}", content_style))

        if rankings:
            story.append(Paragraph("Opportunity Ranking", section_style))
            ranking_table_data = [["Career Path", "Score", "Readiness"]]
            for rank in rankings:
                readiness = "Strong" if rank["score"] >= 8 else "Promising" if rank["score"] >= 6 else "Emerging"
                ranking_table_data.append([rank["title"], rank["score_text"], readiness])

            ranking_table = Table(ranking_table_data, colWidths=[3.6 * inch, 1.0 * inch, 1.7 * inch])
            ranking_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 7),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(ranking_table)

        if gaps:
            story.append(Paragraph("Key Skill Gaps", section_style))
            for idx, gap in enumerate(gaps[:8], start=1):
                story.append(Paragraph(f"<b>{idx}. {html.escape(gap['title'])}</b>", content_style))
                story.append(Paragraph(_safe_paragraph_text(gap['detail']), content_style))

        if roadmap_items:
            story.append(Paragraph("Roadmap Highlights", section_style))
            for idx, item in enumerate(roadmap_items[:10], start=1):
                story.append(Paragraph(f"{idx}. {_safe_paragraph_text(item)}", content_style))

        story.append(PageBreak())
        story.append(Paragraph("Detailed 6-Step Reasoning Log", section_style))
        story.append(Paragraph("The following section contains the complete outputs generated for each reasoning step.", meta_style))

        for step in result.get("steps", []):
            story.append(Paragraph(f"<b>Step {step['step']}: {html.escape(step['name'])}</b>", section_style))
            story.append(Paragraph(_safe_paragraph_text(_normalize_step_output(step.get("output", ""))), content_style))
            story.append(Spacer(1, 0.06 * inch))

        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph("Full Consolidated Response", section_style))
        story.append(Paragraph(_safe_paragraph_text(result.get('full_response', '')), content_style))
        
        doc.build(story)
        pdf_buffer.seek(0)

        filename = f"CareerCompass_Analysis_{uuid.uuid4().hex[:8]}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export-skills-checklist")
async def export_skills_checklist(request: ProfileRequest):
    """
    Generate CSV checklist of skills to learn
    """
    try:
        result = career_agent.analyze_profile(request.profile)
        step_outputs = _extract_step_outputs(result.get("steps", []))
        profile_summary = _parse_profile_summary(step_outputs.get(1, ""))
        careers = _parse_career_list(step_outputs.get(2, ""))
        gaps = _parse_gap_lines(step_outputs.get(3, ""))
        rankings = _parse_rankings(step_outputs.get(4, ""))
        roadmap_items = _parse_roadmap_items(step_outputs.get(5, ""))

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        writer.writerow(['CareerCompass Skills and Career Strategy Report', datetime.now().strftime('%Y-%m-%d')])
        writer.writerow(['Generated At', datetime.now().strftime('%H:%M:%S')])
        writer.writerow([])
        writer.writerow(['User Profile Input'])
        writer.writerow([request.profile])
        writer.writerow([])

        writer.writerow(['Executive Summary'])
        writer.writerow(['Top Recommended Path', rankings[0]['title'] if rankings else 'Not available'])
        writer.writerow(['Top Path Score', rankings[0]['score_text'] if rankings else 'N/A'])
        writer.writerow(['Education', profile_summary.get('education', 'Not provided')])
        writer.writerow(['Experience', profile_summary.get('experience', 'Not provided')])
        writer.writerow(['Skills', '; '.join(profile_summary.get('skills', [])) or 'Not provided'])
        writer.writerow(['Goals', '; '.join(profile_summary.get('goals', [])) or 'Not provided'])
        writer.writerow([])

        writer.writerow(['Recommended Career Paths'])
        writer.writerow(['Career Path'])
        for career in careers:
            writer.writerow([career])
        writer.writerow([])

        writer.writerow(['Opportunity Ranking'])
        writer.writerow(['Career Path', 'Score', 'Readiness'])
        for rank in rankings:
            readiness = 'Strong' if rank['score'] >= 8 else 'Promising' if rank['score'] >= 6 else 'Emerging'
            writer.writerow([rank['title'], rank['score_text'], readiness])
        writer.writerow([])

        writer.writerow(['Skills Gap Checklist'])
        writer.writerow(['Career Path', 'Gap Detail', 'Status'])
        for gap in gaps:
            writer.writerow([gap['title'], gap['detail'], 'Not Started'])
        if not gaps:
            writer.writerow(['General', 'No explicit gaps parsed from step output', 'Review Manually'])
        writer.writerow([])

        writer.writerow(['Roadmap Action Items'])
        writer.writerow(['Action Item', 'Status'])
        for item in roadmap_items:
            writer.writerow([item, 'Not Started'])
        if not roadmap_items:
            writer.writerow(['Review roadmap section in analysis output', 'Pending'])
        writer.writerow([])

        writer.writerow(['Detailed Step Outputs'])
        writer.writerow(['Step', 'Step Name', 'Output'])
        for step in result.get('steps', []):
            writer.writerow([step.get('step', ''), step.get('name', ''), _normalize_step_output(step.get('output', ''))])

        csv_content = csv_buffer.getvalue()
        filename = f"CareerCompass_Skills_{uuid.uuid4().hex[:8]}.csv"

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown():
    career_agent.cleanup()