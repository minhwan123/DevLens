from pydantic import BaseModel, Field


class RoleFit(BaseModel):
    """How well a profile currently fits a target role, ranked by required-skill coverage —
    the reverse of the usual flow (pick a role, see the gap): here every known role is scored
    against the profile to surface "what you're already suited for"."""

    role: str
    fit_score: float = Field(
        ge=0, le=1, description="Fraction of the role's required skills already covered"
    )
    matched_skills: list[str]
    missing_skills: list[str]
