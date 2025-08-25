import json
from redis.asyncio import Redis
from settings import (
    REDIS_HOST,
    REDIS_PORT
)

redis_client = None
KEY_FORMAT = "midguard-service~{}-{}-"

def get_redis_client():
    global redis_client
    if redis_client:
        return redis_client
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
    return redis_client


async def get_keys(pattern: str):
    client = await get_redis_client()
    keys = await client.execute_command("KEYS", pattern)
    return [key.decode('utf-8') for key in keys] if keys else []


async def delete(*keys):
    client = await get_redis_client()
    return client.execute_command("DEL", *keys)


async def delete_pattern(pattern: str):
    client = await get_redis_client()
    keys_to_delete = await get_keys(pattern)
    if keys_to_delete:
        return await client.execute_command("DEL", *keys_to_delete)
    return 0


async def set(key, value, ex=None):
    client = await get_redis_client()
    value = json.dumps(value)
    await client.set(key, value, ex=ex)


async def get(key):
    client = await get_redis_client()
    value = await client.get(key)
    if value == None:
        return None
    return json.loads(value)