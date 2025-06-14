import json
from connections.asyncpg import select, upsert
from app.utils.utils import dict_reduce

def validate_permisisons(parent_permissions, permissions):
    for key, value in permissions.items():
        if key not in parent_permissions:
            raise Exception(f"Invalid permission key: {key}")
        if isinstance(value, dict):
            validate_permisisons(parent_permissions[key], value)

async def set_roles(org, body):
    body["permissions"] = dict_reduce(body.get("permissions", {}))
    parent_permissions = await select("permissions", ["*"], {"org = '{}'": org, "service = '{}'": ""})
    if not parent_permissions:
        parent_permissions = [{}]
    parent_permissions = parent_permissions[0]
    parent_permission_set = json.loads(parent_permissions.get("permissions", "{}"))
    validate_permisisons(parent_permission_set, body.get("permissions", {}))
    body["permissions"] = json.dumps(body["permissions"])
    await upsert("roles", body, ["org", "role_id"])