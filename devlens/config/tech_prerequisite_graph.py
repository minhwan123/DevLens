"""Technology prerequisite DAG: tech name -> list of technologies it depends on.

RoadmapEngine topologically sorts a recommended subset of these nodes into a learning order.
Add a new technology by adding a node/edges here; no engine code changes needed.
"""

DEFAULT_TECH_PREREQUISITE_GRAPH: dict[str, list[str]] = {
    "Python": [],
    "SQL": [],
    "Git": [],
    "JavaScript": [],
    "Statistics": [],
    "Excel": [],
    "Docker": ["Git"],
    "FastAPI": ["Python"],
    "Django": ["Python"],
    "Flask": ["Python"],
    "PostgreSQL": ["SQL"],
    "NumPy": ["Python"],
    "Pandas": ["Python", "NumPy"],
    "Scikit-learn": ["NumPy", "Pandas"],
    "PyTorch": ["NumPy"],
    "TensorFlow": ["NumPy"],
    "CI/CD": ["Docker", "Git"],
    "AWS": ["Docker"],
    "Terraform": ["AWS"],
    "Kubernetes": ["Docker", "CI/CD"],
    "Airflow": ["Python", "Docker"],
    "Spark": ["Python"],
    "Tableau": ["Excel"],
    "TypeScript": ["JavaScript"],
    "React": ["JavaScript"],
    "Next.js": ["React", "TypeScript"],
}
