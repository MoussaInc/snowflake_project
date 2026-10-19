# US Economy: pipeline Snowflake déployé en CI/CD

CPI, chômage, taux hypothécaire 30 ans : trois indicateurs américains, deux sources, **une seule table à jour toutes les heures**, des analyses SQL prêtes à l'emploi et des tests de qualité qui tournent seuls chaque jour.

Tout est du code versionné : un `git push` déploie, Snowflake exécute et planifie.

```
Git ──push──> GitHub Actions ──> Snowflake
                                  ├─ Dynamic Table      rafraîchie toutes les heures
                                  ├─ Procédure DQ       tests de qualité
                                  └─ Task DQ_TASK       tests chaque jour à 7h
```

## Données

| Indicateur | Source (`SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`) | Fréquence |
|---|---|---|
| CPI, chômage | `FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | mensuelle |
| Taux hypothécaire 30 ans | `FREDDIE_MAC_HOUSING_TIMESERIES` | hebdomadaire |

Résultat : `ECON_DB.ANALYTICS.ECONOMIC_DYNAMIC_TABLE` (`TARGET_LAG = 1 hour`).

Analyses fournies (`sql/analytics/`) : inflation annuelle (CPI YoY), variation annuelle du chômage, moyenne mobile des taux, dernière valeur par indicateur.

## Choix de conception

- **Dynamic Table** plutôt qu'un job de refresh : Snowflake gère la fraîcheur, aucun orchestrateur externe.
- **Une Task, pas un DAG** : un seul traitement planifié (les tests), le reste est déclaratif.
- **Tests bloquants** : la procédure `RUN_DATA_QUALITY_TESTS` lève une erreur si un test échoue. Le déploiement passe au rouge, la Task aussi.
- **Droits minimaux** : l'initialisation (`setup`) est faite une fois par un admin, le déploiement tourne avec `ECON_ROLE`.
- **Aucun secret exposé** : identifiants dans `.env` en local, dans les secrets GitHub en CI.

## Démarrage

Prérequis : Python 3.12, un compte Snowflake, un utilisateur avec le rôle `ECON_ROLE` et un PAT (la network policy doit autoriser votre IP).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # puis renseigner les 7 variables SNOWFLAKE_*
```

Depuis la racine du projet :

```bash
# 1. Initialisation, une seule fois (utilisateur autorisé à utiliser ACCOUNTADMIN)
python -m src.run_sql setup

# 2. Déploiement : Dynamic Table, procédure, Task, tests
python -m src.run_sql models ops tests/run_dq.sql
```

Autres commandes :

```bash
python -m src.prototype_script                       # prototype Snowpark, lecture seule
python -m src.run_sql analytics                      # requêtes d'analyse
python -m src.run_sql tests                          # contrôles de qualité
python -m src.run_sql sql/models/dynamic_table.sql   # un fichier précis
python -m src.run_sql                                # run tous les scripts sql
```

Les étapes s'exécutent dans l'ordre demandé, les fichiers par ordre alphabétique (`01_`, `02_`...). Le script s'arrête à la première erreur.

## Structure

```
sql/
├── setup/       warehouse, base, schéma, rôle, droits
├── models/      Dynamic Table
├── ops/         procédure de tests + Task
└── analytics/   requêtes d'analyse
src/             connexion Snowpark, prototype, exécuteur SQL
tests/           contrôles de qualité (data_quality.sql, run_dq.sql)
.github/         workflow de déploiement
```

## Qualité des données

- **Bloquants** (`RUN_DATA_QUALITY_TESTS`) : une observation par date et indicateur, CPI > 0, taux entre 0 et 1.
- **Monitoring** (`tests/data_quality.sql`) : complétude par indicateur et trous dans les séries.

Suivi de la Task :

```sql
SELECT * FROM TABLE(ECON_DB.INFORMATION_SCHEMA.TASK_HISTORY()) ORDER BY SCHEDULED_TIME DESC;
```

## CI/CD

Un push sur `main` lance `python -m src.run_sql models ops tests/run_dq.sql`.
Secrets GitHub à créer (*Settings > Secrets and variables > Actions*) : les 7 variables du `.env`.
