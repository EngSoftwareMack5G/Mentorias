from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MentoriaStatus(str, Enum):
    AGENDADA = "agendada"
    CONCLUIDA = "concluída"
    CANCELADA = "cancelada"
    DISPONIVEL = "disponível"

class UserType(str, Enum):
    MENTOR = "Mentor"
    MENTORADO = "Mentorado" # Exemplo de futuro tipo
    ADMIN = "Admin"       # Exemplo de futuro tipo

class MentoriaBase(BaseModel):
    data_hora: datetime
    duracao_minutos: int
    status: MentoriaStatus
    topico: str

class MentoriaCreate(MentoriaBase):
    pass # Será preenchido pelo token do usuário logado

class MentoriaUpdate(BaseModel):
    data_hora: Optional[datetime] = None
    duracao_minutos: Optional[int] = None
    status: Optional[MentoriaStatus] = None
    topico: Optional[str] = None

class MentoriaInDB(MentoriaBase):
    id: int
    mentor_email: EmailStr
    data_hora: datetime
    duracao_minutos: int
    status: MentoriaStatus
    topico: str

class MentoradoEmail(BaseModel):
    mentorado_email: EmailStr

class TokenData(BaseModel):
    username: EmailStr
    type: UserType # Usaremos este enum para verificar o tipo de usuário