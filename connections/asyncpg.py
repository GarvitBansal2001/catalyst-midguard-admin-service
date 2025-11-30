import asyncpg
from settings import (
    DB_HOST,
    DB_PORT,
    MIDGUARD_DB_NAME,
    MIDGUARD_DB_USER,
    MIDGUARD_DB_PASSWORD
)

db_pool = None

kwargs = {
    "host": DB_HOST,
    "port": DB_PORT,
    "database": MIDGUARD_DB_NAME,
    "user": MIDGUARD_DB_USER,
    "password": MIDGUARD_DB_PASSWORD
}


async def get_db():
    global db_pool
    if db_pool:
        return db_pool
    db_pool = await asyncpg.create_pool(**kwargs)
    return db_pool


def get_where(where_dict: dict):
    return "AND ".join([key.format(value) for key, value in where_dict.items()])


async def select(table: str, columns: list, where_dict: dict):
    db = await get_db()
    query = "SELECT {} FROM {} WHERE {}".format(
        ", ".join(columns),
        table,
        get_where(where_dict)
    )
    result = await db.fetch(query)
    return list(map(dict, result))


async def update(table: str, values: dict, unique_columns: list):
    db = await get_db()
    set_columns = [col for col in values.keys() if col not in unique_columns]
    set_clause = ", ".join(
        [f"{col} = ${i+1}" for i, col in enumerate(set_columns)]
    )
    where_clause = " AND ".join(
        [f"{col} = ${len(set_columns) + i + 1}" for i, col in enumerate(unique_columns)]
    )
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    params = [values[col] for col in set_columns] + [values[col] for col in unique_columns]
    return await db.execute(query, *params)


async def upsert(table: str, values: dict, unique_columns: list):
    db = await get_db()
    upsert_base_string = "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {};"
    keys = list(values.keys())
    excluded_columns = [f"{key} = EXCLUDED.{key}" for key in keys if key not in unique_columns]
    unique_cols = ', '.join(unique_columns)
    do_update = ", ".join(excluded_columns) if excluded_columns else "DO NOTHING"
    placeholder = ", ".join([f"${i+1}" for i in range(len(keys))])
    query = upsert_base_string.format(
        table, 
        ",".join(keys), 
        placeholder, 
        unique_cols, 
        do_update
    )
    return await db.execute(query, *tuple(values.values()))


async def delete(table: str, where_dict: dict):
    db = await get_db()
    query = "DELETE FROM {} WHERE {}".format(
        table,
        get_where(where_dict)
    )
    return await db.execute(query)