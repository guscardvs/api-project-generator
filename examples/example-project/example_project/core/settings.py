
from pathlib import Path

from dotenv import load_dotenv

from example_project.core.log import set_logger
from example_project.utils import Env, Environment

BASE_DIR = Path(__file__).resolve().parent.parent
if (env_file:=(BASE_DIR.parent / ".env")).exists():
    load_dotenv(env_file)

environment = Environment()
ENV = environment.get("ENV", dev="dev", parser=Env)
required_env = environment.required_if(ENV == Env.PROD)
logger = set_logger(ENV)
environment.set_logger(logger)

DB_NAME = environment.get("DB_NAME", dev="db-name")
DB_USER = required_env("DB_USER", dev="db-user")
DB_PASSWORD = required_env("DB_PASSWORD", dev="db-pass")
DB_HOST =required_env("DB_HOST", dev="localhost")

