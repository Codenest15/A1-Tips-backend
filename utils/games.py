from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from utils import sporty as sporty_games
from Oauth2 import get_current_user, get_admin_user
from typing import Annotated
from schemas import BookingResponse, Booking  # Import your Pydantic schema
from datetime import datetime, timedelta
from models import Booking, Game  # Make sure to import Game
from fastapi import HTTPException


# Endpoint to get booking details by share code
def load_booking(share_code: str, db: Session):
    booking = sporty_games.get_booking(share_code)
    if not booking:
        return {"error": "Booking not found"}
    return booking


def upload_booking(request: BookingResponse, db: Session):
    # Check if booking already exists
    existing_booking = (
        db.query(Booking).filter(Booking.share_code == request.shareCode).first()
    )
    if existing_booking:
        raise HTTPException(
            status_code=400, detail="Booking with this share code already exists"
        )

    # Convert deadline string to datetime object
    deadline_dt = datetime.fromisoformat(request.deadline)

    # Create Booking object
    new_booking = Booking(
        share_code=request.shareCode,
        share_url=request.shareURL,
        deadline=deadline_dt,
        category=request.category,
        price=request.price,  # <-- Add this line
        # sold_out and created_at will use default values
    )

    # Create Game objects and associate with booking
    for game in request.games:
        match_day = None
        if getattr(game, "kickoff", None):
            match_day = datetime.fromisoformat(game.kickoff)
        elif getattr(game, "match_day", None):
            match_day = datetime.fromisoformat(game.match_day)
        new_game = Game(
            home_team=game.home,
            away_team=game.away,
            tournament=game.tournament,
            sport=game.sport,
            odds=game.odd,
            prediction=game.prediction,
            match_status=getattr(game, "matchStatus", None)
            or getattr(game, "match_status", None),
            match_day=match_day,
            booking_id=new_booking.id,
        )
        new_booking.games.append(new_game)

    try:
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking  # ✅ This works because of response_model=Booking
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Booking with this share code already exists"
        )


def vip_for_today(db: Session):
    cat_games = []
    today = datetime.now().date()
    vip_bookings = (
        db.query(Booking)
        .filter(Booking.category.ilike("%VIP%"))
        .filter(Booking.created_at >= datetime(today.year, today.month, today.day))
        .all()
    )
    for booking in vip_bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        if "error" not in games:
            cat_games.append(
                {
                    "category": booking.category,
                    "id": booking.id,
                    "price": booking.price,
                    "booking_code": booking.share_code,  # Include booking code
                    "deadline": booking.deadline.isoformat() if booking.deadline else None,  # Include deadline
                "share_url": booking.share_url,  # Include share URL
                "games": [serialize_game(game) for game in games],  # Serialize all games
                }
            )
        # Access games to ensure they are loaded
    return cat_games

def number_of_vip_bookings_today(db: Session):
    today = datetime.now().date()
    vip_count = (
        db.query(Booking)
        .filter(Booking.category.ilike("%VIP%"))
        .filter(Booking.created_at >= datetime(today.year, today.month, today.day))
        .count()
    )
    return vip_count


def free_for_today(db: Session):
    cat_games = []
    today = datetime.now().date()
    free_bookings = (
        db.query(Booking)
        .filter(Booking.category.ilike("%Free%"))
        .filter(Booking.created_at >= datetime(today.year, today.month, today.day))
        .filter(~Booking.sold_out)
        .all()
    )
    for booking in free_bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        # Access games to ensure they are loaded
        print(games)
        cat_games.append(
            {
                "category": booking.category,
                "id": booking.id,
                "booking_code": booking.share_code,
                "deadline": booking.deadline.isoformat() if booking.deadline else None,  # Include deadline
                "share_url": booking.share_url,  # Include share URL
                "games": [serialize_game(game) for game in games],  # Serialize all games
            }
        )
    return cat_games


def all_for_other_days(db: Session, date: datetime):
    today = date.date()
    cat_games = []
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    other_bookings = (
        db.query(Booking)
        .filter(
            Booking.created_at >= start,
            Booking.created_at < end,
            Booking.category.ilike("%free%"),
        )
        .all()
    )
    for booking in other_bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        cat_games.append(
            {
                "category": booking.category,
                "id": booking.id,
                "booking_code": booking.share_code,
                "games": [serialize_game(game) for game in games],
            }
        )

    return cat_games


def view_vip_booking(share_code: str, db: Session):
    booking = (
        db.query(Booking)
        .filter(Booking.share_code == share_code, Booking.category.ilike("%VIP%"))
        .first()
    )
    if not booking:
        return {"error": "VIP Booking not found"}
    return booking


def all_bookings(db: Session):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    result = []
    for booking in bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        result.append({"booking": booking, "games": [serialize_game(game) for game in games]})
    return result


def update_sold_out(booking_id: int, db: Session):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.sold_out = True
    db.commit()
    db.refresh(booking)
    return booking


def update_availability(booking_id: int, db: Session):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.sold_out = False
    db.commit()
    db.refresh(booking)
    return booking


def vip_list_for_today(db: Session):
    vip_list = []
    today = datetime.now().date()
    vip_bookings = (
        db.query(Booking)
        .filter(Booking.category.ilike("%VIP%"))
        .filter(Booking.created_at >= datetime(today.year, today.month, today.day))
        .all()
    )
    for booking in vip_bookings:
        vip_list.append(
            {
                "id": booking.id,
                "name": booking.category,
                "amount": float(booking.price) if booking.price else 0,
                "available": not booking.sold_out,
            }
        )
    return vip_list


def serialize_game(game):
    # Handle both dictionary objects (from API) and model objects (from database)
    if isinstance(game, dict):
        # API data - return all available fields with consistent naming
        return {
            "id": game.get("id"),
            "home_team": game.get("home"),  # Consistent naming
            "away_team": game.get("away"),  # Consistent naming
            "tournament": game.get("tournament"),
            "sport": game.get("sport"),
            "odds": game.get("odd"),  # API uses "odd", standardize to "odds"
            "prediction": game.get("prediction"),
            "match_status": game.get("match_status", "scheduled"),  # Default status
            "match_day": game.get("match_day"),
            
        }
    else:
        # Database model objects - return all available fields
        return {
            "id": getattr(game, 'id', None),
            "home_team": getattr(game, 'home_team', None),
            "away_team": getattr(game, 'away_team', None),
            "tournament": getattr(game, 'tournament', None),
            "sport": getattr(game, 'sport', None),
            "odds": getattr(game, 'odds', None),
            "prediction": getattr(game, 'prediction', None),
            "match_status": getattr(game, 'match_status', 'scheduled'),
            "match_day": game.match_day.isoformat() if hasattr(game, 'match_day') and game.match_day else None,
            "booking_id": getattr(game, 'booking_id', None),
        }


def update_games_statuses(booking_id: int, statuses: dict, db: Session):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    games_status_list = statuses.get("games", [])
    status_map = {item["id"]: item["status"] for item in games_status_list}
    for game in booking.games:
        if game.id in status_map:
            game.match_status = status_map[game.id]
    booking.updated = True
    db.commit()
    return {"message": "Game statuses updated successfully"}


def list_bookings(db: Session):
    today = datetime.now().date()
    updated_bookings = db.query(Booking).filter(Booking.category.ilike("%vip%")).filter(Booking.created_at >= today).all()
    result = []
    for booking in updated_bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        result.append({"booking": booking, "games": [serialize_game(game) for game in games]})
    return result

def list_not_updated_bookings(db: Session):
    today = datetime.now().date()

    not_updated_bookings = db.query(Booking).filter(
        ~Booking.updated,
        Booking.category.ilike("%vip%"),
        ~Booking.sold_out
    ).filter(Booking.created_at >= today).all()
    result = []
    for booking in not_updated_bookings:
        games = db.query(Game).filter(Game.booking_id == booking.id).all()
        games_info = [
            {"id": game.id, "home_team": game.home_team, "away_team": game.away_team}
            for game in games
        ]
        result.append({"booking_id": booking.id, "price": booking.price,"date":booking.created_at,"category":booking.category,"games": games_info})

    return result
