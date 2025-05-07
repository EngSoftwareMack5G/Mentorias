# Microsserviço de Gerenciamento de Mentorias

Este microsserviço é responsável pelo gerenciamento de mentorias, permitindo que mentores criem, atualizem, listem e deletem suas mentorias, além de gerenciar os mentorados associados a cada uma.

## Tecnologias Utilizadas

*   **Framework:** FastAPI
*   **Banco de Dados:** PostgreSQL
*   **Driver Banco de Dados:** asyncpg
*   **Autenticação:** JWT (JSON Web Tokens)
*   **Validação de Dados:** Pydantic

## Estrutura do Banco de Dados (PostgreSQL)

As seguintes tabelas são utilizadas:

1.  **`mentorias`**: Armazena informações sobre cada mentoria.
    ```sql
    CREATE TABLE mentorias (
        id SERIAL PRIMARY KEY,
        mentor_email VARCHAR(255) NOT NULL,
        data_hora TIMESTAMP NOT NULL,
        duracao_minutos INTEGER NOT NULL,
        status VARCHAR(20) NOT NULL CHECK (status IN ('agendada', 'concluída', 'cancelada', 'disponível')),
        topico VARCHAR(20) NOT NULL CHECK (topico IN ('carreiras', 'lideranças', 'financeiro', 'negócios')),
        titulo TEXT NOT NULL,
        descricao TEXT
    );
    ```

2.  **`mentoria_mentorados`**: Tabela de associação para vincular mentorados a mentorias.
    ```sql
    CREATE TABLE mentoria_mentorados (
        mentoria_id INTEGER NOT NULL REFERENCES mentorias(id) ON DELETE CASCADE,
        mentorado_email VARCHAR(255) NOT NULL,
        PRIMARY KEY (mentoria_id, mentorado_email)
    );
    ```

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis. Um arquivo `.env.example` pode ser fornecido como referência.

| Variável                  | Descrição                                                                 | Exemplo (no `.env`)                  |
| :------------------------ | :------------------------------------------------------------------------ | :----------------------------------- |
| `DB_USER`                 | Usuário do banco de dados PostgreSQL.                                     | `postgres`                           |
| `DB_PASSWORD`             | Senha do usuário do banco de dados.                                       | `seu_password_seguro`                |
| `DB_HOST`                 | Host onde o PostgreSQL está rodando.                                      | `localhost`                          |
| `DB_PORT`                 | Porta do PostgreSQL.                                                      | `5432`                               |
| `DB_NAME`                 | Nome do banco de dados a ser utilizado.                                   | `mentoria_db`                        |
| `SECRET_KEY`              | Chave secreta para assinatura de tokens JWT. **Deve ser forte e única.** | `segredo_super_top_realmente_secreto` |
| `ALGORITHM`               | Algoritmo usado para os tokens JWT.                                       | `HS256`                              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do token JWT em minutos.                             | `30`                                 |

## API Endpoints

Todos os endpoints protegidos requerem um token JWT no header `Authorization: Bearer <seu_token>`.
A maioria das operações de escrita e gerenciamento exige que o tipo de usuário no token seja `"Mentor"`.

### Mentorias

1.  **Criar Nova Mentoria**
    *   **Endpoint:** `POST /mentorias`
    *   **Autorização:** JWT (Tipo: `Mentor`)
    *   **Request Body:**
        ```json
        {
          "data_hora": "2024-08-15T14:00:00Z", // Formato ISO 8601 UTC
          "duracao_minutos": 60,
          "status": "agendada", //ou 'disponível'
          "topico": "carreiras", //carreiras, lideranças, financeiro ou negócios
          "titulo": "TITULO",
          "descrição": "Descrição" //Pode ser nulo
        }
        ```
    *   **Response:** `201 CREATED` - Objeto da mentoria criada.

2.  **Listar Mentorias do Mentor**
    *   **Endpoint:** `GET /mentorias`
    *   **Autorização:** JWT (Tipo: `Mentor`)
    *   **Response:** `200 OK` - Lista de objetos de mentoria do mentor autenticado.

3.  **Buscar Mentoria Específica**
    *   **Endpoint:** `GET /mentorias/{mentoria_id}`
    *   **Autorização:** JWT (Qualquer tipo de usuário autenticado)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Response:** `200 OK` - Objeto da mentoria.

4.  **Atualizar Mentoria**
    *   **Endpoint:** `PUT /mentorias/{mentoria_id}`
    *   **Autorização:** JWT (Tipo: `Mentor` - proprietário da mentoria)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Request Body (parcialmente, apenas campos a atualizar):**
        ```json
        {
          "data_hora": "2024-08-15T15:00:00Z",
          "status": "concluída"
        }
        ```
    *   **Response:** `200 OK` - Objeto da mentoria atualizada.

5.  **Deletar Mentoria**
    *   **Endpoint:** `DELETE /mentorias/{mentoria_id}`
    *   **Autorização:** JWT (Tipo: `Mentor` - proprietário da mentoria)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Response:** `204 NO CONTENT`

### Gerenciamento de Mentorados em uma Mentoria

1.  **Adicionar Mentorado a uma Mentoria**
    *   **Endpoint:** `POST /mentorias/{mentoria_id}/mentorados`
    *   **Autorização:** JWT (Tipo: `Mentor` - proprietário da mentoria)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Request Body:**
        ```json
        {
          "mentorado_email": "mentorado@example.com"
        }
        ```
    *   **Response:** `201 CREATED` - Mensagem de sucesso.

2.  **Remover Mentorado de uma Mentoria**
    *   **Endpoint:** `DELETE /mentorias/{mentoria_id}/mentorados`
    *   **Autorização:** JWT (Tipo: `Mentor` - proprietário da mentoria)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Query Parameter:** `mentorado_email` (string) - Email do mentorado a ser removido.
        *   Exemplo: `/mentorias/1/mentorados?mentorado_email=aluno@example.com`
    *   **Response:** `204 NO CONTENT`

3.  **Listar Mentorados de uma Mentoria**
    *   **Endpoint:** `GET /mentorias/{mentoria_id}/mentorados`
    *   **Autorização:** JWT (Qualquer tipo de usuário autenticado)
    *   **Path Parameter:** `mentoria_id` (integer) - ID da mentoria.
    *   **Response:** `200 OK` - Lista de emails dos mentorados.
        ```json
        [
          "mentorado1@example.com",
          "mentorado2@example.com"
        ]
        ```

### Autenticação (Exemplo para Teste)

*   **Gerar Token de Teste (APENAS DESENVOLVIMENTO):**
    *   **Endpoint:** `POST /token/generate_test`
    *   **Autorização:** Nenhuma
    *   **Query Parameters:**
        *   `email` (string, opcional, default: `mentor@example.com`)
        *   `user_type` (string, opcional, default: `Mentor`. Valores possíveis: `Mentor`, `Mentorado`, `Admin`)
    *   **Response:** `200 OK`
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```

## Como Rodar Localmente

1.  **Pré-requisitos:**
    *   Python 3.9+
    *   PostgreSQL instalado e rodando.
    *   Git

2.  **Clone o repositório:**
    ```bash
    git clone <url_do_seu_repositorio>
    cd nome_do_repositorio
    ```

3.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure as variáveis de ambiente:**
    *   Copie `.env.example` para `.env` (se existir um example).
    *   Edite o arquivo `.env` com as suas configurações do banco de dados e uma `SECRET_KEY` forte.

6.  **Crie o banco de dados** no PostgreSQL com o nome especificado em `DB_NAME`. As tabelas serão criadas automaticamente na primeira execução da aplicação (configurado no `lifespan`).

7.  **Execute a aplicação:**
    ```bash
    uvicorn app.main:app --reload
    ```
    A flag `--reload` faz o servidor reiniciar automaticamente após alterações no código (útil para desenvolvimento).

8.  **Acesse a documentação interativa (Swagger UI):**
    Abra seu navegador e vá para `http://127.0.0.1:8000/docs`.

## Próximos Passos (Sugestões)

*   Implementar um sistema de login real (em vez do `generate_test_token`).
*   Adicionar testes unitários e de integração.
*   Configurar migrations de banco de dados (ex: Alembic).
*   Melhorar o tratamento de erros e logging.
*   Paginação para listas longas.
