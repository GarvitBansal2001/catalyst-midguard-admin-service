from uuid import UUID
from pydantic import BaseModel, Field, root_validator
from typing import Optional
from app.models.validators import validate_permission_set

class SetOrg(BaseModel):
    org: UUID = Field(...)
    org_name: str = Field(...)

class DeleteOrg(BaseModel):
    org: UUID = Field(...)


class PermissionGroup(BaseModel):
    read: Optional[int] = None
    write: Optional[int] = None

    @root_validator(pre=True, allow_reuse=True)
    def validate_permissions(cls, values):
        return validate_permission_set(values)
     
class SetPermission(BaseModel):
    route: Optional[str] = None
    method: Optional[str] = None
    permissions: dict[str, dict[str, PermissionGroup]] = Field(default_factory=dict)


class SetRole(BaseModel):
    role_id : UUID = Field(...)
    role_name: str = Field(...)
    permissions: dict[str, dict[str, PermissionGroup]] = Field(default_factory=dict)


class DeleteRole(BaseModel):
    role_id: UUID = Field(...)


class CreateUser(BaseModel):
    username: str = Field(...)
    password: str = Field(...)
    email: str = Field(...)
    org: UUID = Field(...)
    role_id: Optional[UUID] = None

class DeleteUser(BaseModel):
    username: str = Field(...)
    org: UUID = Field(...)