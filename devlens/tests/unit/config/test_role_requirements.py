from devlens.config.role_requirements import DEFAULT_ROLE_REQUIRED_SKILLS


def test_mobile_and_fullstack_roles_are_registered_with_nonempty_skills() -> None:
    assert DEFAULT_ROLE_REQUIRED_SKILLS["Mobile Developer"]
    assert DEFAULT_ROLE_REQUIRED_SKILLS["Full-stack Developer"]


def test_all_roles_have_unique_nonempty_skill_lists() -> None:
    for role, skills in DEFAULT_ROLE_REQUIRED_SKILLS.items():
        assert skills, f"{role} has no required skills"
        assert len(skills) == len(set(skills)), f"{role} has duplicate skills"
