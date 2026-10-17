-- After getting the data from the public dataset, 
-- And creating the compute warehouse, the database, schema and role; 
-- we can query the data to get the 30-Year Fixed Rate Mortgage Rate, National Average for the last 12 months.

SELECT VARIABLE_NAME, DATE, VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
WHERE VARIABLE_NAME = '30-Year Fixed Rate Mortgage Rate, National Average'
ORDER BY DATE DESC
LIMIT 12;