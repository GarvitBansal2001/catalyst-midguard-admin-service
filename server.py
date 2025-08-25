import json
from fastapi import FastAPI
from app.routes.public import router as health_router
from app.routes.org import router as org_routes
from app.routes.permissions import router as permission_routes
from app.routes.roles import router as role_routes
from app.routes.login import router as login_routes
from app.routes.users import router as user_routes
from app.models.models import SetOrg
from app.services.org import upsert_org
from connections.asyncpg import upsert
from settings import (
    BASE_ROUTE,
    ORG_ID,
    ORG_NAME,
    ROOT_USERNAME,
    ROOT_PASSWORD,
    ROOT_EMAIL,
    ROOT_USER_SECRET
)

app = FastAPI()

async def upsert_default_org():
    org_data = SetOrg(
        org=ORG_ID,
        org_name=ORG_NAME
    )
    await upsert_org(None, dict(org_data))

def add_route_to_tree(tree: dict, endpoint: str):
    paths = endpoint.path.strip("/").split("/")
    pointer = tree
    path_variables = []
    for path in paths:
        node = "$" if path.startswith(("{", "<")) else path
        if node == "$":
            path_variables.append(path)
        if not pointer.get(node):
            pointer[node] = {}
        pointer = pointer.get(node)
    pointer["__path_variables"] = path_variables
    if "__methods" not in pointer:
        pointer["__methods"] = list(endpoint.methods)
    else :
        pointer["__methods"].extend(endpoint.methods)
        pointer["__methods"] = list(set(pointer["__methods"]))

def create_route_tree(endpoints: list):
    route_tree = {}
    for endpoint in endpoints:
       add_route_to_tree(route_tree, endpoint)
    return route_tree


async def add_route_tree():
    tree = create_route_tree(app.routes)
    service = BASE_ROUTE.strip("/")
    tree = tree[service]
    values = {
        "org": ORG_ID,
        "service": service,
        "route_map": json.dumps(tree)
    }
    await upsert("route_maps", values, ["org", "service"])

async def add_root_user():
    payload = {
        "org": ORG_ID,
        "secret": ROOT_USER_SECRET,
        "username": ROOT_USERNAME,
        "password": ROOT_PASSWORD,
        "email": ROOT_EMAIL
    }
    await upsert("users", payload, ["org", "username"])


def register_routes():
    app.include_router(health_router, tags=["health"], prefix=BASE_ROUTE)
    app.include_router(org_routes, tags=["org"], prefix=BASE_ROUTE)
    app.include_router(permission_routes, tags=["permissions"], prefix=BASE_ROUTE)
    app.include_router(role_routes, tags=["roles"], prefix=BASE_ROUTE)
    app.include_router(login_routes, tags=["login"], prefix=BASE_ROUTE)
    app.include_router(user_routes, tags=["users"], prefix=BASE_ROUTE)

@app.on_event("startup")
async def startup():
    await upsert_default_org()
    register_routes()
    await add_route_tree()
    await add_root_user()