from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from typing import List
# Importe _AsyncGeneratorContextManager para type hinting se não estiver globalmente disponível
from contextlib import _AsyncGeneratorContextManager
import asyncpg # Para o type hint da dependência de conexão

from app.models.mentoria import (
    MentoriaCreate, MentoriaUpdate, MentoriaInDB,
    MentoradoEmail, TokenData, UserType
)
from app.crud import mentoria_crud # Importa o módulo
from app.auth.security import get_current_active_mentor, RoleChecker, get_current_user
from app.database.session import get_db_connection


router = APIRouter(
    prefix="/mentorias",
    tags=["Mentorias"]
)

# --- Endpoints de Mentoria ---

@router.post(
    "/",
    response_model=MentoriaInDB,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))]
)
async def create_new_mentoria(
    mentoria_data: MentoriaCreate,
    current_user: TokenData = Depends(get_current_active_mentor),
    # Aqui, conn_manager é o nome da variável local que recebe o resultado de get_db_connection
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    created_mentoria = await mentoria_crud.create_mentoria(
        # Passe o conn_manager para o parâmetro db_conn_manager da função CRUD
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria=mentoria_data,
        mentor_email=current_user.username
    )
    if not created_mentoria:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create mentoria")
    return created_mentoria


@router.get(
    "/",
    response_model=List[MentoriaInDB],
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR, UserType.MENTORADO]))]
)
async def list_mentorias(
    current_user: TokenData = Depends(get_current_user),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    mentorias = await mentoria_crud.get_mentorias_by_user(
        db_conn_manager=conn_manager,
        email=current_user.username,
        type = current_user.type
    )
    return mentorias

@router.get(
        "/topico/{topic}",
        response_model=List[MentoriaInDB],
)
async def list_mentorias_by_topic(
    topic: str = Path(...),
    current_user: TokenData = Depends(get_current_user),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    mentorias = await mentoria_crud.get_mentorias_by_topic(
        db_conn_manager=conn_manager,
        topic=topic
    )
    return mentorias


@router.get(
    "/{mentoria_id}",
    response_model=MentoriaInDB
)
async def get_single_mentoria(
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_user),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    mentoria = await mentoria_crud.get_mentoria_by_id(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria_id=mentoria_id
    )
    if not mentoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found")
    return mentoria


@router.put(
    "/{mentoria_id}",
    response_model=MentoriaInDB,
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))]
)
async def update_existing_mentoria(
    mentoria_data: MentoriaUpdate,
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_active_mentor),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    updated_mentoria = await mentoria_crud.update_mentoria(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria_id=mentoria_id,
        mentoria_update=mentoria_data,
        current_mentor_email=current_user.username
    )
    if updated_mentoria == "UNAUTHORIZED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this mentoria")
    if not updated_mentoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found or update failed")
    return updated_mentoria


@router.delete(
    "/{mentoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))]
)
async def delete_existing_mentoria(
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_active_mentor),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    success = await mentoria_crud.delete_mentoria(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria_id=mentoria_id,
        current_mentor_email=current_user.username
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found or not authorized to delete")
    return None


# --- Endpoints de Associação Mentoria-Mentorado ---

@router.post(
    "/{mentoria_id}/mentorados",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))]
)
async def add_mentorado_to_a_mentoria(
    mentorado_data: MentoradoEmail,
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_active_mentor),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    success = await mentoria_crud.add_mentorado_to_mentoria(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria_id=mentoria_id,
        mentorado_email_obj=mentorado_data,
        current_mentor_email=current_user.username
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found or not authorized, or mentorado could not be added/already in mentoria")
    return {"message": "Mentorado added successfully to mentoria"}


@router.delete(
    "/{mentoria_id}/mentorados",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))]
)
async def remove_mentorado_from_a_mentoria(
    mentorado_data: MentoradoEmail,
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_active_mentor),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    success = await mentoria_crud.remove_mentorado_from_mentoria(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUI
        mentoria_id=mentoria_id,
        mentorado_email_obj=mentorado_data,
        current_mentor_email=current_user.username
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found, mentorado not in mentoria, or not authorized")
    return None


@router.get(
    "/{mentoria_id}/mentorados",
    response_model=List[str]
)
async def list_mentorados_in_mentoria(
    mentoria_id: int = Path(..., ge=1),
    current_user: TokenData = Depends(get_current_user),
    conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection] = Depends(get_db_connection)
):
    mentorados_emails = await mentoria_crud.get_mentorados_for_mentoria(
        db_conn_manager=conn_manager, # <--- CORRIGIDO AQUIs
        mentoria_id=mentoria_id
    )
    if mentorados_emails is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentoria not found")
    return mentorados_emails