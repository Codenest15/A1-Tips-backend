from typing import Union
import models
from database import engine
from routers import auth, user, games, payment, notification, sms
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origin = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://coral-app-l62hg.ondigitalocean.app",
    "https://a1-tips.vercel.app",
    "https://a1-tips.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(games.router)
app.include_router(payment.router)
app.include_router(notification.router)
app.include_router(sms.router)
