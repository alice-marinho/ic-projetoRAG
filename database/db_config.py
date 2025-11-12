import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL_TEST=os.getenv('DATABASE_URL_TEST')
DATABASE_URL=os.getenv('DATABASE_URL')
ASYNC_DATABASE_URL=os.getenv('ASYNC_DATABASE_URL')
MONGO_DATABASE=os.getenv("MONGO_URL")