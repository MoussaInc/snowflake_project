import os

from src.snowflake_connection import get_snowflake_session


try:
    print("Connexion à Snowflake en cours...")

    session = get_snowflake_session()

    print("Connexion réussie !")

    result = session.sql("""
        SELECT
            CURRENT_USER() AS USER_NAME,
            CURRENT_ROLE() AS ROLE_NAME,
            CURRENT_DATABASE() AS DATABASE_NAME,
            CURRENT_SCHEMA() AS SCHEMA_NAME,
            CURRENT_WAREHOUSE() AS WAREHOUSE_NAME,
            CURRENT_VERSION() AS SNOWFLAKE_VERSION
    """).collect()

    for row in result:
        print(row)

except Exception as exc:
    print(f"Échec de la connexion : {type(exc).__name__}")
    print(str(exc))

finally:
    if session is not None:
        session.close()
        print("Session Snowflake fermée.")