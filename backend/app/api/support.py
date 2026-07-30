import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.domain import SupportTicket, User
from app.schemas.support import SupportTicketCreateRequest, SupportTicketUpdateRequest, SupportTicketResponse
from app.api.auth import limiter

support_router = APIRouter(prefix="/api/support", tags=["support"])


def _to_response(t: SupportTicket) -> SupportTicketResponse:
    return SupportTicketResponse(
        id=t.id,
        user_id=t.user_id,
        subject=t.subject,
        message=t.message,
        category=t.category,
        lot_code=t.lot_code,
        status=t.status,
        created_at=str(t.created_at) if t.created_at else "",
        updated_at=str(t.updated_at) if t.updated_at else "",
    )


@support_router.post("/contact", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def contact_form(
    request: Request,
    req: SupportTicketCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public contact form — no auth required."""
    ticket = SupportTicket(
        id=str(uuid.uuid4()),
        user_id=None,
        subject=req.subject,
        message=req.message,
        category=req.category,
        lot_code=req.lot_code,
        status="open",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return {
        "ok": True,
        "message": "Your message has been received. We'll get back to you soon.",
    }


@support_router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_ticket(
    request: Request,
    req: SupportTicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a support ticket. Any authenticated user can open a ticket."""
    ticket = SupportTicket(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        subject=req.subject,
        message=req.message,
        category=req.category,
        lot_code=req.lot_code,
        status="open",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return _to_response(ticket)


@support_router.get("/tickets/my", response_model=list[SupportTicketResponse])
async def my_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's support tickets."""
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.user_id == current_user.id)
        .order_by(desc(SupportTicket.created_at))
    )
    tickets = result.scalars().all()
    return [_to_response(t) for t in tickets]


# ========== ADMIN: List all tickets ==========
@support_router.get("/tickets", response_model=list[SupportTicketResponse])
async def admin_list_tickets(
    status_filter: str | None = Query(None, description="Filter by status (open, in_progress, resolved, closed)"),
    category: str | None = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets with optional status/category filter. Admin only."""
    query = select(SupportTicket).order_by(desc(SupportTicket.created_at))
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)
    if category:
        query = query.where(SupportTicket.category == category)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return [_to_response(t) for t in tickets]


# ========== ADMIN: Update ticket status ==========
@support_router.put("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def admin_update_ticket(
    ticket_id: str,
    req: SupportTicketUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update support ticket status. Admin only."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = req.status
    await db.commit()
    await db.refresh(ticket)

    return _to_response(ticket)
