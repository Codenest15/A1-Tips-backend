from fastapi import APIRouter,Depends
from schemas import GetUser,User, AdminUser
from sqlalchemy.orm import Session
from database import get_db
from utils import user as user_utils
from Oauth2 import get_current_user, get_admin_user

router = APIRouter(
    prefix="/auth",
    tags=["Users"]
)

#register a user
@router.post("/sign-up",response_model=GetUser )
def create_user(request:User, db: Session = Depends(get_db)):
   return user_utils.add_user(request, db)

#get user details
@router.get("/user/{id}", response_model=GetUser, dependencies=[Depends(get_current_user)])
def get_user(id: int, db: Session = Depends(get_db)):
    return user_utils.get_user(id, db)

#get total number of users
@router.get("/total-users")
def total_users(db: Session = Depends(get_db)):
    return user_utils.get_total_users(db)


@router.get("/all-users")
def all_users(db: Session = Depends(get_db)):
    return user_utils.get_all_users(db)

@router.post("/add-admin")
def add_admin(request:AdminUser,db: Session = Depends(get_db)):
    return user_utils.add_admin_user(request, db)

@router.get("/all-admins")
def all_admins(db: Session = Depends(get_db)):
    return user_utils.get_admins(db)

@router.get("/user-purchases/{user_email}")
def user_purchases(user_email: str, db: Session = Depends(get_db)):
    return user_utils.get_users_purchases_for_today(user_email, db)

@router.get("/games-purchases/{user_email}")
def games_purchases(user_email: str, db: Session = Depends(get_db)):
    return user_utils.get_user_purchased_games(user_email, db)
