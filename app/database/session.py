import asyncpg
from app.core.config import settings
from contextlib import asynccontextmanager

# Variável global para o pool de conexões
db_pool = None

async def connect_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=5,  # Mínimo de conexões no pool
            max_size=20  # Máximo de conexões no pool
        )
        print("Conexão com o banco de dados estabelecida e pool criado.")
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        # Tratar erro de conexão, talvez tentar reconectar ou sair da aplicação
        raise

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Pool de conexões com o banco de dados fechado.")

@asynccontextmanager
async def get_db_connection():
    """
    Obtém uma conexão do pool.
    """
    if not db_pool:
        # Isso não deveria acontecer se connect_db foi chamado no startup
        raise RuntimeError("Database pool is not initialized. Call connect_db() first.")
    
    conn = None
    try:
        conn = await db_pool.acquire()
        yield conn
    finally:
        if conn:
            await db_pool.release(conn)

# Exemplo de função para executar os creates (opcional, pode ser feito manualmente)
async def create_tables_if_not_exist():
    async with get_db_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mentorias (
                id SERIAL PRIMARY KEY,
                mentor_email VARCHAR(255) NOT NULL,
                data_hora TIMESTAMP NOT NULL,
                duracao_minutos INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('agendada', 'concluída', 'cancelada', 'disponível')),
                topico TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mentoria_mentorados (
                mentoria_id INTEGER NOT NULL REFERENCES mentorias(id) ON DELETE CASCADE,
                mentorado_email VARCHAR(255) NOT NULL,
                PRIMARY KEY (mentoria_id, mentorado_email)
            );
        """)
        print("Tabelas verificadas/criadas.")