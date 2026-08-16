"""One-off: create (or promote) a super_admin account directly in the DB.

Run on the server, from backend/, with the same env as the app (so it hits
the same DATABASE_URL):

    python scripts/create_super_admin.py [email] [password]

Defaults to admin@bidmont.me / 123456 if not given. Change the password
after first login - this exists because /api/admin/seed can only mint a
plain "admin", never a super_admin, and there's no other bootstrap path.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.domain import User, UserRole


async def main(email: str, password: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user:
            user.role = UserRole.super_admin
            user.status = "active"
            user.password_hash = hash_password(password)
            user.email_verified = True
            print(f"Updated existing user {email} -> super_admin, password reset.")
        else:
            user = User(
                name="Super Admin",
                email=email,
                password_hash=hash_password(password),
                role=UserRole.super_admin,
                status="active",
                accepted_terms=True,
                accepted_privacy=True,
                email_verified=True,
            )
            db.add(user)
            print(f"Created super_admin {email}.")
        await db.commit()


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@bidmont.me"
    password = sys.argv[2] if len(sys.argv) > 2 else "123456"
    asyncio.run(main(email, password))
    print("Done. Log in and change the password.")
