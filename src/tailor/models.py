from pydantic import BaseModel, Field

class BilingualText(BaseModel):
    en: str = ""
    fr: str = ""

class PersonalInfo(BaseModel):
    name: str
    title: str  # Already resolved to target language
    email: str
    phone: str
    location: str
    linkedin: str = ""
    commercial_email: str = ""
    photo_path: str = ""

class TailoredExperience(BaseModel):
    id: str
    company: str
    title: str  # Already resolved to the correct language
    location: str
    start_date: str
    end_date: str | None = None
    is_current: bool = False
    summary: str  # Already resolved to the correct language
    bullets: list[str]  # Already resolved to the correct language
    skills_used: list[str] = Field(default_factory=list)

class TailoredEducation(BaseModel):
    institution: str
    degree: str  # Already resolved to the correct language
    location: str = ""
    start_date: str
    end_date: str
    details: list[str] = Field(default_factory=list)  # Resolved to correct language

class TailoredProject(BaseModel):
    name: str
    description: str  # Resolved to correct language
    technologies: list[str] = Field(default_factory=list)

class TailoredCertification(BaseModel):
    name: str
    issuer: str = ""
    date: str = ""

class TailoredLanguageSkill(BaseModel):
    language: str
    level: str
    code: str = ""

class TailoredVolunteering(BaseModel):
    organization: str
    role: str  # Resolved to correct language
    description: str = ""  # Resolved to correct language

class TailoredCV(BaseModel):
    personal: PersonalInfo
    summary: str  # Already resolved to correct language + tailored to job
    experience: list[TailoredExperience]
    education: list[TailoredEducation]
    skills: dict[str, list[str]]  # Category -> list of skills, reordered
    languages: list[TailoredLanguageSkill]
    certifications: list[TailoredCertification] = Field(default_factory=list)
    projects: list[TailoredProject] = Field(default_factory=list)
    volunteering: list[TailoredVolunteering] = Field(default_factory=list)
    target_language: str = "en"
