import sys
from io import StringIO
from pathlib import Path

from jupyter_server import files
from snowflake.connector.util_text import split_statements

from src.snowflake_connection import get_snowflake_session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGES = {
    "setup": PROJECT_ROOT / "sql" / "setup",
    "models": PROJECT_ROOT / "sql" / "models",
    "ops": PROJECT_ROOT / "sql" / "ops",
    "analytics": PROJECT_ROOT / "sql" / "analytics",
    "tests": PROJECT_ROOT / "tests",
}


def collect_files(targets: list[str]) -> list[Path]:
    """
    Args:
        targets (list[str]): Liste de cibles (stages ou chemins de fichiers SQL).
    Returns:
        list[Path]: Liste de fichiers SQL à exécuter.
    """
    if not targets:
        targets = list(STAGES)

    files = []
    for target in targets:
        if target in STAGES:
            files.extend(sorted(STAGES[target].glob("*.sql")))
        else:
            files.append(Path(target))
    return files


def run_file(session, sql_file: Path) -> None:
    """
    Args:
        session: Session Snowflake.
        sql_file (Path): Chemin vers le fichier SQL à exécuter.
    returns:
        None
    """
    print(f"\n== {sql_file.name}")
    script = sql_file.read_text(encoding="utf-8")

    for statement, _ in split_statements(StringIO(script), remove_comments=True):
        statement = statement.strip().rstrip(";")
        if not statement:
            continue

        print(f"Exécution : {' '.join(statement.split())[:80]}...")
        rows = session.sql(statement).collect()
        print(f"Terminé ({len(rows)} lignes).")


def main(targets: list[str]) -> None:
    """
    Args:
        targets (list[str]): Liste de cibles (stages ou chemins de fichiers SQL).
    Returns:
        None
    """

    files = collect_files(targets)
    if not files:
        sys.exit("Aucun fichier SQL trouvé.")
        
    session = get_snowflake_session()

    try:
        for sql_file in files:
            run_file(session, sql_file)
        print("\nTous les scripts SQL ont été exécutés avec succès.")
    finally:
        session.close()


if __name__ == "__main__":
    # Usage : python -m src.run_sql [setup|models|analytics|tests|chemin.sql ...]
    main(sys.argv[1:])