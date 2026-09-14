"""JWT and role helpers. Authentication is optional in demo mode but enforced in production."""
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.db import SessionLocal
from backend.models.db_models import Role, User
try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
except ImportError:  # demo-only environments may omit production auth extras
    JWTError = ValueError
    jwt = None
    CryptContext = None

SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto") if CryptContext else None
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)
ROLES = {"ADMIN", "ENGINEER", "SUPERVISOR", "ANALYST", "OPERATOR", "AUDITOR"}
def hash_password(password):
    if not pwd_context: raise RuntimeError("Install production authentication dependencies")
    return pwd_context.hash(password)
def verify_password(password, hashed):
    if not pwd_context: raise RuntimeError("Install production authentication dependencies")
    return pwd_context.verify(password, hashed)
def create_token(subject: str, roles: list[str]) -> str:
    if not jwt: raise RuntimeError("Install production authentication dependencies")
    return jwt.encode({"sub": subject, "roles": roles, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, SECRET, algorithm=ALGORITHM)
def current_user(token: str | None = Depends(oauth2)):
    if os.getenv("DEMO_MODE", "true").lower() == "true" and not token: return {"sub": "demo", "roles": ["ADMIN"]}
    if not token: raise HTTPException(401, "Authentication required")
    try:
        if not jwt: raise HTTPException(503, "Authentication dependencies are not installed")
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except JWTError as exc: raise HTTPException(401, "Invalid authentication token") from exc
def require_role(*roles):
    def dependency(user=Depends(current_user)):
        if not set(user.get("roles", [])) & set(roles): raise HTTPException(403, "Insufficient role")
        return user
    return dependency

def can_access_project(user: dict, owner_id: str | None, project_id: str | None = None) -> bool:
    """Central project/document filter used by repository queries and API handlers."""
    roles = set(user.get("roles", []))
    return bool({"ADMIN", "AUDITOR"} & roles) or owner_id is None or owner_id == user.get("sub")

def bootstrap_admin() -> None:
    """Create the first local administrator once, using environment-configured credentials."""
    if not SessionLocal:
        return
    email = os.getenv("ADMIN_EMAIL", "admin@gmail.com").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == email).first()
        legacy = session.query(User).filter(User.username == "admin@gmai.com").first()
        if legacy and email == "admin@gmail.com" and user and legacy.id != user.id:
            session.delete(legacy)
            session.commit()
        elif legacy and email == "admin@gmail.com" and not user:
            legacy.username = email
            session.commit()
            user = legacy
        if user:
            return
        roles = {role.name: role for role in session.query(Role).all()}
        for role_name in ROLES:
            if role_name not in roles:
                roles[role_name] = Role(name=role_name)
                session.add(roles[role_name])
        session.flush()
        user = User(username=email, password_hash=hash_password(password), is_active=True)
        user.roles.append(roles["ADMIN"])
        session.add(user)
        session.commit()

def authenticate_user(username: str, password: str) -> dict | None:
    if not SessionLocal:
        return None
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username.strip().lower()).first()
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            return None
        return {"sub": user.username, "roles": [role.name for role in user.roles]}

def _user_public(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "roles": sorted(role.name for role in user.roles),
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_activity": None,
    }

def create_local_user(username: str, password: str, roles: list[str]) -> dict:
    if not SessionLocal:
        raise RuntimeError("Database is not available.")
    email = username.strip().lower()
    selected_roles = sorted(set(roles))
    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not selected_roles or not set(selected_roles).issubset(ROLES):
        raise ValueError("One or more roles are invalid.")
    with SessionLocal() as session:
        if session.query(User).filter(User.username == email).first():
            raise ValueError("A user with this email already exists.")
        role_records = session.query(Role).filter(Role.name.in_(selected_roles)).all()
        user = User(username=email, password_hash=hash_password(password), is_active=True)
        user.roles.extend(role_records)
        session.add(user)
        session.commit()
        return _user_public(user)

def update_local_user(user_id: str, roles: list[str] | None = None, is_active: bool | None = None) -> dict:
    if not SessionLocal:
        raise RuntimeError("Database is not available.")
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise KeyError("User not found.")
        if roles is not None:
            selected_roles = sorted(set(roles))
            if not selected_roles or not set(selected_roles).issubset(ROLES):
                raise ValueError("One or more roles are invalid.")
            user.roles = session.query(Role).filter(Role.name.in_(selected_roles)).all()
        if is_active is not None:
            user.is_active = is_active
        session.commit()
        return _user_public(user)

def reset_local_password(user_id: str, password: str) -> dict:
    if not SessionLocal:
        raise RuntimeError("Database is not available.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise KeyError("User not found.")
        user.password_hash = hash_password(password)
        session.commit()
        return _user_public(user)

def delete_local_user(user_id: str, current_user_id: str) -> dict:
    if not SessionLocal:
        raise RuntimeError("Database is not available.")
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise KeyError("User not found.")
        if user.id == current_user_id:
            raise ValueError("You cannot delete your own administrator account.")
        if any(role.name == "ADMIN" for role in user.roles):
            admin_count = session.query(User).join(User.roles).filter(Role.name == "ADMIN", User.is_active.is_(True)).count()
            if admin_count <= 1:
                raise ValueError("The last active administrator cannot be deleted.")
        result = _user_public(user)
        session.delete(user)
        session.commit()
        return result

def list_local_users() -> list[dict]:
    if not SessionLocal:
        return []
    with SessionLocal() as session:
        return [_user_public(user) for user in session.query(User).order_by(User.username).all()]
