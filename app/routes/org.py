from fastapi import APIRouter, Body, Header
from app.models.models import SetOrg, DeleteOrg
from app.services.org import upsert_org, delete_organization
from logger import logger
from app.utils.response import success_response, error_response
from connections.redis import delete_pattern, KEY_FORMAT
from app.utils.utils import authentication

router = APIRouter()
@router.post("/org")
async def set_org(
    body: SetOrg = Body(...),
    org: str = Header(...)
):
    try:
        await upsert_org(org, dict(body))
        redis_key = KEY_FORMAT.format("org", org) + "*"
        await delete_pattern(redis_key)
        return success_response(None, "Org created successfully")
    except Exception as e:
        logger.error(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")
    
@router.delete("/org")
@authentication()
async def delete_org(
    authenticationtoken: str = Header(...),
    totp: str = Header(...),
    org: str = Header(...),
    body: DeleteOrg = Body(...)
):
    try:
        await delete_organization(str(body.org))
        return success_response(None, "Org deleted successfully")
    except Exception as e:
        logger.error(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")