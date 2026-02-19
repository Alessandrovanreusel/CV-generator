"""Shared pytest fixtures for CV-generator tests."""

import pytest

from src.analyzer.models import JobRequirements
from src.tailor.models import (
    PersonalInfo,
    TailoredCertification,
    TailoredCV,
    TailoredEducation,
    TailoredExperience,
    TailoredLanguageSkill,
    TailoredProject,
    TailoredVolunteering,
)


@pytest.fixture
def sample_job_text() -> str:
    """Realistic job advertisement text."""
    return (
        "Senior Software Engineer - TechCorp\n"
        "Location: Amsterdam, Netherlands\n"
        "Type: Full-time\n"
        "Department: Engineering\n\n"
        "About the Role\n\n"
        "TechCorp is looking for a Senior Software Engineer to join our growing "
        "platform team in Amsterdam. You will play a key role in designing, building, "
        "and maintaining the backend services and cloud infrastructure that power our "
        "data analytics platform, used by over 2 million users worldwide.\n\n"
        "Requirements\n\n"
        "- 5+ years of professional software development experience\n"
        "- Strong proficiency in Python, with experience building REST APIs\n"
        "- Solid understanding of cloud services on AWS (EC2, S3, Lambda, RDS)\n"
        "- Hands-on experience with Docker for containerization\n"
        "- Familiarity with CI/CD pipelines using GitHub Actions or Jenkins\n"
        "- Experience with front-end development using React and TypeScript\n"
        "- Strong knowledge of relational databases such as PostgreSQL\n"
        "- Proficiency with Git and collaborative development workflows\n"
        "- Good communication skills in English; Dutch is a plus\n\n"
        "Nice to Have\n\n"
        "- Experience with Kubernetes\n"
        "- Familiarity with GraphQL APIs\n"
        "- Knowledge of Terraform or CloudFormation\n\n"
        "Responsibilities\n\n"
        "- Design and implement scalable microservices and APIs\n"
        "- Collaborate with product managers, designers, and other engineers\n"
        "- Write clean, well-tested, and well-documented code\n"
        "- Participate in architecture discussions and technical design reviews\n"
        "- Mentor junior developers\n\n"
        "To apply, send your CV to careers@techcorp.example.com.\n"
    )


@pytest.fixture
def sample_job_requirements() -> JobRequirements:
    """A populated JobRequirements instance matching the sample job text."""
    return JobRequirements(
        title="Senior Software Engineer",
        company="TechCorp",
        location="Amsterdam, Netherlands",
        description="Backend-focused senior engineer role building cloud infrastructure and APIs.",
        required_skills=["Python", "AWS", "Docker", "React", "TypeScript", "PostgreSQL", "Git"],
        preferred_skills=["Kubernetes", "GraphQL", "Terraform"],
        experience_years=5,
        language="en",
        keywords=["CI/CD", "microservices", "REST API", "cloud", "backend"],
        responsibilities=[
            "Design and implement scalable microservices and APIs",
            "Collaborate with product managers and engineers",
            "Write clean, well-tested code",
            "Participate in architecture discussions",
            "Mentor junior developers",
        ],
    )


@pytest.fixture
def sample_master_cv() -> dict:
    """Minimal but complete master CV dictionary matching master_cv.json structure."""
    return {
        "personal_info": {
            "name": "Alessandro van Reusel",
            "title": {"en": "Software Engineer", "fr": "Ingénieur Logiciel"},
            "location": "Amsterdam, Netherlands",
            "phone": "+31 6 12345678",
            "email": "alessandro@example.com",
            "linkedin": "https://linkedin.com/in/alessandrovr",
            "photo": "data/photo.jpg",
        },
        "professional_summary": {
            "en": "Experienced software engineer with expertise in Python, cloud infrastructure, and test automation.",
            "fr": "Ingénieur logiciel expérimenté avec une expertise en Python, infrastructure cloud et automatisation de tests.",
        },
        "experience": [
            {
                "id": "exp-1",
                "company": "CloudTech BV",
                "title": {"en": "Software Engineer", "fr": "Ingénieur Logiciel"},
                "location": "Amsterdam",
                "start_date": "2024-01",
                "end_date": None,
                "is_current": True,
                "is_parent": False,
                "summary": {
                    "en": "Building cloud-native applications on AWS.",
                    "fr": "Développement d'applications cloud-natives sur AWS.",
                },
                "bullets": {
                    "en": [
                        "Developed REST APIs using Python and FastAPI serving 1M+ requests/day",
                        "Designed and deployed AWS infrastructure using Terraform",
                        "Implemented CI/CD pipelines with GitHub Actions",
                    ],
                    "fr": [
                        "Développé des API REST avec Python et FastAPI pour 1M+ requêtes/jour",
                        "Conçu et déployé l'infrastructure AWS avec Terraform",
                        "Implémenté des pipelines CI/CD avec GitHub Actions",
                    ],
                },
                "skills_used": ["Python", "AWS", "Docker", "Terraform", "CI/CD"],
                "sub_experiences": [],
                "parent_id": None,
            },
            {
                "id": "exp-2",
                "company": "DataSoft NV",
                "title": {"en": "Junior Developer", "fr": "Développeur Junior"},
                "location": "Brussels",
                "start_date": "2022-06",
                "end_date": "2023-12",
                "is_current": False,
                "is_parent": False,
                "summary": {
                    "en": "Full-stack development with React and Python.",
                    "fr": "Développement full-stack avec React et Python.",
                },
                "bullets": {
                    "en": [
                        "Built React front-end components with TypeScript",
                        "Maintained PostgreSQL databases and wrote complex queries",
                    ],
                    "fr": [
                        "Construit des composants front-end React avec TypeScript",
                        "Maintenance de bases de données PostgreSQL et requêtes complexes",
                    ],
                },
                "skills_used": ["React", "TypeScript", "Python", "PostgreSQL"],
                "sub_experiences": [],
                "parent_id": None,
            },
            {
                "id": "exp-parent",
                "company": "Umbrella Corp",
                "title": {"en": "Consultant", "fr": "Consultant"},
                "location": "Paris",
                "start_date": "2021-01",
                "end_date": "2022-05",
                "is_current": False,
                "is_parent": True,
                "summary": {"en": "Consulting missions", "fr": "Missions de conseil"},
                "bullets": {"en": [], "fr": []},
                "skills_used": [],
                "sub_experiences": ["exp-child-a"],
                "parent_id": None,
            },
            {
                "id": "exp-child-a",
                "company": "Client Alpha (Umbrella Corp)",
                "title": {"en": "Python Developer", "fr": "Developpeur Python"},
                "location": "Paris",
                "start_date": "2021-06",
                "end_date": "2022-05",
                "is_current": False,
                "is_parent": False,
                "summary": {"en": "Built Python tools.", "fr": "Construit des outils Python."},
                "bullets": {
                    "en": ["Developed internal CLI tools with Python", "Automated reporting pipelines"],
                    "fr": ["Developpe des outils CLI internes en Python", "Automatise des pipelines de reporting"],
                },
                "skills_used": ["Python", "AWS"],
                "sub_experiences": [],
                "parent_id": "exp-parent",
            },
        ],
        "education": [
            {
                "institution": "Vrije Universiteit Amsterdam",
                "degree": {
                    "en": "MSc Computer Science",
                    "fr": "Master en Informatique",
                },
                "start_date": "2017",
                "end_date": "2022",
                "coursework": {
                    "en": "Data Structures, Algorithms, Cloud Computing",
                    "fr": "Structures de données, Algorithmes, Cloud Computing",
                },
            }
        ],
        "skills": {
            "Programming": ["Python", "Java", "TypeScript"],
            "Cloud": ["AWS", "Docker", "Terraform"],
            "Frameworks": ["React", "FastAPI", "Django"],
        },
        "languages": [
            {
                "language": {"en": "English", "fr": "Anglais"},
                "level": {"en": "Native", "fr": "Langue maternelle"},
                "code": "en",
            },
            {
                "language": {"en": "French", "fr": "Français"},
                "level": {"en": "Fluent", "fr": "Courant"},
                "code": "fr",
            },
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect Associate",
                "issuer": "Amazon Web Services",
                "date": "2024-01",
                "relevance_tags": ["AWS", "cloud"],
            }
        ],
        "projects": [
            {
                "name": "CV Generator",
                "description": {
                    "en": "Automated CV tailoring tool using AI",
                    "fr": "Outil d'adaptation de CV automatisé par IA",
                },
                "technologies": ["Python", "Claude API", "WeasyPrint"],
            }
        ],
        "volunteering": [
            {
                "organization": "Code for NL",
                "role": {"en": "Volunteer Developer", "fr": "Développeur Bénévole"},
                "description": {
                    "en": "Built open-source tools for civic projects.",
                    "fr": "Développement d'outils open-source pour des projets civiques.",
                },
            }
        ],
    }


@pytest.fixture
def sample_tailored_cv() -> TailoredCV:
    """A fully populated TailoredCV instance for testing."""
    return TailoredCV(
        personal=PersonalInfo(
            name="Alessandro van Reusel",
            title="Software Engineer",
            email="alessandro@example.com",
            phone="+31 6 12345678",
            location="Amsterdam, Netherlands",
            linkedin="https://linkedin.com/in/alessandrovr",
            photo_path="data/photo.jpg",
        ),
        summary="Experienced software engineer specializing in Python, AWS, and scalable microservices.",
        experience=[
            TailoredExperience(
                id="exp-1",
                company="CloudTech BV",
                title="Software Engineer",
                location="Amsterdam",
                start_date="2024-01",
                end_date=None,
                is_current=True,
                summary="Building cloud-native applications on AWS.",
                bullets=[
                    "Developed REST APIs using Python and FastAPI serving 1M+ requests/day",
                    "Designed and deployed AWS infrastructure using Terraform",
                    "Implemented CI/CD pipelines with GitHub Actions",
                ],
                skills_used=["Python", "AWS", "Docker", "Terraform", "CI/CD"],
            ),
            TailoredExperience(
                id="exp-2",
                company="DataSoft NV",
                title="Junior Developer",
                location="Brussels",
                start_date="2022-06",
                end_date="2023-12",
                is_current=False,
                summary="Full-stack development with React and Python.",
                bullets=[
                    "Built React front-end components with TypeScript",
                    "Maintained PostgreSQL databases and wrote complex queries",
                ],
                skills_used=["React", "TypeScript", "Python", "PostgreSQL"],
            ),
            TailoredExperience(
                id="exp-parent",
                company="Umbrella Corp",
                title="Consultant",
                location="Paris",
                start_date="2021-01",
                end_date="2022-05",
                is_current=False,
                summary="Consulting missions",
                bullets=[],
                is_parent=True,
                sub_experiences=[
                    TailoredExperience(
                        id="exp-child-a",
                        company="Client Alpha (Umbrella Corp)",
                        title="Python Developer",
                        location="Paris",
                        start_date="2021-06",
                        end_date="2022-05",
                        is_current=False,
                        summary="Built Python tools.",
                        bullets=["Developed internal CLI tools with Python", "Automated reporting pipelines"],
                        skills_used=["Python", "AWS"],
                    ),
                ],
            ),
        ],
        education=[
            TailoredEducation(
                institution="Vrije Universiteit Amsterdam",
                degree="MSc Computer Science",
                start_date="2017",
                end_date="2022",
                details=["Data Structures", "Algorithms", "Cloud Computing"],
            )
        ],
        skills={
            "Programming": ["Python", "Java", "TypeScript"],
            "Cloud": ["AWS", "Docker", "Terraform"],
            "Frameworks": ["React", "FastAPI", "Django"],
        },
        languages=[
            TailoredLanguageSkill(language="English", level="Native", code="en"),
            TailoredLanguageSkill(language="French", level="Fluent", code="fr"),
        ],
        certifications=[
            TailoredCertification(
                name="AWS Solutions Architect Associate",
                issuer="Amazon Web Services",
                date="2024-01",
            )
        ],
        projects=[
            TailoredProject(
                name="CV Generator",
                description="Automated CV tailoring tool using AI",
                technologies=["Python", "Claude API", "WeasyPrint"],
            )
        ],
        volunteering=[
            TailoredVolunteering(
                organization="Code for NL",
                role="Volunteer Developer",
                description="Built open-source tools for civic projects.",
            )
        ],
        target_language="en",
    )
