# Snowflake Economic Indicators

Pipeline Snowflake qui consolide trois indicateurs économiques américains (CPI, taux de chômage, taux hypothécaire 30 ans) dans une **Dynamic Table**, les analyse en SQL et contrôle leur qualité automatiquement.

**Sources** : `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`
- `FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` (CPI, chômage)
- `FREDDIE_MAC_HOUSING_TIMESERIES` (taux hypothécaire)

**Cible** : `ECON_DB.ANALYTICS.ECONOMIC_DYNAMIC_TABLE` (`TARGET_LAG = 1 hour`)

## Architecture

```
Git (code) ──push──> GitHub Actions ──run_sql.py──> Snowflake
                                                     ├─ Dynamic Table (rafraîchie toutes les heures)
                                                     ├─ Procédure RUN_DATA_QUALITY_TESTS
                                                     └─ Task DQ_TASK (tests chaque jour à 7h, Europe/Paris)
```

Le code vit dans Git. Snowflake exécute et planifie. Ne modifiez pas les objets directement dans Snowsight.

## Structure

```
.
├── sql/
│   ├── setup/        # warehouse, base, schéma, rôle, droits (lancé une seule fois)
│   ├── models/       # dynamic_table.sql
│   ├── ops/          # procédure de tests + Task planifiée
│   └── analytics/    # analytics_queries.sql (CPI YoY, chômage, moyenne mobile...)
├── src/
│   ├── snowflake_connection.py   # session Snowpark depuis .env
│   ├── prototype_script.py       # prototype Snowpark avant la Dynamic Table
│   └── run_sql.py                # exécute les scripts SQL
├── tests/
│   ├── data_quality.sql          # requêtes de contrôle et de monitoring
│   └── run_dq.sql                # appelle la procédure de tests (bloquant en CI)
├── .github/workflows/            # déploiement CI/CD
├── .env.example
└── requirements.txt
```

## Prérequis

- Python 3.12
- Un compte Snowflake et un utilisateur ayant le rôle `ECON_ROLE`
- Un Programmatic Access Token (PAT) ; une network policy doit autoriser votre IP

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseignez le `.env` (jamais commité) :

```
SNOWFLAKE_ACCOUNT=orgname-accountname
SNOWFLAKE_USER=
SNOWFLAKE_PAT=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=
```

## Utilisation

Toutes les commandes se lancent depuis la racine du projet.

**1. Initialisation (une seule fois, à la main, rôle administrateur)**

```bash
python -m src.run_sql setup
```

Crée le warehouse, la base, le schéma, le rôle `ECON_ROLE` et ses droits. Cette étape n'est **pas** exécutée par le CI.

**2. Déploiement (avec `ECON_ROLE`)**

```bash
python -m src.run_sql models ops tests/run_dq.sql
```

**Autres commandes**

```bash
python -m src.prototype_script                  # prototype, sans écriture
python -m src.run_sql analytics                 # requêtes d'analyse
python -m src.run_sql tests                     # contrôles de qualité
python -m src.run_sql sql/models/dynamic_table.sql   # un fichier précis
```

Le script s'arrête à la première erreur. Les fichiers d'une étape s'exécutent par ordre alphabétique (`01_`, `02_`...).

## Qualité des données

- **`RUN_DATA_QUALITY_TESTS`** : procédure Snowflake qui lève une erreur si un test échoue (unicité date/indicateur, CPI > 0, taux entre 0 et 1). Elle est appelée chaque jour par la Task `DQ_TASK` et à chaque déploiement (`tests/run_dq.sql`).
- **`tests/data_quality.sql`** : contrôles complémentaires. Les tests 1 et 2 doivent retourner 0 ligne, le test 3 donne la complétude par indicateur, le test 4 liste les trous dans les séries.

Suivi des exécutions de la Task :

```sql
SELECT * FROM TABLE(ECON_DB.INFORMATION_SCHEMA.TASK_HISTORY()) ORDER BY SCHEDULED_TIME DESC;
```

## CI/CD

À chaque push sur `main`, GitHub Actions exécute `python -m src.run_sql models ops tests/run_dq.sql`.

Secrets à créer dans *Settings > Secrets and variables > Actions* : les 7 variables du `.env`.

## Notes

- Le taux hypothécaire est hebdomadaire, le CPI et le chômage sont mensuels : agréger au mois pour les comparer.
- Les dernières valeurs de CPI et de chômage sont `NULL` tant que le mois n'est pas publié. Octobre 2025 est un trou connu de la source (le test 4 le signale).
- Les taux sont stockés en décimal (`0.0649` = 6,49 %).