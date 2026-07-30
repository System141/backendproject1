"""Legal document API (doc §15): versioned content + user acceptance audit trail."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import TermsDocument, TermsAcceptance, User
from app.schemas.legal import TermsDocumentResponse, TermsAcceptanceCreate, TermsAcceptanceResponse

legal_router = APIRouter(prefix="/api/legal", tags=["legal"])


@legal_router.get("/{document_type}", response_model=TermsDocumentResponse)
async def get_active_document(document_type: str, db: AsyncSession = Depends(get_db)):
    """Public: latest active version of a legal document (Terms of Use, Privacy
    Policy, etc). 404 until LITZOR's legal counsel-approved text is loaded (§15)."""
    result = await db.execute(
        select(TermsDocument)
        .where(TermsDocument.document_type == document_type, TermsDocument.is_active == True)  # noqa: E712
        .order_by(desc(TermsDocument.created_at))
        .limit(1)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="No active document of this type")
    return doc


@legal_router.post("/accept", response_model=TermsAcceptanceResponse, status_code=201)
async def accept_terms(
    req: TermsAcceptanceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record that the current user accepted a specific document version, with
    a server timestamp (doc §15.1/§15.2/§15.3). Never updated - a material
    update requiring re-consent is a new row, not an edit."""
    exists = await db.execute(
        select(TermsDocument).where(
            TermsDocument.document_type == req.document_type,
            TermsDocument.version == req.version,
        )
    )
    if not exists.scalars().first():
        raise HTTPException(status_code=404, detail="No such document version was ever published")

    acceptance = TermsAcceptance(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        document_type=req.document_type,
        version=req.version,
        ip_address=request.client.host if request.client else None,
    )
    db.add(acceptance)
    await db.commit()
    await db.refresh(acceptance)
    return acceptance
