from uuid import UUID
from fastapi import APIRouter, Body, Header
from app.models.models import SetRole, DeleteRole
from logger import logger
from app.utils.response import error_response, success_response
from app.utils.utils import authentication
from app.services.roles import set_roles
from connections.redis import delete as redis_delete, KEY_FORMAT
from connections.asyncpg import delete

router = APIRouter()

@router.post("/role")
@authentication(verify_totp=False)
async def set_role(
    body: SetRole = Body(...),
    authenticationtoken: str = Header(...),
    org: UUID = Header(...)
):
    try:
        body_dict = body.dict(by_alias=True)
        body_dict["org"] = str(org)
        await set_roles(org, body_dict)
        redis_key = KEY_FORMAT.format("role", org) + f"{body.role_id}"
        await redis_delete(redis_key)
        return success_response(None, "Role set successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")


@router.delete("/role")
@authentication()
async def delete_role(
    authenticationtoken: str = Header(...),
    totp: str = Header(...),
    org: str = Header(...),
    payload: DeleteRole = Body(...)
):
    try:
        where = {
            "org = '{}'": str(org),
            "role_id = '{}'": str(payload.role_id)
        }
        await delete("roles", where)
        redis_key = KEY_FORMAT.format("role", org) + f"{str(payload.role_id)}"
        await redis_delete(redis_key)
        return success_response(None, "Role deleted successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")