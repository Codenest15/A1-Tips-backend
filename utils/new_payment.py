from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
import os
import uuid
from dotenv import load_dotenv


# Load environment variables (recommended practice)
load_dotenv() 



# --- Configuration (Use environment variables for security) ---
# NOTE: Replace these with your actual details and store them in a .env file https://api.useaccrue.com/cashramp/api/graphql

CASHRAMP_API_URL = os.getenv("CASHRAMP_API_URL", "https://api.useaccrue.com/cashramp/api/graphql")
CASHRAMP_API_KEY = os.getenv("CASHRAMP_API_KEY", "CSHRMP-SECK_tZXqffHth67AqAL2") 

# This is the URL Cashramp will redirect the user to after a successful/failed payment
SUCCESS_REDIRECT_URL = "https://www.a1-tips.com/" 

# Allowed currency enum values (update to match provider docs)
ALLOWED_CURRENCIES = {"USD", "GHS", "NGN"}

# Pydantic model for the data expected from the frontend
class DepositRequest(BaseModel):
    vipamount: float
    countryCode: str
    gameType: str
    email: str
    firstName: str      # <-- added (required)
    lastName: str       # <-- added (required)


async def create_deposit(deposit_data: DepositRequest):
    print("Creating deposit with data:", deposit_data)
    print("Using CASHRAMP_API_URL:", CASHRAMP_API_URL)
    # 1. Define the GraphQL Mutation and Variables
    query = """
        mutation InitiateHostedPayment(
            $amount: Decimal!, $countryCode: String!,
            $email: String!, 
            $redirectUrl: String!, $reference: String!
            $firstName: String!, $lastName: String!
        ) {
            initiateHostedPayment(
                paymentType: deposit
                amount: $amount
                currency: usd
                countryCode: $countryCode
                email: $email
                redirectUrl: $redirectUrl
                reference: $reference
                firstName: $firstName
                lastName: $lastName
            ) {
                id
                hostedLink
                status
            }
        }
    """
    
    # Generate a unique reference ID for reconciliation
    reference_id = str(uuid.uuid4())
    
    variables = {
        "amount": deposit_data.vipamount,
        "countryCode": deposit_data.countryCode,
        "email": deposit_data.email,
        "firstName": deposit_data.firstName,  # <-- include
        "lastName": deposit_data.lastName,    # <-- include
        "redirectUrl": SUCCESS_REDIRECT_URL,
        "reference": reference_id,
    }
    
    headers = {
        "Authorization": f"Bearer {CASHRAMP_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "variables": variables,
    }

    try:
        # 2. Make the asynchronous API call to Cashramp using aiohttp
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(CASHRAMP_API_URL, json=payload, headers=headers) as resp:
                text = await resp.text()
                status = resp.status
                try:
                    cashramp_response = await resp.json()
                except Exception:
                    cashramp_response = None

        if status >= 400:
            print(f"Cashramp returned status={status}, body={text}")
            raise HTTPException(status_code=502, detail=f"Payment provider returned status {status}")

        # 3. Check for GraphQL errors
        if not cashramp_response:
            print("Cashramp returned non-json response:", text)
            raise HTTPException(status_code=502, detail="Payment provider returned non-json response")

        if 'errors' in cashramp_response:
            print("GraphQL Errors:", cashramp_response['errors'])
            # Propagate provider errors back to the caller so they can be inspected
            raise HTTPException(status_code=400, detail=cashramp_response['errors'])

        # 4. Debug: log full provider response (helps when hostedLink is missing)
        print("Cashramp response:", cashramp_response)

        # Extract and return the hosted link
        hosted_obj = cashramp_response.get('data', {}).get('initiateHostedPayment') if isinstance(cashramp_response, dict) else None
        hosted_link = None
        if hosted_obj and isinstance(hosted_obj, dict):
            hosted_link = hosted_obj.get('hostedLink')

        if not hosted_link:
            # Return provider response to caller for debugging (don't leak secrets in production)
            raise HTTPException(status_code=502, detail={
                "message": "Cashramp did not return a hostedLink",
                "provider_response": cashramp_response
            })
        if hosted_link:

    

        return {"hostedLink": hosted_link}

    except HTTPException:
        # Let FastAPI HTTPExceptions pass through unchanged
        raise

    except aiohttp.ClientConnectorError as e:
        import traceback
        tb = traceback.format_exc()
        print("aiohttp.ClientConnectorError:", e)
        print(tb)
        raise HTTPException(status_code=502, detail=f"Network error: {e}")
    except aiohttp.ClientResponseError as e:
        print("aiohttp.ClientResponseError:", e)
        raise HTTPException(status_code=502, detail=f"Payment provider returned error: {e}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("Unexpected error:", e)
        print(tb)
        raise HTTPException(status_code=500, detail=f"{e.__class__.__name__}: {e}")



