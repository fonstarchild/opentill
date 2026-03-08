from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, text

from backend.database import get_session
from backend.shared.domain.exceptions import NotFoundError, DomainException
from ..application.dtos import (
    OrderItemInputDTO,
    PlaceOrderCommand,
    ListOrdersQuery,
    OrderDTO,
    OrderItemDTO,
)
from ..application.use_cases import PlaceOrder, VoidOrder, GetOrder, ListOrders
from ..infrastructure.repository import SqlModelOrderRepository
from backend.catalog.infrastructure.repository import SqlModelProductRepository

router = APIRouter()


def get_order_repo(session: Session = Depends(get_session)) -> SqlModelOrderRepository:
    return SqlModelOrderRepository(session)


def get_product_repo(session: Session = Depends(get_session)) -> SqlModelProductRepository:
    return SqlModelProductRepository(session)


# ── Request/Response Schemas ──────────────────────────────────────────────────

class OrderItemInputRequest(BaseModel):
    product_id: int
    quantity: int


class OrderCreateRequest(BaseModel):
    items: List[OrderItemInputRequest]
    payment_method: str
    discount_amount: float = 0.0
    amount_received: float = 0.0
    notes: str = ""
    customer_name: str = ""
    customer_email: str = ""
    currency: str = "EUR"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=OrderDTO, status_code=201)
def create_order(
    data: OrderCreateRequest,
    session: Session = Depends(get_session),
):
    order_repo = SqlModelOrderRepository(session)
    product_repo = SqlModelProductRepository(session)
    try:
        cmd = PlaceOrderCommand(
            items=[OrderItemInputDTO(p.product_id, p.quantity) for p in data.items],
            payment_method=data.payment_method,
            discount_amount=data.discount_amount,
            amount_received=data.amount_received,
            notes=data.notes,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            currency=data.currency,
        )
        return PlaceOrder(order_repo, product_repo).execute(cmd)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.get("/", response_model=List[OrderDTO])
def list_orders(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    repo: SqlModelOrderRepository = Depends(get_order_repo),
):
    return ListOrders(repo).execute(ListOrdersQuery(
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    ))


# ── Metrics Endpoint ──────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(
    year: int = Query(default=datetime.now().year, ge=2000, le=2100),
    month: int = Query(default=datetime.now().month, ge=1, le=12),
    session: Session = Depends(get_session),
):
    # KPIs for the year
    kpi_row = session.exec(text("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COUNT(*) AS order_count,
            CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(total_amount), 0) / COUNT(*) ELSE 0 END AS avg_ticket
        FROM ordertable
        WHERE status = 'COMPLETED'
          AND strftime('%Y', created_at) = :year
    """), {"year": str(year)}).fetchone()

    # Best month by revenue
    best_month_row = session.exec(text("""
        SELECT CAST(strftime('%m', created_at) AS INTEGER) AS month
        FROM ordertable
        WHERE status = 'COMPLETED'
          AND strftime('%Y', created_at) = :year
        GROUP BY month
        ORDER BY SUM(total_amount) DESC
        LIMIT 1
    """), {"year": str(year)}).fetchone()

    # Daily sales for the given month
    daily_rows = session.exec(text("""
        SELECT
            CAST(strftime('%d', created_at) AS INTEGER) AS day,
            COALESCE(SUM(total_amount), 0) AS revenue,
            COUNT(*) AS orders
        FROM ordertable
        WHERE status = 'COMPLETED'
          AND strftime('%Y', created_at) = :year
          AND strftime('%m', created_at) = :month
        GROUP BY day
        ORDER BY day
    """), {"year": str(year), "month": f"{month:02d}"}).fetchall()

    # Monthly sales for the year
    monthly_rows = session.exec(text("""
        SELECT
            CAST(strftime('%m', created_at) AS INTEGER) AS month,
            COALESCE(SUM(total_amount), 0) AS revenue,
            COUNT(*) AS orders
        FROM ordertable
        WHERE status = 'COMPLETED'
          AND strftime('%Y', created_at) = :year
        GROUP BY month
        ORDER BY month
    """), {"year": str(year)}).fetchall()

    # By payment method
    payment_rows = session.exec(text("""
        SELECT
            payment_method AS method,
            COALESCE(SUM(total_amount), 0) AS revenue,
            COUNT(*) AS orders
        FROM ordertable
        WHERE status = 'COMPLETED'
          AND strftime('%Y', created_at) = :year
        GROUP BY payment_method
        ORDER BY revenue DESC
    """), {"year": str(year)}).fetchall()

    # Top 5 products by revenue
    top_products_rows = session.exec(text("""
        SELECT
            oi.product_name,
            COALESCE(SUM(oi.subtotal), 0) AS revenue,
            COALESCE(SUM(oi.quantity), 0) AS units
        FROM orderitem oi
        JOIN ordertable o ON oi.order_id = o.id
        WHERE o.status = 'COMPLETED'
          AND strftime('%Y', o.created_at) = :year
        GROUP BY oi.product_name
        ORDER BY revenue DESC
        LIMIT 5
    """), {"year": str(year)}).fetchall()

    return {
        "year": year,
        "month": month,
        "kpi": {
            "total_revenue": round(float(kpi_row[0]), 2),
            "order_count": int(kpi_row[1]),
            "avg_ticket": round(float(kpi_row[2]), 2),
            "best_month": int(best_month_row[0]) if best_month_row else None,
        },
        "daily": [
            {"day": int(r[0]), "revenue": round(float(r[1]), 2), "orders": int(r[2])}
            for r in daily_rows
        ],
        "monthly": [
            {"month": int(r[0]), "revenue": round(float(r[1]), 2), "orders": int(r[2])}
            for r in monthly_rows
        ],
        "by_payment": [
            {"method": r[0], "revenue": round(float(r[1]), 2), "orders": int(r[2])}
            for r in payment_rows
        ],
        "top_products": [
            {"product_name": r[0], "revenue": round(float(r[1]), 2), "units": int(r[2])}
            for r in top_products_rows
        ],
    }


@router.get("/{order_id}", response_model=OrderDTO)
def get_order(
    order_id: int,
    repo: SqlModelOrderRepository = Depends(get_order_repo),
):
    try:
        return GetOrder(repo).execute(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/void", response_model=OrderDTO)
def void_order(
    order_id: int,
    session: Session = Depends(get_session),
):
    order_repo = SqlModelOrderRepository(session)
    product_repo = SqlModelProductRepository(session)
    try:
        return VoidOrder(order_repo, product_repo).execute(order_id)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))
