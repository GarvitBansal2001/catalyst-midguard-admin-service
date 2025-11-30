import pyotp
import uuid
from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.utils.response import success_response, error_response
from connections.asyncpg import select
from connections.redis import set as redis_set
from logger import logger

router = APIRouter()
security = HTTPBasic()

@router.post("/public/login")
async def login(
    org: str = Header(...),
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        where = {
            "org = '{}'": org,
            "username = '{}'": credentials.username,
            "password = '{}'": credentials.password,
        }
        data = await select("users", ["username"], where)
        if not data:
            return error_response("Invalid username or password", http_status=401)
        data = data[0]
        return success_response(data, "Login successful")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}", http_status=401)


@router.post("/public/totp")
async def totp(
    org: str = Header(...),
    totp: str = Header(...),
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        where = {
            "org = '{}'": org,
            "username = '{}'": credentials.username,
            "password = '{}'": credentials.password,
        }
        data = await select("users", ["username", "email", "org", "role_id", "secret"], where)
        if not data:
            return error_response("Invalid username or password", http_status=401)
        data = data[0]
        if data.get("role_id"):
            data["role_id"] = str(data.get("role_id"))
        secret = data["secret"]
        totp_verify = pyotp.TOTP(secret)
        if not totp_verify.verify(totp):
            return error_response("Invalid totp", http_status=401)
        data["org"] = str(data["org"])
        auth_token = str(uuid.uuid4())
        await redis_set(auth_token, data, ex=24*60*60)
        return success_response({"auth_token": auth_token}, "Verification successful")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}", http_status=401)