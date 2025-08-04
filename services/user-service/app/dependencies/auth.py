from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.api.v1.schemas.auth_schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/auth")

async def get_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise credentials_exception
    return token_data

def has_role(required_role: str):
    def role_checker(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
        if payload.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return payload
    return role_checker
