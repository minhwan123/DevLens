import json
import re
import tomllib
from collections.abc import Callable
from datetime import datetime

from devlens.config.filter_thresholds import (
    DEFAULT_FILTER_NORMALIZATION,
    RepositoryFilterNormalization,
)
from devlens.domain.models.repository_analysis import RepositoryAnalysis
from devlens.domain.models.repository_candidate import RepositoryCandidate
from devlens.domain.models.repository_raw_data import RepositoryRawData
from devlens.domain.policies.readme_scoring import score_readme

_BYTES_PER_LINE_ESTIMATE = 40

_EXACT_BASENAME_MARKERS: dict[str, str] = {
    "dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "manage.py": "Django",
    "alembic.ini": "Alembic",
    "angular.json": "Angular",
    "vue.config.js": "Vue.js",
    "next.config.js": "Next.js",
    "next.config.ts": "Next.js",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "go.mod": "Go Modules",
    "cargo.toml": "Cargo",
    "gemfile": "Bundler",
    "serverless.yml": "Serverless Framework",
    "chart.yaml": "Helm",
}

_SUFFIX_MARKERS: dict[str, str] = {
    ".tf": "Terraform",
    ".ipynb": "Jupyter Notebook",
}

_PATH_PREFIX_MARKERS: dict[str, str] = {
    ".github/workflows/": "GitHub Actions",
}

_TAG_TO_DOMAIN: dict[str, str] = {
    "Django": "backend",
    "Angular": "frontend",
    "Vue.js": "frontend",
    "Next.js": "frontend",
    "Docker": "devops",
    "Docker Compose": "devops",
    "Terraform": "devops",
    "Helm": "devops",
    "GitHub Actions": "devops",
    "Jupyter Notebook": "data-science",
    "FastAPI": "backend",
    "Flask": "backend",
    "Express": "backend",
    "PostgreSQL": "backend",
    "React": "frontend",
    "PyTorch": "data-science",
    "TensorFlow": "data-science",
    "Scikit-learn": "data-science",
    "Pandas": "data-science",
    "NumPy": "data-science",
    "Spark": "data-science",
    "Airflow": "data-science",
}

_NPM_PACKAGE_TO_SKILL: dict[str, str] = {
    "react": "React",
    "react-dom": "React",
    "vue": "Vue.js",
    "next": "Next.js",
    "express": "Express",
    "@angular/core": "Angular",
    "svelte": "Svelte",
}

_PYPI_PACKAGE_TO_SKILL: dict[str, str] = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "psycopg2": "PostgreSQL",
    "psycopg2-binary": "PostgreSQL",
    "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "pyspark": "Spark",
    "apache-airflow": "Airflow",
}

_DEPENDENCY_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")

_CI_PATH_MARKERS = (
    ".github/workflows/",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "jenkinsfile",
    "azure-pipelines.yml",
    ".travis.yml",
)

_DOCKER_BASENAMES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}

_TEST_PATH_SEGMENTS = {"tests", "test", "__tests__", "spec"}


class GithubAnalysisEngine:
    """Derives per-repository evidence from raw GitHub data.

    Produces a RepositoryCandidate (consumed by RepositoryFilterPolicy) plus tech stack,
    tests/CI/Docker presence, commit frequency, README quality, and best-effort domain tags.
    Tech stack and domain detection are primarily filename-marker based (a proxy, not exact
    dependency parsing), supplemented by best-effort parsing of known manifest files
    (package.json, requirements.txt, pyproject.toml) when their contents are supplied via
    `raw.manifest_files`.
    """

    def __init__(
        self, normalization: RepositoryFilterNormalization = DEFAULT_FILTER_NORMALIZATION
    ) -> None:
        self._normalization = normalization

    def analyze(self, raw: RepositoryRawData) -> RepositoryAnalysis:
        readme_length, readme_has_headings = _readme_signals(raw.readme_text)
        tech_stack = _detect_tech_stack(raw.languages, raw.file_paths, raw.manifest_files)

        candidate = RepositoryCandidate(
            repo_name=raw.repo_name,
            is_fork=raw.is_fork,
            is_template=raw.is_template,
            commit_count=raw.commit_count,
            contributor_count=raw.contributor_count,
            last_activity_at=raw.pushed_at,
            readme_length=readme_length,
            readme_has_headings=readme_has_headings,
            code_line_count=_estimate_code_line_count(raw.languages),
            file_extension_count=_file_extension_count(raw.file_paths),
        )

        return RepositoryAnalysis(
            candidate=candidate,
            tech_stack=tech_stack,
            has_tests=_has_tests(raw.file_paths),
            has_ci=_has_ci(raw.file_paths),
            has_docker=_has_docker(raw.file_paths),
            commit_frequency=_commit_frequency(raw.commit_count, raw.created_at, raw.pushed_at),
            readme_quality_score=score_readme(
                readme_length, readme_has_headings, self._normalization.readme_length_target
            ),
            domain_tags=_detect_domain_tags(tech_stack),
        )


def _readme_signals(readme_text: str | None) -> tuple[int, bool]:
    if readme_text is None:
        return 0, False
    has_headings = any(line.lstrip().startswith("#") for line in readme_text.splitlines())
    return len(readme_text), has_headings


def _commit_frequency(commit_count: int, created_at: datetime, pushed_at: datetime) -> float:
    weeks = max((pushed_at - created_at).days / 7, 1.0)
    return commit_count / weeks


def _estimate_code_line_count(languages: dict[str, int]) -> int:
    """Rough LOC proxy from GitHub's per-language byte totals (no file content is fetched)."""
    return round(sum(languages.values()) / _BYTES_PER_LINE_ESTIMATE)


def _file_extension_count(file_paths: list[str]) -> int:
    extensions: set[str] = set()
    for path in file_paths:
        basename = path.rsplit("/", 1)[-1]
        stem, dot, ext = basename.rpartition(".")
        if dot and stem:
            extensions.add(ext.lower())
    return len(extensions)


def _has_tests(file_paths: list[str]) -> bool:
    for path in file_paths:
        segments = path.lower().split("/")
        basename = segments[-1]
        if any(segment in _TEST_PATH_SEGMENTS for segment in segments[:-1]):
            return True
        if basename.startswith("test_") or basename.endswith("_test.py") or ".spec." in basename:
            return True
    return False


def _has_ci(file_paths: list[str]) -> bool:
    lowered_paths = [path.lower() for path in file_paths]
    return any(marker in path for path in lowered_paths for marker in _CI_PATH_MARKERS)


def _has_docker(file_paths: list[str]) -> bool:
    return any(path.rsplit("/", 1)[-1].lower() in _DOCKER_BASENAMES for path in file_paths)


def _detect_markers(file_paths: list[str]) -> list[str]:
    tags: list[str] = []
    for path in file_paths:
        lowered = path.lower()
        basename = lowered.rsplit("/", 1)[-1]
        if basename in _EXACT_BASENAME_MARKERS:
            tags.append(_EXACT_BASENAME_MARKERS[basename])
        for suffix, tag in _SUFFIX_MARKERS.items():
            if basename.endswith(suffix):
                tags.append(tag)
        for prefix, tag in _PATH_PREFIX_MARKERS.items():
            if lowered.startswith(prefix):
                tags.append(tag)
    return tags


def _detect_tech_stack(
    languages: dict[str, int], file_paths: list[str], manifest_files: dict[str, str]
) -> list[str]:
    by_bytes_desc = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)
    language_names = [name for name, _ in by_bytes_desc]
    markers = _detect_markers(file_paths)
    manifest_tags = _detect_manifest_tags(manifest_files)
    tech_stack: list[str] = []
    seen: set[str] = set()
    for tag in [*language_names, *markers, *manifest_tags]:
        if tag not in seen:
            seen.add(tag)
            tech_stack.append(tag)
    return tech_stack


def _detect_domain_tags(tech_stack: list[str]) -> list[str]:
    return sorted({domain for tag in tech_stack if (domain := _TAG_TO_DOMAIN.get(tag)) is not None})


def _normalize_pypi_name(name: str) -> str:
    """PEP 503 normalization so requirements.txt/pyproject.toml spellings all converge."""
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def _parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    tags: list[str] = []
    for section in ("dependencies", "devDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict):
            continue
        for raw_name in deps:
            tag = _NPM_PACKAGE_TO_SKILL.get(str(raw_name).strip().lower())
            if tag:
                tags.append(tag)
    return tags


def _parse_requirements_txt(content: str) -> list[str]:
    tags: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-") or "://" in line:
            continue
        match = _DEPENDENCY_NAME_RE.match(line)
        if not match:
            continue
        tag = _PYPI_PACKAGE_TO_SKILL.get(_normalize_pypi_name(match.group(1)))
        if tag:
            tags.append(tag)
    return tags


def _tags_from_pep508_list(entries: object) -> list[str]:
    if not isinstance(entries, list):
        return []
    tags: list[str] = []
    for entry in entries:
        if not isinstance(entry, str):
            continue
        match = _DEPENDENCY_NAME_RE.match(entry.strip())
        if not match:
            continue
        tag = _PYPI_PACKAGE_TO_SKILL.get(_normalize_pypi_name(match.group(1)))
        if tag:
            tags.append(tag)
    return tags


def _parse_pyproject_toml(content: str) -> list[str]:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return []

    tags: list[str] = []
    project = data.get("project")
    if isinstance(project, dict):
        tags.extend(_tags_from_pep508_list(project.get("dependencies")))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for group_deps in optional.values():
                tags.extend(_tags_from_pep508_list(group_deps))

    tool = data.get("tool")
    poetry = tool.get("poetry") if isinstance(tool, dict) else None
    if isinstance(poetry, dict):
        for section in ("dependencies", "dev-dependencies"):
            deps = poetry.get(section)
            if isinstance(deps, dict):
                for raw_name in deps:
                    tag = _PYPI_PACKAGE_TO_SKILL.get(_normalize_pypi_name(str(raw_name)))
                    if tag:
                        tags.append(tag)

    return tags


_MANIFEST_PARSERS: dict[str, Callable[[str], list[str]]] = {
    "package.json": _parse_package_json,
    "requirements.txt": _parse_requirements_txt,
    "pyproject.toml": _parse_pyproject_toml,
}


def _detect_manifest_tags(manifest_files: dict[str, str]) -> list[str]:
    tags: list[str] = []
    for path, content in manifest_files.items():
        basename = path.rsplit("/", 1)[-1].lower()
        parser = _MANIFEST_PARSERS.get(basename)
        if parser is not None:
            tags.extend(parser(content))
    return tags
