"""Per-target-role skill/tag lookup table.

Shared by two domain policies that use it differently: SkillGapPolicy compares it against what
the developer profile already has (to find gaps), while CareerGoalRelevancePolicy matches it
against a recommendation item's tags regardless of the profile (rule-based tag matching).
"""

DEFAULT_ROLE_REQUIRED_SKILLS: dict[str, list[str]] = {
    "AI Engineer": ["Python", "PyTorch", "TensorFlow", "Scikit-learn", "Docker", "FastAPI", "SQL"],
    "Data Scientist": ["Python", "Pandas", "NumPy", "Scikit-learn", "SQL", "Statistics"],
    "Data Analyst": ["SQL", "Pandas", "Excel", "Tableau", "Statistics"],
    "Data Engineer": ["Python", "SQL", "Spark", "Airflow", "Docker", "PostgreSQL"],
    "Backend": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "Git"],
    "Frontend": ["JavaScript", "TypeScript", "React", "Next.js", "Git"],
    "DevOps": ["Docker", "Kubernetes", "Terraform", "CI/CD", "AWS", "Git"],
    "Mobile Developer": ["Kotlin", "Swift", "Java", "Git"],
    "Full-stack Developer": [
        "JavaScript",
        "TypeScript",
        "React",
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Git",
    ],
}
