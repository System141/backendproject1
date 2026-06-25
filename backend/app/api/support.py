from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.domain import SupportTicket, User
from app.schemas.support import SupportTicketCreateRequest, SupportTicketUpdateRequest, SupportTicketResponse

support_router = APIRouter(prefix="/api/support", tags=["support"])


@support_router.post("/contact", status_code=status.HTTP_201_CREATED)
async def contact_form(
    req: SupportTicketCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public contact form — no auth required."""
    import uuid

    ticket = SupportTicket(
        id=str(uuid.uuid4()),
        user_id=None,
        subject=req.subject,
        message=req.message,
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
async def create_ticket(
    req: SupportTicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a support ticket. Any authenticated user can open a ticket."""
    import uuid

    ticket = SupportTicket(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        subject=req.subject,
        message=req.message,
        status="open",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return SupportTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        subject=ticket.subject,
        message=ticket.message,
        status=ticket.status,
        created_at=str(ticket.created_at) if ticket.created_at else "",
        updated_at=str(ticket.updated_at) if ticket.updated_at else "",
    )


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
    return [
        SupportTicketResponse(
            id=t.id,
            user_id=t.user_id,
            subject=t.subject,
            message=t.message,
            status=t.status,
            created_at=str(t.created_at) if t.created_at else "",
            updated_at=str(t.updated_at) if t.updated_at else "",
        )
        for t in tickets
    ]


# ========== ADMIN: List all tickets ==========
@support_router.get("/tickets", response_model=list[SupportTicketResponse])
async def admin_list_tickets(
    status_filter: str | None = Query(None, description="Filter by status (open, in_progress, resolved, closed)"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets with optional status filter. Admin only."""
    query = select(SupportTicket).order_by(desc(SupportTicket.created_at))
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        SupportTicketResponse(
            id=t.id,
            user_id=t.user_id,
            subject=t.subject,
            message=t.message,
            status=t.status,
            created_at=str(t.created_at) if t.created_at else "",
            updated_at=str(t.updated_at) if t.updated_at else "",
        )
        for t in tickets
    ]


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

    return SupportTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        subject=ticket.subject,
        message=ticket.message,
        status=ticket.status,
        created_at=str(ticket.created_at) if ticket.created_at else "",
        updated_at=str(ticket.updated_at) if ticket.updated_at else "",
    )
