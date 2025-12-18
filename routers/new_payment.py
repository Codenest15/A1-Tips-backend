# routers/new_payments.py
from fastapi import APIRouter, HTTPException
from utils.new_payment import DepositRequest, create_deposit, check_transaction_status

router = APIRouter(prefix="/payments", tags=["Payment"])

@router.post("/api/v1/create-deposit")
async def create_deposit_endpoint(deposit_data: DepositRequest):
    # Triggers the push notification
    return await create_deposit(deposit_data)

@router.get("/api/v1/check-status/{reference_id}")
async def check_status_endpoint(reference_id: str):
    # Frontend calls this every 5 seconds to see if user paid
    return await check_transaction_status(reference_id)
