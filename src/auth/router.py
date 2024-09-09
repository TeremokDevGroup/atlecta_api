from fastapi import APIRouter, Depends
from .models import User
from .auth import current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/greeting")
async def greeting():
    return {"message": "Hello World"}


@router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


# @router.get("/")
# async def get_all_users_profiles():
#     sports = await UserProfileSQLAlchemyService().get_all()
#     return {"sports": "Users profiles here"}
