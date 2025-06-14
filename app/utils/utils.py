import json
import pyotp
from copy import deepcopy
from connections.asyncpg import select
from connections.redis import get as redis_get
from functools import wraps
from app.utils.response import error_response

def dict_reduce(dest: dict, allow_empty_list: bool = True) -> dict:
    if not isinstance(dest, dict):
        return dest
    keys_to_remove = []
    for key, value in dest.items():
        if isinstance(value, dict):
            reduced_dict = dict_reduce(value, allow_empty_list)
            if not reduced_dict:
                keys_to_remove.append(key)
            else:
                dest[key] = reduced_dict
        elif not value and not (isinstance(value, list) and allow_empty_list):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        dest.pop(key)
    
    return dest

def get_diff(dict_1: dict, dict_2: dict) -> dict:
    temp_dict = {}
    for key, value in dict_1.items():
        if key not in dict_2:
            temp_dict[key] = deepcopy(value)
            continue
        if isinstance(value, dict):
            temp_dict[key] = get_diff(value, dict_2[key])
    return temp_dict

def update_diff_map(dest: dict, final_value) -> list:
    route_list = []
    for key, value in dest.items():
        if isinstance(value, dict):
            route_list.extend(update_diff_map(value, final_value))
            continue
        if isinstance(value, (list, tuple)):
            route_list.extend(list(value))
            continue
        if isinstance(final_value, (list, tuple)):
            route_list.extend(final_value)
        else:
            route_list.append(final_value)
        dest[key] = final_value
    return route_list

async def get_generic_path(org: str, route: str, method: str) -> str:
    paths = route.strip("/").split("/")
    service = paths[0]
    generic_path_list = []
    route_map = await select(
        "route_maps",
        ["route_map"],
        {"org = '{}'": org, "service = '{}'": service}
    )
    if not route_map:
        raise Exception("Route map not found")
    route_map = json.loads(route_map[0]["route_map"])
    iterMap = route_map
    for path in paths[1:]:
        if path not in iterMap:
            if "$" not in iterMap:
                raise Exception(f"Route '{route}' not found in service '{service}'")
            path = "$"
        generic_path_list.append(path)
        iterMap = iterMap[path]
    if method not in iterMap.get("__methods", []):
        raise Exception(f"Method '{method}' not allowed for route '{route}' in service '{service}'")
    return "/".join(generic_path_list)


def authentication(verify_totp=True):
    def innerfunc(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = "authenticationtoken"
            if key not in kwargs:
                return error_response("Authentication failed", http_status=401)
            if verify_totp:
                auth_token = kwargs.get(key)
                user_data = await redis_get(auth_token)
                if not user_data:
                    return error_response("Authentication failed", http_status=401)
                totp_verify = pyotp.TOTP(user_data["secret"])
                if not totp_verify.verify(kwargs.get("totp", "")):
                    return error_response("Invalid totp", http_status=400)
            return await func(*args, **kwargs)
        return wrapper
    return innerfunc