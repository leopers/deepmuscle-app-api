from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: str
    age: int
    country: str
    phone: str
    password: str
    is_active:Optional[bool] 

    class Config:
        from_attributes = True
        schemas_extra = {
            "example": {
                "full_name": "Felipe",
                "email": "felipe@gmail.com",
                "age": 25,
                "country": "Brazil",
                "phone": "1122334455",
                "password": "12345678",
                "is_active": True
            }
        }

class settings(BaseModel):
    authjwt_secret_key:str='efabc2443dbf72a23f7df4817d91ffeb035c99aca0bb5fd8e2b6cfca8e281892'

class Login(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True
        schemas_extra = {
            "example": {
                "email": "felipe@gmail.com",
                "password": "admin",
            }
        }

