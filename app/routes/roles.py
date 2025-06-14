from uuid import UUID
from fastapi import APIRouter, Body, Header
from app.models.models import SetRole
from logger import logger
from app.utils.response import error_response, success_response
from app.services.roles import set_roles

router = APIRouter()

@router.post("/role")
async def set_role(
    body: SetRole = Body(...),
    org: UUID = Header(...)
):
    try:
        body_dict = body.dict(by_alias=True)
        body_dict["org"] = str(org)
        await set_roles(org, body_dict)
        return success_response(None, "Role set successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")