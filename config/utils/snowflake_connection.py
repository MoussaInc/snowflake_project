import os
from pathlib import Path

from dotenv import load_dotenv
from snowflake.snowpark import Session

# Chemin vers le .env
CONFIG_DIR = Path(__file__).resolve().parents[1]
load_dotenv(CONFIG_DIR / ".env")


def get_snowflake_session() -> Session:
    """
    Crée et retourne une session Snowpark en utilisant les paramètres de connexion
    définis dans le fichier .env.

    Returns:
        Session: Une instance de session Snowpark.
    """

    connection_params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PAT"],
        "role": os.environ["SNOWFLAKE_ROLE"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
    }

    return Session.builder.configs(connection_params).create()