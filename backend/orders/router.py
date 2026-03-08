from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session
from ..catalog.models import Product
from .models import Order, OrderItem, OrderCreate, OrderOut, OrderItemOut

router = APIRouter()

# ── Reference generator ────────────────────────────────────────────────────────

def _next_reference(session: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"OT-{today}-"
    existing = session.exec(
        select(Order).where(Order.reference.startswith(prefix))
    ).all()
    seq = len(existing) + 1
    return f"{prefix}{seq:04d}"


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, session: Session = Depends(get_session)):
    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    order_items = []
    subtotal = 0.0

    for item_input in data.items:
        product = session.get(Product, item_input.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item_input.product_id} not found",
            )
        if product.stock < item_input.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}' (available: {product.stock})",
            )
        line_total = round(product.price * item_input.quantity, 2)
        subtotal += line_total
        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price=product.price,
                tax_rate=product.tax_rate,
                quantity=item_input.quantity,
                total_price=line_total,
            )
        )

    discount = round(data.discount_amount, 2)
    total = round(max(subtotal - discount, 0), 2)
    change = round(max(data.amount_received - total, 0), 2) if data.payment_method == "CASH" else 0.0

    order = Order(
        reference=_next_reference(session),
        subtotal=subtotal,
        discount_amount=discount,
        total=total,
        payment_method=data.payment_method,
        amount_received=data.amount_received,
        change_given=change,
        notes=data.notes,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
    )
    session.add(order)
    session.flush()  # get order.id before adding items

    for oi in order_items:
        oi.order_id = order.id
        session.add(oi)
        # Deduct stock
        product = session.get(Product, oi.product_id)
        product.stock -= oi.quantity
        session.add(product)

    session.commit()
    session.refresh(order)
    return _to_out(order)


@router.get("/", response_model=List[OrderOut])
def list_orders(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    session: Session = Depends(get_session),
):
    q = select(Order)
    if date_from:
        q = q.where(Order.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.where(Order.created_at <= datetime.combine(date_to, datetime.max.time()))
    q = q.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    orders = session.exec(q).all()
    return [_to_out(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _to_out(order)


@router.post("/{order_id}/void", response_model=OrderOut)
def void_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Cannot void order with status {order.status}")
    # Restore stock
    for item in order.items:
        product = session.get(Product, item.product_id)
        if product:
            product.stock += item.quantity
            session.add(product)
    order.status = "VOID"
    session.add(order)
    session.commit()
    session.refresh(order)
    return _to_out(order)


def _to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        reference=order.reference,
        created_at=order.created_at,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        total=order.total,
        payment_method=order.payment_method,
        amount_received=order.amount_received,
        change_given=order.change_given,
        notes=order.notes,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        status=order.status,
        items=[
            OrderItemOut(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product_name,
                product_sku=i.product_sku,
                unit_price=i.unit_price,
                tax_rate=i.tax_rate,
                quantity=i.quantity,
                total_price=i.total_price,
            )
            for i in order.items
        ],
    )
