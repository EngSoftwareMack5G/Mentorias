from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import mentoria_router
from app.database.session import connect_db, close_db, create_tables_if_not_exist # Adicionado create_tables_if_not_exist
from app.core.config import settings # Para debug, se necessário

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Iniciando aplicação...")
    await connect_db()
    # Opcional: Criar tabelas se não existirem ao iniciar (para desenvolvimento)
    # Em produção, é melhor usar migrations (ex: Alembic)
    await create_tables_if_not_exist() 
    yield
    # Shutdown
    print("Encerrando aplicação...")
    await close_db()

app = FastAPI(
    title="Microsserviço de Gerenciamento de Mentorias",
    description="API para gerenciar mentorias e seus participantes.",
    version="0.1.0",
    lifespan=lifespan # Novo modo de definir startup/shutdown events
)

app.include_router(mentoria_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique sua origem, por exemplo: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # ou ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"],  # ou ["Authorization", "Content-Type"]
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo ao Microsserviço de Mentorias!"}

# Para gerar um token JWT de teste (apenas para desenvolvimento):
# Remova ou proteja este endpoint em produção!
from app.auth.security import create_access_token, UserType # Adicionado UserType
@app.post("/token/generate_test", tags=["Development"])
async def generate_test_token(email: str = "mentor@example.com", user_type: UserType = UserType.MENTOR):
    """Gera um token de teste para o email e tipo fornecidos."""
    token_data = {"username": email, "type": user_type.value}
    token = create_access_token(data=token_data)
    return {"access_token": token, "token_type": "bearer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)