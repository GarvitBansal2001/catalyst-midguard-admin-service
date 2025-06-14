from connections.asyncpg import select, upsert, delete

async def update_parent_org(parent_org, org, add=True):
    if not parent_org:
        return
    where = {
        "org = '{}'": parent_org
    }
    db_data = await select("orgs", ["*"], where)
    if not db_data:
        raise Exception("Organisation not found")
    db_data = db_data[0]
    if add == True:
        if not db_data["child_orgs"]:
            db_data["child_orgs"] = []
        db_data["child_orgs"].append(str(org))
    else: 
        if str(org) in db_data["child_orgs"]:
            db_data["child_orgs"] = list(set(db_data["child_orgs"])-{str(org)})
    db_data["child_orgs"] = list(set(db_data["child_orgs"]))
    await upsert("orgs", db_data, ["org"])


# Create an organization role with default permissions
# and update the parent organization if it exists.
# If the organization does not exist, it will be created.
async def upsert_org(parent_org, response_dict):
    response_dict["parent_org"] = parent_org
    org_data = await select("orgs", ["*"], {"org = '{}'": response_dict["org"]})
    await upsert("orgs", response_dict, ["org"])
    if org_data:
        return
    await update_parent_org(parent_org, response_dict["org"])


# Delete an organization and its associated data.
# This includes removing the organization role and updating the parent organization.
# Org will not be deleted if it has child organizations.
async def get_org(org):
    where = {
        "org = '{}'": org
    }
    db_data = await select("orgs", ["*"], where)
    if not db_data:
        raise Exception("Organisation not found")
    return db_data[0]


async def delete_organization(org):
    db_data = await get_org(org)
    if db_data["child_orgs"]:
        raise Exception("Cannot delete organization with child organizations")
    where = {
        "org = '{}'": org
    }
    await delete("orgs", where)
    if db_data["parent_org"]:
        await update_parent_org(db_data["parent_org"], org, add=False)
    await delete("roles", where)