from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.domain import SupportTicket, User
from app.schemas.support import SupportTicketCreateRequest, SupportTicketUpdateRequest, SupportTicketResponse

support_router = APIRouter(prefix="/api/support", tags=["support"])


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