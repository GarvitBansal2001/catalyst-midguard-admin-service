import pyotp
import qrcode
from connections.asyncpg import select, delete, upsert, update
from app.utils.response import success_response, error_response
from app.utils.utils import authentication
from fastapi import APIRouter, Query, Body, BackgroundTasks, Header
from fastapi.responses import FileResponse
import asyncio
import os
from app.models.models import CreateUser, DeleteUser, UpdateUser
from settings import INSTUTITION_NAME, QR_FILE_PATH
from datetime import datetime
from logger import logger


router = APIRouter()


async def delete_qr_file(file_path: str, delay_seconds: int = 60):
    try:
        await asyncio.sleep(delay_seconds)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"QR code file deleted: {file_path}")
    except Exception as e:
        logger.exception(f"Error deleting QR file: {e}")


@router.get("/user")
@authentication(verify_totp=False)
async def get_user(
    authenticationtoken: str = Header(...),
    org: str = Query(...),
    username: str = Query(default=None)
):
    try:
        where = {
            "org = '{}'": org,
        }
        if username:
            where["username = '{}'"] = username
        data = await select("users", ["org", "username", "role_id", "email"], where)
        if not data:
            return success_response([], "User not found")
        for rec in data:
            rec["role_id"] = str(rec["role_id"])
            rec["org"] = str(rec["org"])
        if username:
            data = data[0]
        return success_response(data, "User retrieved successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")


@router.post("/user")
@authentication(verify_totp=False)
async def create_user(
    background_tasks: BackgroundTasks,
    authenticationtoken: str = Header(...),
    body: CreateUser = Body(...)
):
    try:
        payload = body.dict(by_alias=True)
        where = {
            "org = '{}'": payload["org"],
            "username = '{}'": payload["username"]
        }
        data = await select("users", ["org", "username"], where)
        if data:
            return error_response("User already exists", http_status=400)
        payload["secret"] = pyotp.random_base32()
        url = pyotp.totp.TOTP(payload["secret"]).provisioning_uri(name=payload["email"], issuer_name=INSTUTITION_NAME)
        qr = qrcode.make(url)
        qr_file_path = f"{QR_FILE_PATH}/{payload['org']}_{payload['username']}_{datetime.now()}.png"
        qr.save(qr_file_path)
        await upsert("users", payload, ["org", "username"])
        background_tasks.add_task(delete_qr_file, qr_file_path)
        return FileResponse(qr_file_path, media_type="image/png")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")
    

@router.delete("/user")
@authentication()
async def delete_user(
    authenticationtoken: str = Header(...),
    totp: str = Header(...),
    body: DeleteUser = Body(...)
):
    try:
        where = {
            "username = '{}'": body.username,
            "org = '{}'": str(body.org)
        }
        await delete("users", where)
        return success_response(None, "User deleted successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")
    

@router.patch("/user")
@authentication(verify_totp=False)
async def update_user(
    authenticationtoken: str = Header(...),
    body: UpdateUser = Body(...)
):
    try:
        payload = body.dict(by_alias=True)
        where = {
            "org = '{}'": payload["org"],
            "username = '{}'": payload["username"]
        }
        data = await select("users", ["org", "username"], where)
        if not data:
            return error_response("User does not exist", http_status=400)
        await update("users", payload, ["org", "username"])
        return success_response(None, "User updated successfully")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")
    

@router.get("/user/qr")
@authentication(verify_totp=False)
async def get_user_qr(
    background_tasks: BackgroundTasks,
    authenticationtoken: str = Header(...),
    org: str = Query(...),
    username: str = Query(...)
):
    try:
        where = {
            "org = '{}'": org,
            "username = '{}'": username
        }
        data = await select("users", ["email", "secret"], where)
        if not data:
            return error_response("User does not exist", http_status=400)
        data = data[0]
        url = pyotp.totp.TOTP(data["secret"]).provisioning_uri(name=data["email"], issuer_name=INSTUTITION_NAME)
        qr = qrcode.make(url)
        qr_file_path = f"{QR_FILE_PATH}/{org}_{username}_{datetime.now()}.png"
        qr.save(qr_file_path)
        background_tasks.add_task(delete_qr_file, qr_file_path)
        return FileResponse(qr_file_path, media_type="image/png")
    except Exception as e:
        logger.exception(f"Exception :: {e.__class__.__name__} | {str(e)}")
        return error_response(f"Error : {e.__class__.__name__}")