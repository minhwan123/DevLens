"""Seed catalog of recommendable skills/projects/datasets.

Plain data (no pydantic dependency here, kept dependency-free like the rest of config/); callers
convert entries into `domain.models.RecommendationItem`. Extend by appending entries — no engine
changes needed.
"""

from typing import Any

DEFAULT_RECOMMENDATION_CATALOG: list[dict[str, Any]] = [
    # --- skills ---
    {
        "item_id": "skill-fastapi",
        "name": "FastAPI",
        "category": "skill",
        "tags": ["FastAPI", "Python", "Backend", "Full-stack Developer"],
        "description": "Python 기반의 비동기 웹 프레임워크로, REST API 서버를 빠르게 구축한다.",
    },
    {
        "item_id": "skill-docker",
        "name": "Docker",
        "category": "skill",
        "tags": ["Docker", "DevOps"],
        "description": "애플리케이션을 컨테이너로 패키징하여 어디서든 동일하게 실행되도록 한다.",
    },
    {
        "item_id": "skill-kubernetes",
        "name": "Kubernetes",
        "category": "skill",
        "tags": ["Kubernetes", "Docker", "DevOps"],
        "description": "컨테이너 오케스트레이션 플랫폼으로 대규모 배포와 스케일링을 자동화한다.",
    },
    {
        "item_id": "skill-pytorch",
        "name": "PyTorch",
        "category": "skill",
        "tags": ["PyTorch", "NumPy", "AI Engineer"],
        "description": "딥러닝 모델을 정의하고 학습시키는 대표적인 파이썬 프레임워크.",
    },
    {
        "item_id": "skill-scikit-learn",
        "name": "Scikit-learn",
        "category": "skill",
        "tags": ["Scikit-learn", "NumPy", "Pandas", "Data Scientist"],
        "description": (
            "고전 머신러닝 모델(회귀, 분류, 클러스터링)을 손쉽게 적용할 수 있는 라이브러리."
        ),
    },
    {
        "item_id": "skill-airflow",
        "name": "Airflow",
        "category": "skill",
        "tags": ["Airflow", "Python", "Docker", "Data Engineer"],
        "description": "데이터 파이프라인을 DAG로 정의하고 스케줄링/모니터링하는 워크플로우 도구.",
    },
    {
        "item_id": "skill-terraform",
        "name": "Terraform",
        "category": "skill",
        "tags": ["Terraform", "AWS", "DevOps"],
        "description": (
            "코드로 클라우드 인프라를 정의하고 버전 관리하는 IaC(Infrastructure as Code) 도구."
        ),
    },
    {
        "item_id": "skill-react",
        "name": "React",
        "category": "skill",
        "tags": ["React", "JavaScript", "Frontend", "Full-stack Developer"],
        "description": "컴포넌트 기반으로 사용자 인터페이스를 구축하는 자바스크립트 라이브러리.",
    },
    {
        "item_id": "skill-postgresql",
        "name": "PostgreSQL",
        "category": "skill",
        "tags": ["PostgreSQL", "SQL", "Backend", "Data Engineer", "Full-stack Developer"],
        "description": "확장성과 안정성을 갖춘 오픈소스 관계형 데이터베이스.",
    },
    {
        "item_id": "skill-kotlin",
        "name": "Kotlin",
        "category": "skill",
        "tags": ["Kotlin", "Mobile Developer"],
        "description": "Android 네이티브 앱 개발에 널리 쓰이는 JVM 기반 언어.",
    },
    {
        "item_id": "skill-spark",
        "name": "Spark",
        "category": "skill",
        "tags": ["Spark", "Python", "Data Engineer"],
        "description": "대용량 데이터를 분산 처리하는 빅데이터 엔진.",
    },
    # --- projects ---
    {
        "item_id": "project-log-dashboard",
        "name": "실시간 로그 분석 대시보드",
        "category": "project",
        "tags": ["Backend", "Docker", "PostgreSQL", "Data Engineer"],
        "description": (
            "애플리케이션 로그를 수집·적재하고 실시간 지표를 시각화하는 대시보드를 구축한다."
        ),
    },
    {
        "item_id": "project-image-classifier-api",
        "name": "이미지 분류 모델 서빙 API",
        "category": "project",
        "tags": ["AI Engineer", "PyTorch", "FastAPI", "Docker"],
        "description": (
            "학습된 이미지 분류 모델을 FastAPI로 감싸 컨테이너로 배포하는 서빙 파이프라인."
        ),
    },
    {
        "item_id": "project-etl-pipeline",
        "name": "ETL 파이프라인 자동화",
        "category": "project",
        "tags": ["Data Engineer", "Airflow", "Spark", "SQL"],
        "description": (
            "외부 데이터를 정기적으로 수집·정제·적재하는 배치 파이프라인을 Airflow로 자동화한다."
        ),
    },
    {
        "item_id": "project-portfolio-spa",
        "name": "개인 포트폴리오 SPA",
        "category": "project",
        "tags": ["Frontend", "React", "TypeScript"],
        "description": "React/TypeScript로 반응형 개인 포트폴리오 웹사이트를 제작하고 배포한다.",
    },
    {
        "item_id": "project-k8s-msa",
        "name": "쿠버네티스 기반 MSA 배포",
        "category": "project",
        "tags": ["DevOps", "Kubernetes", "Docker", "Terraform", "CI/CD"],
        "description": (
            "여러 마이크로서비스를 쿠버네티스 클러스터에 CI/CD로 자동 배포하는 인프라를 구성한다."
        ),
    },
    {
        "item_id": "project-recommendation-service",
        "name": "추천 시스템 API",
        "category": "project",
        "tags": ["Data Scientist", "Scikit-learn", "FastAPI", "PostgreSQL"],
        "description": "사용자-아이템 상호작용 데이터로 추천 모델을 학습하고 API로 제공한다.",
    },
    {
        "item_id": "project-mobile-app",
        "name": "할 일 관리 모바일 앱",
        "category": "project",
        "tags": ["Mobile Developer", "Kotlin", "Swift"],
        "description": (
            "Android/iOS 네이티브로 로컬 저장과 알림 기능을 갖춘 할 일 관리 앱을 제작한다."
        ),
    },
    {
        "item_id": "project-fullstack-webapp",
        "name": "풀스택 웹 애플리케이션",
        "category": "project",
        "tags": ["Full-stack Developer", "React", "FastAPI", "PostgreSQL"],
        "description": (
            "React 프론트엔드와 FastAPI/PostgreSQL 백엔드를 함께 구축해 배포까지 진행한다."
        ),
    },
    # --- datasets ---
    {
        "item_id": "dataset-titanic",
        "name": "Kaggle Titanic",
        "category": "dataset",
        "tags": ["Data Scientist", "Scikit-learn", "beginner"],
        "description": "생존자 예측을 연습하기 좋은 입문용 정형 데이터셋.",
    },
    {
        "item_id": "dataset-nyc-taxi",
        "name": "NYC Taxi Trip Data",
        "category": "dataset",
        "tags": ["Data Engineer", "Spark", "SQL"],
        "description": "대용량 뉴욕 택시 운행 기록으로 분산 처리와 대규모 집계를 연습할 수 있다.",
    },
    {
        "item_id": "dataset-coco",
        "name": "COCO Image Dataset",
        "category": "dataset",
        "tags": ["AI Engineer", "PyTorch"],
        "description": "객체 탐지/분할 모델 학습에 널리 쓰이는 대규모 이미지 데이터셋.",
    },
    {
        "item_id": "dataset-github-events",
        "name": "GH Archive (Public GitHub Events)",
        "category": "dataset",
        "tags": ["Data Engineer", "SQL", "Airflow"],
        "description": (
            "공개 GitHub 이벤트 스트림으로 파이프라인/집계 연습에 적합한 대규모 로그 데이터셋."
        ),
    },
]
