from typing import List, Optional
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    """
    Representa la información de contacto estructurada del ingeniero junior.
    """
    email: Optional[str] = Field(None, description="Email address of the junior engineer")
    phone: Optional[str] = Field(None, description="Phone number of the junior engineer")
    location: Optional[str] = Field(None, description="Physical location or city and country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")

class OptimizedExperience(BaseModel):
    """
    Representa una experiencia profesional optimizada para la oferta laboral.
    """
    company: str = Field(description="Name of the company or organization")
    role: str = Field(description="Optimized role title aligned with the job description")
    period: str = Field(description="Employment or project period")
    tailored_achievements: List[str] = Field(
        description="Action-oriented, high-impact achievements tailored to the target job description. Focus on metrics, technologies, and results without inventing any facts."
    )

class OptimizedEducation(BaseModel):
    """
    Representa la formación académica u proyectos de estudio optimizados.
    """
    institution: str = Field(description="Name of the educational institution")
    degree: str = Field(description="Degree name or certification")
    period: str = Field(description="Period of study or completion date")
    achievements: List[str] = Field(
        description="Key academic achievements, coursework, or project descriptions aligned with the job requirements."
    )

class Alucinacion(BaseModel):
    """
    Representa un dato inventado o no respaldado detectado en el CV optimizado.
    """
    linea_cv: str = Field(description="Texto exacto o sección del CV donde aparece el dato cuestionable")
    dato_inventado: str = Field(description="Descripción del dato que no está respaldado por el perfil original")
    severidad: str = Field(description="Nivel de severidad: 'baja', 'media' o 'alta'")

class ReporteRobustez(BaseModel):
    """
    Reporte estructurado de auditoría de honestidad y robustez del CV optimizado.
    """
    score_honestidad: int = Field(
        ge=0,
        le=100,
        description="Puntuación de honestidad de 0 a 100 respecto al perfil original",
    )
    alucinaciones_detectadas: List[Alucinacion] = Field(
        description="Lista de alucinaciones, inconsistencias o datos no verificables detectados"
    )
    comentario_auditor: str = Field(
        description="Resumen del auditor sobre cumplimiento ético, inconsistencias y recomendaciones"
    )

class OptimizedCV(BaseModel):
    """
    Estructura completa del currículum optimizado y adaptado.
    """
    full_name: str = Field(description="Full name of the junior engineer")
    contact_info: ContactInfo = Field(description="Structured contact info of the junior engineer")
    professional_summary: str = Field(
        description="A powerful 3-4 sentence professional summary tailored to the target job using the Pygmalion Effect, highlighting technical capability and potential."
    )
    optimized_skills: List[str] = Field(
        description="List of core technical and professional skills filtered and sorted by relevance to the job description."
    )
    experiences: List[OptimizedExperience] = Field(
        description="List of professional experiences with achievements tailored using action verbs and technical keywords."
    )
    education: List[OptimizedEducation] = Field(
        description="List of education details and tailored academic projects."
    )
