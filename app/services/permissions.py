import json
from connections.asyncpg import upsert, select
from app.utils.utils import (
    get_diff,
    dict_reduce
)

def update_route_from_parent(org_permission: dict, diff_map: dict, route: str, add=False):
    for key, value in diff_map.items():
        if key not in org_permission:
            raise Exception("Invalid permissions")
        if isinstance(org_permission[key], dict):
            update_route_from_parent(org_permission[key], value, route, add)
            continue
        if isinstance(org_permission[key], (list, tuple)):
            if add:
                org_permission[key] = list(set(org_permission[key]) | set([route]))
            else:
                org_permission[key] = list(set(org_permission[key]) - set([route]))


def get_effected_routes(diff_map: dict):
    temp_list = []
    for _, value in diff_map.items():
        if isinstance(value, dict):
            temp_list.extend(get_effected_routes(value))
            continue
        if isinstance(value, (list, tuple)):
            temp_list.extend(list(value))
    return list(set(temp_list))


async def remove_permission_from_route(org: str, route: str, removed_permissions: dict):
    service = route.strip("/").split("/")[0]
    where = {
        "org = '{}'": org,
        "service = '{}'": service
    }
    result = await select("permissions", ["*"], where)
    if not result:
        return
    result = result[0]
    old_permissions = json.loads(result["permissions"])
    route_old_permissions = old_permissions.get(route, {})
    route_permissions = get_diff(route_old_permissions, removed_permissions)
    old_permissions[route] = route_permissions
    dict_reduce(old_permissions)
    result["permissions"] = json.dumps(old_permissions)
    await upsert("permissions", result, ["org", "service"])


async def handle_route_permissions(org, route: str, permissions: dict, **kwargs):
    removed_permissions = get_diff(permissions.get(route, {}), kwargs.get("new_permissions"))
    added_permissions = get_diff(kwargs.get("new_permissions"), permissions)
    dict_reduce(removed_permissions, False)
    dict_reduce(added_permissions, False)
    where = {
        "org = '{}'": org,
        "service = '{}'": ""
    }
    org_record = await select("permissions", ["*"], where)
    if not org_record:
        raise Exception("No permission set for organization")
    org_record = org_record[0]
    org_permissions = json.loads(org_record.get("permissions"))
    update_route_from_parent(org_permissions, removed_permissions, route)
    update_route_from_parent(org_permissions, added_permissions, route, True)
    org_record["permissions"] = json.dumps(org_permissions)
    await upsert("permissions", org_record, ["org", "service"])
    permissions[route] = kwargs.get("new_permissions")
    dict_reduce(permissions)
    values = {
        "org": org,
        "service": kwargs.get("service"),
        "permissions": json.dumps(permissions)
    }
    await upsert("permissions", values, ["org", "service"])

def add_org_permissions(permissions, add_map: dict):
    for key, value in add_map.items():
        if isinstance(value, dict):
            if key not in permissions:
                permissions[key] = {}
            add_org_permissions(permissions[key], value)
        else:
            permissions[key] = []


async def handle_org_permissions(org, permissions: dict, **kwargs):
    removed_permissions = get_diff(permissions, kwargs.get("new_permissions"))
    dict_reduce(removed_permissions)
    effected_routes = get_effected_routes(removed_permissions)
    for effected_route in effected_routes:
        await remove_permission_from_route(org,effected_route, removed_permissions)
    add_map = get_diff(kwargs.get("new_permissions"), permissions)
    dict_reduce(add_map)
    permissions = get_diff(permissions, removed_permissions)
    add_org_permissions(permissions, add_map)
    dict_reduce(permissions)
    values = {
        "org": org,
        "service": kwargs.get("service"),
        "permissions": json.dumps(permissions)
    }
    await upsert("permissions", values, ["org", "service"])


async def set_permissions(org, service, body: dict, is_route_permission: bool):
    where = {
        "org = '{}'": org,
        "service = '{}'": service
    }
    old_permissions_rec = await select("permissions", ["*"], where)
    if not old_permissions_rec:
        old_permissions_rec = {
            "org": org,
            "service": service,
            "permissions": {}
        }
    else:
        old_permissions_rec = old_permissions_rec[0]
        old_permissions_rec["permissions"] = json.loads(old_permissions_rec["permissions"])
    kwargs = {
        "route": body.get("route"),
        "new_permissions": dict_reduce(body.get("permissions", {})),
        **old_permissions_rec
    }
    if is_route_permission:
        await handle_route_permissions(**kwargs)
    else:
        await handle_org_permissions(**kwargs)