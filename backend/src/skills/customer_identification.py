"""
Skill: Customer Identification
When to use: On EVERY incoming message
Purpose: Resolve customer identity by email or phone
"""
from src.database.connection import get_pool
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class CustomerIdentity:
    """Customer identity result."""
    customer_id: str
    email: str | None
    phone: str | None
    is_new: bool


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Validate E.164 phone format."""
    pattern = r"^\+?[1-9]\d{1,14}$"
    return bool(re.match(pattern, phone.replace("-", "").replace(" ", "")))


async def resolve_customer(email: str | None = None, phone: str | None = None) -> CustomerIdentity:
    """
    Resolve customer by email or phone.
    Creates new customer if not found.
    
    Args:
        email: Customer email (primary identifier)
        phone: Customer phone (secondary identifier)
        
    Returns:
        CustomerIdentity with customer_id and metadata
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Try email first
        if email:
            row = await conn.fetchrow(
                "SELECT id, email, phone FROM customers WHERE email = $1",
                email,
            )
            if row:
                return CustomerIdentity(
                    customer_id=str(row["id"]),
                    email=row["email"],
                    phone=row["phone"],
                    is_new=False,
                )

        # Try phone
        if phone:
            row = await conn.fetchrow(
                "SELECT id, email, phone FROM customers WHERE phone = $1",
                phone,
            )
            if row:
                return CustomerIdentity(
                    customer_id=str(row["id"]),
                    email=row["email"],
                    phone=row["phone"],
                    is_new=False,
                )

        # Create new customer
        async with conn.transaction():
            customer_id = await conn.fetchval(
                """
                INSERT INTO customers (email, phone)
                VALUES ($1, $2)
                RETURNING id
                """,
                email, phone,
            )
            return CustomerIdentity(
                customer_id=str(customer_id),
                email=email,
                phone=phone,
                is_new=True,
            )


async def link_customer_email_phone(customer_id: str, email: str, phone: str) -> None:
    """
    Link email and phone to existing customer.
    
    Args:
        customer_id: Existing customer ID
        email: Email to link
        phone: Phone to link
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE customers SET email = $1, phone = $2
            WHERE id = $3
            """,
            email, phone, customer_id,
        )
