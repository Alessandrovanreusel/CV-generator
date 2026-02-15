from pydantic import BaseModel, Field

class JobRequirements(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_years: int = 0
    language: str = "en"
    keywords: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
