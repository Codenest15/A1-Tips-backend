from schemas import User, AdminUser
import models
from hashing import Hash
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from utils import notification
def add_user(request:User, db: Session):
    # Check for existing user by username, email, or phone number in a single query
    existing_user = db.query(models.User).filter(
        (models.User.username == request.username) |
        (models.User.email == request.email) |
        (models.User.phone_number == request.phone_number)
    ).first()
    if existing_user:
        if existing_user.username == request.username:
            detail = f"User with username already exists"
        elif existing_user.email == request.email:
            detail = f"User with email already exists"
        else:
            detail = f"User with phone number already exists"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    hashed_password = Hash().bcrypt(request.password)
    new_user = models.User(
        username=request.username,
        email=request.email,
        password=hashed_password,
        phone_number=request.phone_number,
        is_active=1,
        is_superuser=1 if request.is_superuser else 0,
        is_staff= 1 if request.is_staff else 0

    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    notification.create_admin_notification(db, f"New user registered: {new_user.username}")
    return new_user

def get_user(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found"
        )
    return user
    
#get total number of users
def get_total_users(db: Session):
    total_users = db.query(models.User).count()
    return total_users

def get_all_users(db: Session):
    users = db.query(models.User).all()
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone_number,
            "status": "active" if user.is_active else "inactive"
        })
    return result

def add_admin_user(request: AdminUser, db: Session):
    # Check for existing admin user by email or phone number
    existing_admin = db.query(models.User).filter(
        (models.User.email == request.email) |
        (models.User.phone_number == request.phone_number)
    ).first()
    if existing_admin:
        if existing_admin.email == request.email:
            detail = f"Admin user with email {request.email} already exists"
        else:
            detail = f"Admin user with phone number {request.phone_number} already exists"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    hashed_password = Hash().bcrypt(request.password)
    new_admin = models.User(
        username=request.username,
        email=request.email,
        password=hashed_password,
        phone_number=request.phone_number,
        is_active=1,
        is_superuser=1,
        is_staff=1
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    notification.create_admin_notification(db, f"New admin user registered: {new_admin.username}")
    return new_admin

def get_admins(db: Session):
    admins = db.query(models.User).filter(models.User.is_superuser == 1).all()
    return admins

def get_users_purchases_for_today(email: str, db: Session):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # fetch distinct categories the user bought today
    categories = (
        db.query(models.Booking.category)
        .join(models.Purchase, models.Booking.id == models.Purchase.booking_id)
        .join(models.User, models.Purchase.user_id == models.User.id)
        .filter(
            models.User.email == email,
            models.Purchase.purchase_date >= today,
            models.Purchase.purchase_date < tomorrow,
        )
        .distinct()
        .all()
    )
    bought = {c[0] for c in categories}  # extract category strings

    # return flags for vip1..vip3
    result = {f"vip{i}": (f"vip{i}" in bought) for i in range(1, 4)}
    return result

def get_user_purchased_games(email: str, db: Session):
    bookings = (
        db.query(models.Booking)
        .join(models.Purchase, models.Booking.id == models.Purchase.booking_id)
        .join(models.User, models.Purchase.user_id == models.User.id)
        .filter(models.User.email == email)
        .all()
    )
    result = []
    for booking in bookings:
        games = []
        for game in booking.games:
            games.append({
                "home_team": game.home_team,
                "away_team": game.away_team,
                "tournament": game.tournament,
                "sport": game.sport,
                "odds": game.odds,
                "prediction": game.prediction,
                "match_status": game.match_status,
                "match_day": game.match_day
            })
        result.append({
            "booking_id": booking.id,
            "share_code": booking.share_code,
            "share_url": booking.share_url,
            "deadline": booking.deadline,
            "category": booking.category,
            "sold_out": booking.sold_out,
            "created_at": booking.created_at,
            "price": booking.price,
            "games": games
        })
    return result
