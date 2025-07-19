from fastapi import APIRouter, Body, Header
from app.models.models import SetPermission
from app.services.permissions import set_permissions
from logger import logger
from uuid import UUID
from app.utils.response import success_response, error_response
from connections.redis import delete_pattern, KEY_FORMAT
from app.utils.utils import get_generic_path

router = APIRouter()

@router.post("/permissions")
async def set_permission(
    body: SetPermission = Body(...),
    org: UUID = Header(...)
):
    is_route_permission = bool(body.route)
    service = ""
    if is_route_permission:
        if not body.method:
            return error_response("Method is required for route permissions", http_status=422)
        path = (await get_generic_path(str(org), body.route, body.method)).strip("/")
        service = body.route.strip("/").split("/")[0]
        body.route = f"{body.method} /{service}/{path}"
    try: 
        body_dict = body.dict(by_alias=True)
        await set_permissions(str(org), service, body_dict, is_route_permission)
        redis_key = KEY_FORMAT.format("permissions", org) + "*"
        await delete_pattern(redis_key)
        return success_response(None, "Permissions set successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")
