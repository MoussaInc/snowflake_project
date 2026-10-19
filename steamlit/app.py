import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

TABLE = "ECON_DB.ANALYTICS.ECONOMIC_DYNAMIC_TABLE"

st.set_page_config(page_title="US Economy", layout="wide")
session = get_active_session()


@st.cache_data(ttl=3600)
def load_monthly() -> pd.DataFrame:
    """Une ligne par mois, une colonne par indicateur."""
    df = session.sql(f"""
        SELECT 
            DATE_TRUNC('MONTH', DATE)::DATE AS MONTH, 
            METRIC, 
            AVG(VALUE) AS VALUE
        FROM {TABLE}
        WHERE VALUE IS NOT NULL AND DATE>='1990-01-01'
        GROUP BY 1, 2
    """).to_pandas()
    df["MONTH"] = pd.to_datetime(df["MONTH"])
    # asfreq garde les mois manquants (NaN) : le calcul sur 12 mois reste juste
    return df.pivot(index="MONTH", columns="METRIC", values="VALUE").asfreq("MS")


def show_metric(col, label, series, pct=False, suffix=""):
    s = series.dropna()
    if len(s) < 2:
        col.metric(label, "n/a")
        return
    k = 100 if pct else 1
    last, prev = s.iloc[-1] * k, s.iloc[-2] * k
    col.metric(f"{label} ({s.index[-1]:%b %Y})", f"{last:.2f}{suffix}", f"{last - prev:+.2f}{suffix}")


data = load_monthly()

st.title("US Economy")
st.caption(f"Source : SNOWFLAKE_PUBLIC_DATA_FREE · table {TABLE}, rafraîchie toutes les heures")

start_year = st.slider("Depuis", int(data.index.year.min()), int(data.index.year.max()), 2000)
view = data[data.index.year >= start_year]

cpi = data["CPI"]
cpi_yoy = cpi.pct_change(12, fill_method=None) * 100

c1, c2, c3, c4 = st.columns(4)
show_metric(c1, "CPI", cpi)
show_metric(c2, "Inflation sur 1 an", cpi_yoy / 100, pct=True, suffix=" %")
show_metric(c3, "Chômage", data["UNEMPLOYMENT_RATE"], pct=True, suffix=" %")
show_metric(c4, "Taux hypothécaire 30 ans", data["MORTGAGE_RATE_30Y"], pct=True, suffix=" %")

left, right = st.columns(2)
with left:
    st.subheader("Inflation annuelle (CPI, %)")
    st.line_chart(cpi_yoy[cpi_yoy.index.year >= start_year])
with right:
    st.subheader("Chômage (%)")
    st.line_chart(view["UNEMPLOYMENT_RATE"] * 100)

st.subheader("Taux hypothécaire 30 ans (%, moyenne mensuelle)")
st.line_chart(view["MORTGAGE_RATE_30Y"] * 100)

with st.expander("Données mensuelles"):
    st.dataframe(view.sort_index(ascending=False), use_container_width=True)