USE DATABASE ECON_DB;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE DYNAMIC TABLE ECONOMIC_DYNAMIC_TABLE
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
    DATE,
    METRIC,
    VALUE,
    CASE 
        WHEN METRIC = 'CPI' THEN 'Index'
        WHEN METRIC = 'UNEMPLOYMENT_RATE' THEN 'Percent'
        WHEN METRIC = 'MORTGAGE_RATE_30Y' THEN 'Percent'
    END AS UNIT,
FROM (
    -- CPI and Unemployment from the economic indicators table
    SELECT 
          DATE, 
          VALUE::DOUBLE AS VALUE, 
          'CPI' AS METRIC
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES
    WHERE GEO_ID = 'country/USA'
      AND VARIABLE_NAME = 'CPI: All items, Monthly, 1982-84 Index Date (Seasonally adjusted)'

    UNION ALL
    SELECT 
          DATE, 
          VALUE::DOUBLE AS VALUE, 
          'UNEMPLOYMENT_RATE' AS METRIC
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES
    WHERE GEO_ID = 'country/USA'
      AND VARIABLE_NAME = 'Current Labor Force: Unemployment Rate - 20 yrs. & over, Monthly (Seasonally adjusted)'

    UNION ALL
    -- Mortgage rate from the Freddie Mac table
    SELECT 
          DATE, 
          VALUE::DOUBLE AS VALUE, 
          'MORTGAGE_RATE_30Y' AS METRIC
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
    WHERE VARIABLE_NAME = '30-Year Fixed Rate Mortgage Rate, National Average'
)
;


