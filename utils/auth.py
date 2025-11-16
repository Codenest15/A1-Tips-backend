from fastapi import HTTPException,Depends
from typing import Annotated
from sqlalchemy.orm import Session
from hashing import Hash
from schemas import Login,Token,TokenData
from datetime import timedelta
import models,token_utils,email_utils

to_email = ["kobbygilbert233@gmail.com"]

def login(db:Session,request:Login):
    try:
        # Validate email format
        if "@" not in request.email_or_username or "." not in request.email_or_username:
            user = db.query(models.User).filter(models.User.username == request.email_or_username).first()
        else:
            user = db.query(models.User).filter(models.User.email == request.email_or_username).first()
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="User not found"
        )
    if not user:
        raise HTTPException(
            status_code=400, detail="User not found"
        )
    if not Hash().verify(user.password, request.password):
        raise HTTPException(
            status_code=400, detail="Incorrect password"
        )
    access_token_expires = timedelta(minutes=token_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token_utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "username": user.username,
        "token_type": "bearer",
        "email": user.email,
        "is_admin": user.is_superuser
    }

def forgot_password(db:Session,request:TokenData):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    reset_token_expires = timedelta(minutes=token_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    reset_token = token_utils.create_access_token(
        data={"sub": user.email}, expires_delta=reset_token_expires
    )
    # Here you would typically send the reset token to the user's email
    reset_link = f"http://example.com/reset-password?token={reset_token}"
    email_utils.send_email("Password Reset", f"Click the link to reset your password: {reset_link}", to_email, "kobbygilbert233@gmail.com", "otiv rmat hcxc breb")



    return {"msg": "Password reset link has been sent to your email"}
# reset password function
def reset_password(db:Session,email:str,new_password:str):
    payload = token_utils.jwt.decode(email, token_utils.SECRET_KEY, algorithms=[token_utils.ALGORITHM])
    if not payload:
        raise HTTPException(
            status_code=400, detail="Invalid token"
        )
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    user.password = Hash().bcrypt(new_password)
    db.commit()
    return {"msg": "Password has been reset successfully"}
