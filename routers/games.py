from fastapi import HTTPException, status, APIRouter, Depends
from sqlalchemy.orm import Session
from utils import games as games_utils
from Oauth2 import get_current_user, get_admin_user
from typing import Annotated
from schemas import BookingResponse
from datetime import datetime
from models import Booking, Game,Purchase  # Make sure to import Game
from database import get_db

router = APIRouter(prefix="/games", tags=["Games"])
# Endpoint to get booking details by share code
@router.get("/load-booking/{share_code}")
def load_booking(share_code: str, db: Session = Depends(get_db)):
    return games_utils.load_booking(share_code, db)

@router.post("/upload-booking")
def upload_booking(request: BookingResponse, db: Session = Depends(get_db)):
    return games_utils.upload_booking(request, db)

@router.get("/vip-for-today")
def vip_for_today(db: Session = Depends(get_db)):
    return games_utils.vip_for_today(db)

@router.get("/free-bookings")
def free_bookings(db: Session = Depends(get_db)):
    return games_utils.free_for_today(db)

@router.get('/other-games')
def other_games(date: datetime, db: Session = Depends(get_db)):
    return games_utils.all_for_other_days(db, date)

@router.get("/all-bookings")
def all_bookings(db: Session = Depends(get_db)):
    return games_utils.all_bookings(db)

@router.get("/vip-list")
def vip_list(db: Session = Depends(get_db)):
    return games_utils.vip_list_for_today(db)

@router.post("/mark-sold-out/{booking_id}")
def mark_sold_out(booking_id: int, db: Session = Depends(get_db)):
    return games_utils.update_sold_out(booking_id, db)

@router.post("/update-availability/{booking_id}")
def update_availability(booking_id: int, db: Session = Depends(get_db),):
    return games_utils.update_availability(booking_id, db)

@router.post("/update-games-status/{booking_id}")
def update_games_status(booking_id: int, statuses: dict, db: Session = Depends(get_db),):
    return games_utils.update_games_statuses(booking_id, statuses, db)

@router.get("/list-vip-slips")
def list_updated_bookings(db: Session = Depends(get_db)):
    return games_utils.list_bookings(db)

@router.get("/list-not-updated-bookings")
def list_not_updated_bookings(db: Session = Depends(get_db)):
    return games_utils.list_not_updated_bookings(db)

@router.get("/number-of-vip-bookings-today")
def number_of_vip_bookings_today(db: Session = Depends(get_db)):
    return games_utils.number_of_vip_bookings_today(db)

@router.delete("/delete-booking/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Delete associated games first (due to foreign key constraints)
    db.query(Game).filter(Game.booking_id == booking_id).delete()
    db.query(Purchase).filter(Purchase.booking_id == booking_id).delete()
    
    # Delete the booking
    db.delete(booking)
    db.commit()
    
    return {"message": "Booking deleted successfully"}
