from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
async def create_deposit_endpoint(deposit_data: DepositRequest):
    print(f"Recording payment event for email: {email}, booking_id: {booking_id}, reference: {reference}")
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
async def record_payment_event_endpoint(response: dict):  # Adjust type as needed
    print("Received response:", response)
    return True 


