from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import aiohttp
import os
import uuid
from dotenv import load_dotenv
from utils.new_payment import DepositRequest, create_deposit
from utils.payment import record_payment_event
import logging, traceback

# Load environment variables (recommended practice)
load_dotenv()

router = APIRouter(prefix="/payments", tags=["Payment"])


@router.post("/api/v1/create-deposit")
async def create_deposit_endpoint(deposit_data: DepositRequest):  # use Pydantic model
    try:

        response = await create_deposit(deposit_data)
        return response
    except HTTPException as e:
        logging.exception("HTTPException in create_deposit_endpoint")
        # re-raise HTTPExceptions so FastAPI handles them normally
        raise e
    except Exception as e:
        # log full traceback to server stdout/console
        logging.exception("Unhandled exception in create_deposit_endpoint")
        # return full trace in JSON for debugging (remove in production)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/api/v1/record-payment-event")
async def record_payment_event_endpoint(response: dict,db: Session = Depends(get_db)):  # Adjust type as needed
    data = response.get("data", {})
    
    # 2. Access the required fields from the 'data' object
    #    Use .get() with a default value of {} for safety when accessing nested objects
    reference = data.get("reference") 
    email = data.get("customer", {}).get("email")
    booking_id = data.get("metadata", {}).get("game_type")
    status = data.get("status") 
    print("Payment Status:",status)
    if status == "canceled":
        return {"status":"canceled"}
    if status == "picked_up":
        return {"status":"picked_up"}# Adjust key
    if not reference or not email or not booking_id:
        raise HTTPException(status_code=400, detail="Missing required payment event data")
    
    try:
        await record_payment_event(email=email, db=db, booking_id=booking_id, reference=reference)
    except Exception as e:
        logging.exception("Error recording payment event")
        raise HTTPException(status_code=500, detail="Failed to record payment event")
    # Assuming response is available in this context
    return {"status": "success"}



