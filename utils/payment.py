from fastapi import Request, status, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import hmac
import hashlib
import json
import logging
from sqlalchemy import func
import requests
from datetime import datetime,timedelta

from models import (
    User,
    Purchase,
    Booking,
    AdminNotification,
)  # Replace with your actual model names
from database import get_db
from utils import notification
from fastapi.responses import JSONResponse  # Your session dependency

logger = logging.getLogger(__name__)


# async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
#     today = datetime.now()

#     secret_key = os.getenv("PAYSTACK_SK")
#     if not secret_key:
#         logger.error("Missing PAYSTACK_SK env var")
#         raise HTTPException(status_code=500, detail="Missing PAYSTACK_SK")

#     secret_key = secret_key.encode()

#     # 1️⃣  Verify signature
#     signature = request.headers.get("x-paystack-signature")
#     payload = await request.body()
#     expected_signature = hmac.new(
#         secret_key, msg=payload, digestmod=hashlib.sha512
#     ).hexdigest()

#     if signature != expected_signature:
#         logger.warning("Webhook signature mismatch")
#         return Response(status_code=status.HTTP_403_FORBIDDEN)

#     # 2️⃣  Parse event
#     try:
#         event = json.loads(payload)
#     except json.JSONDecodeError:
#         logger.exception("Invalid JSON in webhook")
#         return Response(status_code=400)

#     if event.get("event") != "charge.success":
#         return Response(status_code=200)  # ignore other events

#     data = event["data"]
#     reference = data.get("reference")
#     amount = data.get("amount")
#     # Convert amount from kobo (int) to naira (float)
#     if amount is not None:
#         amount = float(amount) / 100
#     email = data.get("customer", {}).get("email")
#     custom_fields = data.get("metadata", {}).get("custom_fields", [])
#     game_category = ""
#     username = None
#     for field in custom_fields:
#         if field.get("display_name") and field.get("game_category"):
#             username = field.get("display_name")
#             game_category = field.get("game_category")
#             break

#     # 3️⃣  Update database safely
#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         logger.error(f"User {username} not found")
#         return Response(status_code=404)

#     slip = (
#         db.query(Booking)
#         .filter(Booking.created_at == today.date(), Booking.category == game_category)
#         .first()
#     )
#     if not slip:
#         logger.error(f"Slip for {today.date()} and category {game_category} not found")
#         return Response(status_code=404)

#     # Idempotency check
#     purchase = db.query(Purchase).filter(Purchase.reference == reference).first()
#     if purchase:
#         logger.info(f"Duplicate webhook for {reference} – already processed")
#         return Response(status_code=200)

#     try:
#         new_purchase = Purchase(
#             reference=reference,
#             user_id=user.id,
#             booking_id=slip.id,
#             amount=amount,
#             email=email,
#         )

#         notification.create_admin_notification(
#             db=db,
#             message=f"New purchase by {user.username} for {game_category} on {today.strftime('%Y-%m-%d')}",
#         )

#         db.add(new_purchase)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         logger.exception(f"Could not create Purchase for {reference}")
#         return Response(status_code=500)

#     return Response(status_code=200)


async def record_payment_event(email: str, db: Session, booking_id, reference):
    get_user = db.query(User).filter(User.email == email).first()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    booking = (
        db.query(Booking)
        .filter(
            Booking.category == booking_id,
            Booking.created_at >= today,
            Booking.created_at < tomorrow
        )
        .first()
    )


    # fallback: if booking_id is category name, uncomment below
    # booking = db.query(Booking).filter(
    #     Booking.category == booking_id,
    #     func.date(Booking.created_at) == today
    # ).first()

    print(email, booking_id, reference)
    if not booking:
        print("Booking not found")
        raise HTTPException(status_code=404, detail="Booking not found")
    if not get_user:
        print("User not found")
        raise HTTPException(status_code=404, detail="User not found")
    new_purchase = Purchase(
        user_id=get_user.id,
        booking_id=booking.id,  # use the booking object's id
        purchase_date=datetime.now(),
        reference=reference,
        status="completed",
    )
    db.add(new_purchase)
    db.commit()


async def verify_payment(reference: str, db: Session = Depends(get_db)):
    headers = {
        "Authorization": "Bearer sk_live_abe69c578837a5f641744da6d1f6ed25df915383"
    }
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=headers)
    result = response.json()
    if result["status"]:

        # Mark payment as successful in your DB

        return JSONResponse({"status": "success"})
    return JSONResponse({"status": "failed"}, status_code=status.HTTP_400_BAD_REQUEST)


# make helper sync so callers don't accidentally return a coroutine
def get_booking(db: Session):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    booking = (
        db.query(Booking)
        .filter(
            Booking.category == "vip2",
            Booking.created_at >= today,
            Booking.created_at < tomorrow
        )
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

def number_of_purchases(db:Session):
    count = db.query(func.count(Purchase.id)).scalar()
    
    return count
