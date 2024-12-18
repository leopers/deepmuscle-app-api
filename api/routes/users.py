import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import col, delete, func, select
from api.auth.main import get_current_user
from rag_conversation.suggestions import generate_workout_suggestions
from sql.models import (
    DayExercises,
    Exercises,
    UserDetails,
    Users,
    WorkoutDays,
    Workouts,
)
from api.deps import SessionDep
from sql.schemas import UserDetailsCreate, UserOut
import datetime
from fastapi.responses import JSONResponse, Response
import rag_conversation.chain as chain

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/register_details")
async def register_details(
    form_data: UserDetailsCreate,
    db: SessionDep,
    user: UserOut = Depends(get_current_user),
):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Create and store user details
    new_user_details = UserDetails(
        user_id=db_user.id,
        age=form_data.age,
        height=form_data.height,
        weight=form_data.weight,
        gender=form_data.gender,
        fitness_level=form_data.fitness_level,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    db.add(new_user_details)
    db.commit()
    db.refresh(new_user_details)

    # Generate workout suggestions using the chain
    workout_suggestions = await generate_workout_suggestions(form_data)

    if "error" in workout_suggestions:
        raise HTTPException(status_code=500, detail=workout_suggestions["error"])

    # Store generated workout details in the database
    new_workout = Workouts(
        name=workout_suggestions["workout_name"],
        description=workout_suggestions["description"],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)

    # Assign the workout ID to the user details
    new_user_details.workout_id = new_workout.id
    db.commit()

    # Store workout days and exercises
    for day_data in workout_suggestions["days"]:
        new_workout_day = WorkoutDays(
            user_id=db_user.id,
            day=day_data["day"],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        db.add(new_workout_day)
        db.commit()
        db.refresh(new_workout_day)

        # Add exercises for each workout day
        for exercise_data in day_data["exercises"]:
            # Check if the exercise already exists
            existing_exercise = (
                db.query(Exercises)
                .filter(Exercises.name == exercise_data["name"])
                .first()
            )
            if not existing_exercise:
                new_exercise = Exercises(
                    name=exercise_data["name"],
                    category=exercise_data["category"],
                    description=exercise_data["description"],
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                )
                db.add(new_exercise)
                db.commit()
                db.refresh(new_exercise)
                exercise_id = new_exercise.id
            else:
                exercise_id = existing_exercise.id

            new_day_exercise = DayExercises(
                workout_day_id=new_workout_day.id,
                exercise_id=exercise_id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            db.add(new_day_exercise)
            db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message": "User details registered successfully, and a personalized workout plan has been created."
        },
    )


@user_router.get("/check_workout_day")
async def check_workout_day(db: SessionDep, user: UserOut = Depends(get_current_user)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")

    user_details = (
        db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    )

    workout_day = (
        db.query(WorkoutDays)
        .filter(
            WorkoutDays.user_id == db_user.id
            and WorkoutDays.day == user_details.current_workout_day
        )
        .first()
        .day
    )
    if not workout_day:
        raise HTTPException(status_code=400, detail="User does not have a workout day")

    return Response(status_code=200, content="User has a workout day")


@user_router.post("/update_workout_day")
async def update_workout_day(
    day: str, db: SessionDep, user: UserOut = Depends(get_current_user)
):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User does not exist")

    user_details = (
        db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    )

    next_day = (
        db.query(WorkoutDays)
        .filter(
            WorkoutDays.user_id == db_user.id
            and WorkoutDays.day == user_details.current_workout_day + 1
        )
        .first()
    )

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

    user_details = (
        db.query(UserDetails).filter(UserDetails.user_id == db_user.id).first()
    )

    workout_day = (
        db.query(WorkoutDays)
        .filter(
            WorkoutDays.user_id == db_user.id
            and WorkoutDays.day == user_details.current_workout_day
        )
        .first()
    )

    if not workout_day:
        raise HTTPException(status_code=400, detail="User does not have a workout day")

    exercises = (
        db.query(DayExercises)
        .filter(DayExercises.workout_day_id == workout_day.id)
        .all()
    )

    exercise_ids = [exercise.exercise_id for exercise in exercises]
    exercise_list = db.query(Exercises).filter(Exercises.id.in_(exercise_ids)).all()

    return exercise_list
