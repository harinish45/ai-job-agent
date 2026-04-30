"""
Platform credential management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User, PlatformCredential
from app.core.security import get_current_user, encrypt_credentials, decrypt_credentials
from app.schemas.schemas import CredentialCreate, CredentialResponse

router = APIRouter(prefix="/credentials", tags=["credentials"])

@router.get("", response_model=list[CredentialResponse])
def get_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = db.query(PlatformCredential).filter(
        PlatformCredential.user_id == current_user.id
    ).all()

    return [
        {
            "id": c.id,
            "platform": c.platform,
            "is_active": c.is_active,
            "last_used": c.last_used,
        }
        for c in creds
    ]

@router.post("")
def create_credential(
    data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(PlatformCredential).filter(
        PlatformCredential.user_id == current_user.id,
        PlatformCredential.platform == data.platform
    ).first()

    if existing:
        existing.username_encrypted = encrypt_credentials(data.username)
        existing.password_encrypted = encrypt_credentials(data.password)
        existing.is_active = True
    else:
        cred = PlatformCredential(
            user_id=current_user.id,
            platform=data.platform,
            username_encrypted=encrypt_credentials(data.username),
            password_encrypted=encrypt_credentials(data.password),
        )
        db.add(cred)

    db.commit()
    return {"status": "saved"}

@router.delete("/{cred_id}")
def delete_credential(
    cred_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cred = db.query(PlatformCredential).filter(
        PlatformCredential.id == cred_id,
        PlatformCredential.user_id == current_user.id
    ).first()

    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    db.delete(cred)
    db.commit()
    return {"status": "deleted"}
