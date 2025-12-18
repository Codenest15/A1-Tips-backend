# utils/new_payment.py

import aiohttp
import os
import uuid
import base64
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
MTN_URL = os.getenv("MTN_MOMO_URL")
MTN_SUB_KEY = os.getenv("MTN_COLLECTION_SUB_KEY")
MTN_USER = os.getenv("MTN_API_USER")
MTN_KEY = os.getenv("MTN_API_KEY")
MTN_ENV = os.getenv("MTN_TARGET_ENV", "sandbox")

# Updated Model: We need the Phone Number now!
class DepositRequest(BaseModel):
    vipamount: float
    currency: str = "EUR" # Sandbox only supports EUR usually. Change to GHS/UGX in prod.
    phoneNumber: str      # <--- REQUIRED for RequestToPay
    gameType: str
    email: str
    firstName: str
    lastName: str

async def get_momo_token():
    """Helper to get the Bearer Token from MTN"""
    url = f"{MTN_URL}/collection/token/"
    
    # Create Basic Auth String (User:Key)
    creds = f"{MTN_USER}:{MTN_KEY}"
    encoded_creds = base64.b64encode(creds.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_creds}",
        "Ocp-Apim-Subscription-Key": MTN_SUB_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            print(f"MTN Token Response Status: {resp.status} error: {resp}")
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Failed to get MTN Token")
            data = await resp.json()
            return data.get("access_token")

async def create_deposit(deposit_data: DepositRequest):
    """
    Initiates the RequestToPay (Push Notification to User)
    """
    token = await get_momo_token()
    reference_id = str(uuid.uuid4()) # Essential for MTN tracking

    # API Endpoint
    url = f"{MTN_URL}/collection/v1_0/requesttopay"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": reference_id,
        "X-Target-Environment": MTN_ENV,
        "Ocp-Apim-Subscription-Key": MTN_SUB_KEY,
        "Content-Type": "application/json"
    }
    
    # Calculate amount (Preserving your logic)
    final_amount = f"{deposit_data.vipamount / 10.7:.2f}"

    payload = {
        "amount": final_amount,
        "currency": "EUR",
        "externalId": deposit_data.gameType, # Use this to track what they are buying
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": deposit_data.phoneNumber # Format: 233xxxxxxxxx (No +)
        },
        "payerMessage": f"Pay for {deposit_data.gameType}",
        "payeeNote": f"Customer {deposit_data.email}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                # MTN returns 202 Accepted if successful (it's pending user action)
                if resp.status == 202:
                    return {
                        "status": "PENDING",
                        "message": "Payment prompt sent to user phone",
                        "referenceId": reference_id # Frontend needs this to check status!
                    }
                else:
                    text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=f"MTN Error: {text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def check_transaction_status(reference_id: str):
    """
    Checks if the user has entered their PIN
    """
    token = await get_momo_token()
    url = f"{MTN_URL}/collection/v1_0/requesttopay/{reference_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": MTN_ENV,
        "Ocp-Apim-Subscription-Key": MTN_SUB_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json() # Returns status: SUCCESSFUL, FAILED, or PENDING
            raise HTTPException(status_code=resp.status, detail="Could not fetch status")
