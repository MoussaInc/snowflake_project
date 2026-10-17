from snowflake.snowpark import functions as F
from snowflake.snowpark.types import DoubleType

from src.snowflake_connection import get_snowflake_session

DB = "SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE"


def extract(df, variable_name: str, metric: str):
    return (
        df.filter(F.col("VARIABLE_NAME") == variable_name)
        .select(
            F.date_trunc("month", F.col("DATE")).alias("MONTH"),
            F.col("VALUE").cast(DoubleType()).alias("VALUE"),
            F.lit(metric).alias("METRIC"),
        )
    )


def main():
    session = get_snowflake_session()
    print("Connected to Snowflake!")

    try:
        econ = session.table(f"{DB}.FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES").filter(
            F.col("GEO_ID") == "country/USA"
        )
        housing = session.table(f"{DB}.FREDDIE_MAC_HOUSING_TIMESERIES")

        combined = (
            extract(econ, "CPI: All items, Monthly, 1982-84 Index Date (Seasonally adjusted)", "CPI")
            .union_all(extract(
                econ,
                "Current Labor Force: Unemployment Rate - 20 yrs. & over, Monthly (Seasonally adjusted)",
                "UNEMPLOYMENT_RATE",
            ))
            .union_all(extract(
                housing, "30-Year Fixed Rate Mortgage Rate, National Average", "MORTGAGE_RATE_30Y"
            ))
        )

        dashboard = (
            combined.group_by("MONTH")
            .agg(
                F.avg(F.when(F.col("METRIC") == "CPI", F.col("VALUE"))).alias("CPI"),
                F.avg(F.when(F.col("METRIC") == "UNEMPLOYMENT_RATE", F.col("VALUE"))).alias("UNEMPLOYMENT_RATE"),
                F.avg(F.when(F.col("METRIC") == "MORTGAGE_RATE_30Y", F.col("VALUE"))).alias("MORTGAGE_RATE_30Y"),
            )
            .sort(F.col("MONTH").desc())
        )

        dashboard.show(20)
        print("Columns:", dashboard.columns)

    finally:
        session.close()


if __name__ == "__main__":
    main()