import requests
from models import User

def send_sms(recipient:list, message:str):
    endPoint = 'https://api.mnotify.com/api/sms/quick'
    apiKey = 'JKYSiTuEvlc3q5XU5HAvEb8Kp'
    url = endPoint + '?key=' + apiKey

    data = {
        "recipient": recipient,
        "sender": "A1-Tips",
        "message": message,
        "is_schedule": False,
        "schedule_date": "",
    }

    response = requests.post(url, json=data)
    return response.json()
# def send_sms(recipients: list, message: str):
#     client = requests.Session()

#     headers = {
#         "api-key": "WW9DeFFEdW9oSUxMTXFwR3hUaEw",
#         "Content-Type": "application/json"
#     }

#     base_url = "https://sms.arkesel.com/api/v2/sms/send"

    

#     # SEND SMS
#     sms_payload = {
#         "sender": "Hello world",
#         "message": "Welcome to Arkesel SMS API v2. Please enjoy the experience.",
#         "recipients": recipients
#         # When sending SMS to Nigerian recipients, specify the use_case field
#         # "use_case": "promotional"
#     }

#     try:
#         response = client.post(base_url, headers=headers, json=sms_payload)
#         response.raise_for_status()
#         print(response.text)
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")

def get_all_users_number(db):
    users = db.query(User).filter(User.is_superuser==0).all()
    numbers = [user.phone_number for user in users if user.phone_number]
    return numbers


def send_bulk_sms(db, message: str):
    numbers = get_all_users_number(db)
    if not numbers:
        return {"status": "error", "message": "No user phone numbers found."}
    
    response = send_sms(numbers, message)
    return response

def send_to_specific_numbers(phone_numbers: list, message: str):
    phone_numbers = list(set(phone_numbers))  # Remove duplicates
    if not phone_numbers:
        return {"status": "error", "message": "No phone numbers provided."}
    
    response = send_sms(phone_numbers, message)
    return response

def send_individual_sms(db, phone_number: str, message: str):
    if not phone_number:
        return {"status": "error", "message": "Phone number is required."}
    
    response = send_sms([phone_number], message)
    return response
