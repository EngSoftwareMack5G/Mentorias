from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.models.mentoria import TokenData, UserType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # "token" é um endpoint fictício para o Swagger UI

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("username")
        user_type_str: Optional[str] = payload.get("type")

        if username is None or user_type_str is None:
            raise credentials_exception
        
        # Valida o tipo de usuário com o Enum
        try:
            user_type_enum = UserType(user_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user type: {user_type_str}"
            )
        
        token_data = TokenData(username=username, type=user_type_enum)

    except JWTError:
        raise credentials_exception
    except ValidationError: # Pydantic validation error for TokenData
        raise credentials_exception
    return token_data


# Sistema de autorização extensível
class RoleChecker:
    def __init__(self, allowed_roles: List[UserType]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: TokenData = Depends(get_current_user)):
        if current_user.type not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User type '{current_user.type.value}' not authorized for this endpoint. Allowed: {[role.value for role in self.allowed_roles]}"
            )
        return current_user

# Dependência específica para Mentor (poderia ser mais genérica se necessário)
async def get_current_active_mentor(current_user: TokenData = Depends(RoleChecker(allowed_roles=[UserType.MENTOR]))):
    return current_user

# Para gerar um token de teste (coloque em um endpoint de login real ou script separado)
# Exemplo:
# user_data_for_token = {"username": "mentor@example.com", "type": "Mentor"}
# token = create_access_token(data=user_data_for_token)
# print(f"Bearer {token}")