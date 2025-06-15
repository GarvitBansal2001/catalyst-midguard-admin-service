from os import getenv

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

ENV = getenv("ENV")
SERVER_HOST = getenv("SERVER_HOST")
SERVER_PORT = int(getenv("SERVER_PORT"))
BASE_ROUTE = getenv("BASE_ROUTE")
LOG_LEVEL = getenv("LOG_LEVEL", "INFO")

DB_HOST = getenv("DB_HOST")
DB_PORT = int(getenv("DB_PORT"))
MIDGUARD_DB_NAME = getenv("MIDGUARD_DB_NAME")
MIDGUARD_DB_USER = getenv("MIDGUARD_DB_USER")
MIDGUARD_DB_PASSWORD = getenv("MIDGUARD_DB_PASSWORD")

REDIS_HOST = getenv("REDIS_HOST")
REDIS_PORT = int(getenv("REDIS_PORT"))

ORG_ID = getenv("ORG")
ORG_NAME = getenv("ORG_NAME")
ROOT_USERNAME = getenv("ROOT_USERNAME")
ROOT_PASSWORD = getenv("ROOT_PASSWORD")
ROOT_EMAIL = getenv("ROOT_EMAIL")
ROOT_USER_SECRET = getenv("ROOT_USER_SECRET")
INSTUTITION_NAME = getenv("INSTUTITION_NAME")
QR_FILE_PATH = getenv("QR_FILE_PATH")