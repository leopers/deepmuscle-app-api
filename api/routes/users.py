import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import col, delete, func, select
from api.auth.main import get_current_user
from sql.models import DayExercises, Exercises, UserDetails, Users, WorkoutDays
from api.deps import SessionDep
from sql.schemas import UserDetailsCreate, UserOut
import datetime
from fastapi.responses import Response

user_router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@user_router.post("/register_details")
async def register_details(form_data: UserDetailsCreate, db: SessionDep, user: UserOut = Depends(get_current_user)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    new_user_details = UserDetails(
        user_id=db_user.id,
        age=form_data.age,
        height=form_data.height,
        weight=form_data.weight,
        gender=form_data.gender,
        fitness_level=form_data.fitness_level,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )
    
    db.add(new_user_details)
    db.commit()
    db.refresh(new_user_details)
    return Response(status_code=201, content="Detalhes do usuário registrados com sucesso")
    

@user_router.get("/check_workout_day")
async def check_workout_day(db: SessionDep, user: UserOut = Depends(get_current_user)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    user_details = db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    
    
    workout_day = db.query(WorkoutDays).filter(WorkoutDays.user_id == db_user.id and WorkoutDays.day == user_details.current_workout_day).first().day
    if not workout_day:
        raise HTTPException(status_code=400, detail="User does not have a workout day")
    
    return Response(status_code=200, content="User has a workout day")

@user_router.post("/update_workout_day")
async def update_workout_day(day: str, db: SessionDep, user: UserOut = Depends(get_current_user)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    user_details = db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    
    next_day = db.query(WorkoutDays).filter(WorkoutDays.user_id == db_user.id and WorkoutDays.day == user_details.current_workout_day + 1).first()
    
    if not next_day:
        user_details.current_workout_day = 1
    else:
        user_details.current_workout_day += 1
    
    db.commit()
    db.refresh(user_details)
    return Response(status_code=201, content="Dia de treino atualizado com sucesso")

@user_router.get("/get_day_exercises")
async def get_day_exercises(db: SessionDep, user: UserOut = Depends(get_current_user)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    user_details = db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    
    workout_day = db.query(WorkoutDays).filter(WorkoutDays.user_id == db_user.id and WorkoutDays.day == user_details.current_workout_day).first()
    
    if not workout_day:
        raise HTTPException(status_code=400, detail="User does not have a workout day")
    
    exercises = db.query(DayExercises).filter(DayExercises.workout_day_id == workout_day.id).all()
    
    exercise_ids = [exercise.exercise_id for exercise in exercises]
    exercise_list = db.query(Exercises).filter(Exercises.id.in_(exercise_ids)).all()
    
    return exercise_list
    


