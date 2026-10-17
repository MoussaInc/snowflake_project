from pathlib import Path

from config.utils.snowflake_connection import get_snowflake_session

# Chemin du fichier SQL
PROJECT_ROOT = Path(__file__).resolve().parent
SQL_FILE = PROJECT_ROOT / "src" / "dynamic_table.sql"

def main():
    session = get_snowflake_session()

    try:
        sql_script = SQL_FILE.read_text(encoding="utf-8")

        # Exécuter chaque instruction SQL séparément
        statements = [statement.strip() for statement in sql_script.split(";") if statement.strip()]

        for statement in statements:
            print(f"Exécution : {statement[:80]}...")
            result = session.sql(statement).collect()
            print("Terminé.")

        print("\nScript SQL exécuté avec succès.")

    finally:
        session.close()


if __name__ == "__main__":
    main()