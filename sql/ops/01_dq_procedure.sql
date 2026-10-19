CREATE OR REPLACE PROCEDURE ECON_DB.ANALYTICS.RUN_DATA_QUALITY_TESTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
AS
$$
T = "ECON_DB.ANALYTICS.ECONOMIC_DYNAMIC_TABLE"

CHECKS = {
    "unicite": f"SELECT DATE, METRIC FROM {T} GROUP BY DATE, METRIC HAVING COUNT(*) > 1",

    "cpi_positif": f"SELECT DATE FROM {T} WHERE METRIC = 'CPI' AND VALUE <= 0",
    
    "taux_hors_plage": f"""SELECT DATE FROM {T}
        WHERE METRIC IN ('UNEMPLOYMENT_RATE', 'MORTGAGE_RATE_30Y')
        AND (VALUE < 0 OR VALUE > 1)""",
}

def run(session):
    failed = []
    for name, sql in CHECKS.items():
        n = len(session.sql(sql).collect())
        if n:
            failed.append(f"{name}: {n} lignes")
    if failed:
        raise Exception("Tests en échec : " + " | ".join(failed))
    return "OK"
$$;