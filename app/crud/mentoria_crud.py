from typing import List, Optional
import asyncpg
from pydantic import EmailStr
from app.models.mentoria import MentoriaCreate, MentoriaUpdate, MentoriaInDB, MentoradoEmail, MentoriaStatus, UserType, MentoradoInMentoria
from enum import Enum
from contextlib import _AsyncGeneratorContextManager # Para type hinting, se desejar

# --- Mentorias ---

async def create_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection], # O nome foi mudado para clareza
    mentoria: MentoriaCreate,
    mentor_email: str
) -> Optional[MentoriaInDB]:
    async with db_conn_manager as conn: # <--- USE ASYNC WITH AQUI
        query = """
            INSERT INTO mentorias (mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao;
        """
        row = await conn.fetchrow( # <--- Agora conn é o objeto de conexão
            query,
            mentor_email,
            mentoria.data_hora,
            mentoria.duracao_minutos,
            mentoria.status.value,
            mentoria.topico,
            mentoria.titulo,
            mentoria.descricao
        )

        row = dict(row) if row else None

        return MentoriaInDB.model_validate(row) if row else None

async def get_mentorias_by_user(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    email: str,
    type: UserType
) -> List[MentoriaInDB]:
    async with db_conn_manager as conn:
        if(type == UserType.MENTOR):
            query = """
                SELECT id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao
                FROM mentorias
                WHERE mentor_email = $1 ORDER BY data_hora DESC;
            """
        else:
            query = """
                SELECT id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao
                FROM mentorias
                WHERE id IN (SELECT mentoria_id FROM mentoria_mentorados WHERE mentorado_email = $1) ORDER BY data_hora DESC;
            """
        rows = await conn.fetch(query, email)

        return [MentoriaInDB.model_validate(dict(row)) for row in rows]

async def get_mentorias_by_topic(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    topic: str
) -> List[MentoriaInDB]:
    async with db_conn_manager as conn:
        query = """
            SELECT id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao
            FROM mentorias
            WHERE topico = $1 ORDER BY data_hora DESC;
        """
        rows = await conn.fetch(query, topic)

        return [MentoriaInDB.model_validate(dict(row)) for row in rows]


async def get_mentoria_by_id(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int
) -> Optional[MentoriaInDB]:
    async with db_conn_manager as conn:
        query = """
            SELECT id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao
            FROM mentorias
            WHERE id = $1;
        """
        row = await conn.fetchrow(query, mentoria_id)

        row = dict(row) if row else None

        return MentoriaInDB.model_validate(row) if row else None

async def update_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int,
    mentoria_update: MentoriaUpdate,
    current_mentor_email: str
) -> Optional[MentoriaInDB]:
    async with db_conn_manager as conn: # <--- USE ASYNC WITH AQUI
        # Busca a mentoria para verificar se o mentor atual é o proprietário
        # Precisamos de uma função interna ou passar a conexão para get_mentoria_by_id
        # Vamos ajustar get_mentoria_by_id para aceitar uma conexão diretamente ou criar uma função auxiliar

        # Abordagem 1: Passar a conexão para get_mentoria_by_id_internal (se o reescrevermos)
        # Ou, mais simples, replicar a lógica de fetch aqui se for só para esta verificação
        temp_query_check = "SELECT mentor_email FROM mentorias WHERE id = $1;"
        existing_mentoria_record = await conn.fetchrow(temp_query_check, mentoria_id)

        if not existing_mentoria_record:
            return None # Mentoria não encontrada
        if existing_mentoria_record['mentor_email'] != current_mentor_email:
            return "UNAUTHORIZED"

        update_fields = mentoria_update.model_dump(exclude_unset=True)
        if not update_fields:
            # Se não houver campos para atualizar, podemos buscar e retornar a mentoria completa
            full_mentoria_record = await conn.fetchrow(
                "SELECT id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao FROM mentorias WHERE id = $1;",
                mentoria_id
            )

            full_mentoria_record = dict(full_mentoria_record) if full_mentoria_record else None

            return MentoriaInDB.model_validate(full_mentoria_record) if full_mentoria_record else None


        set_clauses = []
        values = []
        param_idx = 1
        for key, value in update_fields.items():
            if isinstance(value, Enum):
                value = value.value
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        values.append(mentoria_id)
        values.append(current_mentor_email)

        query = f"""
            UPDATE mentorias
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx} AND mentor_email = ${param_idx + 1}
            RETURNING id, mentor_email, data_hora, duracao_minutos, status, topico, titulo, descricao;
        """
        row = await conn.fetchrow(query, *values)
        
        row = dict(row) if row else None

        return MentoriaInDB.model_validate(row) if row else None

# ... e assim por diante para todas as funções CRUD ...
# Exemplo para delete_mentoria:
async def delete_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int,
    current_mentor_email: str
) -> bool:
    async with db_conn_manager as conn:
        query = """
            DELETE FROM mentorias
            WHERE id = $1 AND mentor_email = $2
            RETURNING id;
        """
        deleted_id = await conn.fetchval(query, mentoria_id, current_mentor_email)
        return deleted_id is not None

# --- Associação Mentoria-Mentorado ---
# Exemplo para add_mentorado_to_mentoria:
async def add_mentorado_to_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int,
    mentorado_email: str
) -> bool:
    async with db_conn_manager as conn:
        query_insert = """
            INSERT INTO mentoria_mentorados (mentoria_id, mentorado_email)
            VALUES ($1, $2)
            ON CONFLICT (mentoria_id, mentorado_email) DO NOTHING
            RETURNING mentoria_id, mentorado_email;
        """
        result = await conn.fetchrow(query_insert, mentoria_id, mentorado_email)

        return result is not None


# ... e para as outras funções de associação ...
async def remove_mentorado_from_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int,
    mentorado_email_obj: Optional[MentoradoEmail],
    current_user_email: str,
    current_user_type: UserType
) -> bool:
    async with db_conn_manager as conn:
        if(current_user_type == UserType.MENTOR):
            mentoria_record = await conn.fetchrow(
                "SELECT mentor_email FROM mentorias WHERE id = $1;",
                mentoria_id
            )
            if not mentorado_email_obj:
                return False

            if not mentoria_record or mentoria_record['mentor_email'] != current_user_email:
                return False

            query = """
                DELETE FROM mentoria_mentorados
                WHERE mentoria_id = $1 AND mentorado_email = $2
                RETURNING mentoria_id;
            """
            deleted_id = await conn.fetchval(query, mentoria_id, mentorado_email_obj.mentorado_email)
        else:
            query = """
                DELETE FROM mentoria_mentorados
                WHERE mentoria_id = $1 AND mentorado_email = $2
                RETURNING mentoria_id;
            """
            deleted_id = await conn.fetchval(query, mentoria_id, current_user_email)

        return deleted_id is not None

async def get_mentorados_for_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int
) -> Optional[List[EmailStr]]:
    async with db_conn_manager as conn:
        mentoria_exists = await conn.fetchval("SELECT 1 FROM mentorias WHERE id = $1;", mentoria_id)
        if not mentoria_exists:
            return None # Mentoria não encontrada

        query = """
            SELECT mentorado_email FROM mentoria_mentorados
            WHERE mentoria_id = $1;
        """
        rows = await conn.fetch(query, mentoria_id)
        return [row['mentorado_email'] for row in rows]
    
async def mentorado_in_mentoria(
    db_conn_manager: _AsyncGeneratorContextManager[asyncpg.Connection],
    mentoria_id: int,
    current_user_email: str
) -> MentoradoInMentoria:
    async with db_conn_manager as conn:
        query = """
            SELECT mentorado_email FROM mentoria_mentorados
            WHERE mentoria_id = $1 AND mentorado_email = $2;
        """
        row = await conn.fetchrow(query, mentoria_id, current_user_email)

        row = { "inscrito": row is not None }

        return MentoradoInMentoria.model_validate(row) if row else None