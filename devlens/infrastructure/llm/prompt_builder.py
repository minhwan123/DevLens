from devlens.domain.models import CareerRadarProfile, DeveloperProfile, Recommendation

_MAX_RECOMMENDATIONS_IN_PROMPT = 5

_RADAR_AXES = (
    "programming",
    "project_experience",
    "software_engineering",
    "deployment_devops",
    "documentation",
    "activity",
)


def build_career_commentary_prompt(
    profile: DeveloperProfile,
    radar: CareerRadarProfile,
    strengths: list[str],
    growth_areas: list[str],
    recommendations: list[Recommendation],
    roadmap: list[str],
) -> str:
    """Formats already-computed report data into a prompt.

    The LLM only writes prose from this — it never re-ranks, re-scores, or is asked to
    invent facts not present here. Skill evidence (source repos) is included explicitly so
    the model can cite them, per the "근거 repo 인용 포함" requirement.
    """
    skills_block = (
        "\n".join(
            f"- {skill.skill} ({skill.proficiency}) — 근거 저장소: "
            f"{', '.join(skill.source_repos) or 'n/a'}"
            for skill in profile.skills
        )
        or "(추출된 스킬 없음)"
    )

    radar_block = "\n".join(f"- {axis}: {getattr(radar, axis):.0f}/100" for axis in _RADAR_AXES)

    recommendations_block = (
        "\n".join(
            f"- [{rec.item.category}] {rec.item.name} (priority {rec.priority_score:.2f}): "
            f"{rec.item.description}"
            for rec in recommendations[:_MAX_RECOMMENDATIONS_IN_PROMPT]
        )
        or "(추천 항목 없음)"
    )

    roadmap_block = " -> ".join(roadmap) if roadmap else "(로드맵 없음)"

    return f"""당신은 신뢰할 수 있는 커리어 코치입니다. 아래는 한 개발자의 GitHub 분석 결과입니다.
이 데이터만 근거로 삼아 한국어로 3~5문단 분량의 분석 의견을 작성하세요. 새로운 점수나 사실을
만들어내지 말고, 스킬을 언급할 때는 반드시 아래에 주어진 근거 저장소 이름을 함께 인용하세요.

[목표 직무] {profile.career_goal}
[종합 레벨] {profile.project_level}
[활동 분야] {", ".join(profile.domains) or "(없음)"}

[역량 레이더 (0~100, 단일 총점 없음)]
{radar_block}

[보유 스킬 및 근거]
{skills_block}

[강점]
{", ".join(strengths) or "(뚜렷한 강점 없음)"}

[성장 필요 영역 (목표 직무 대비 부족하거나 약한 스킬)]
{", ".join(growth_areas) or "(없음)"}

[추천 항목 (이미 우선순위가 계산되어 있음 — 순서를 바꾸지 마세요)]
{recommendations_block}

[학습 로드맵 순서 (이미 결정되어 있음)]
{roadmap_block}

출력 형식: 마크다운 문단으로, 1) 전반적인 총평 2) 강점과 그 근거 3) 성장 필요 영역과 추천 항목이
어떻게 도움이 되는지 4) 로드맵을 그 순서대로 따라야 하는 이유 순서로 작성하세요."""
