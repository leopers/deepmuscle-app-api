from fastapi import APIRouter
from api.routes.login import login_router
from api.routes.sign_up import signup_router
from fastapi_jwt_auth import AuthJWT
from sql.schemas import settings

api_router = APIRouter()

@AuthJWT.load_config
def get_config():
    return settings()

api_router.include_router(signup_router)
api_router.include_router(login_router)
