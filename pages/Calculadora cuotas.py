import json
import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from plotly import graph_objs as go
from PIL import Image
from st_pages import show_pages_from_config, add_page_title, show_pages, Page
from _utils import convert_df

show_pages_from_config()

#
# Logo de YoFio
#
if "logo_yofio" not in st.session_state:
    import requests
    url = "https://v.fastcdn.co/u/c2e5d077/58473217-0-Logo.png"
    st.session_state["logo_yofio"] = Image.open(requests.get(url, stream=True).raw)

st.set_page_config(
    layout='wide'
    , initial_sidebar_state='expanded'
    , page_title="KPIS de riesgo"
    , page_icon=st.session_state["logo_yofio"]
    , menu_items={"About": "This is a description of the app."}
)

if "style_css" not in st.session_state:
    import requests
    response = requests.get("https://raw.githubusercontent.com/ErickdeMauleon/data/main/style.css")
    st.session_state["style_css"] = response.text

st.markdown(f'<style>{st.session_state["style_css"]}</style>', unsafe_allow_html=True)

# Specify what pages should be shown in the sidebar, and what their titles and icons
# should be
show_pages(
    [
        Page("KPIS.py", "KPIS de riesgo", "")
        , Page("pages/Cortes.py", "Cortes", "")
        , Page("pages/Rolls.py", "Rolls", "")
        , Page("pages/Cosechas.py", "Cosechas", "")
        , Page("pages/Calculadora cuotas.py", "Calculadora de cuotas", "")
    ]
)

st.title("Calculadora de cuotas")

a, b, c, d = st.columns(4)
# Introduce el monto del préstamo
monto = a.number_input("Monto del préstamo", min_value=0.0, value=1000000.0, step=1000.0)

cuota = b.number_input("Cuota", min_value=0.0, value=100000.0, step=1000.0)

interes = c.number_input("Interés mensual", min_value=0.0, value=0.1, step=0.001)

frecuenca = d.selectbox("Frecuencia", ["Semanal", "Quincenal", "Mensual"])

if frecuenca == "Semanal":
    _i = interes / 4
    _step = 7
elif frecuenca == "Quincenal":
    _i = interes / 2
    _step = 14
else:
    _i = interes / 1
    _step = 30

if monto * _i + 0.16 * monto * _i > cuota:
    st.error("La cuota es muy baja o los intereses muy altos, el cliente no va a acabar de pagar el préstamo.")

# Botón que diga calcular
if st.button("Calcular"):
    df = pd.DataFrame(columns=["deadline_date", "starting_balance", "interest", "vat", "principal", "ending_balance"])

    k = 0

    starting_balance = monto 

    interest = starting_balance * _i

    vat = interest * 0.16

    principal = cuota - interest - vat

    ending_balance = starting_balance - principal

    now = pd.to_datetime("now", utc=True).tz_convert("America/Mexico_City").date()

    df.loc[k] = [now, starting_balance, interest, vat, principal, ending_balance]

    while cuota < ending_balance:
        k += 1

        starting_balance = ending_balance

        interest = starting_balance * _i

        vat = interest * 0.16

        principal = cuota - interest - vat

        ending_balance = starting_balance - principal

        now += timedelta(days=_step)

        df.loc[k] = [now, starting_balance, interest, vat, principal, ending_balance]

        if k > 2000:
            st.error("Se ha llegado al límite de iteraciones, por favor ajusta los parámetros.")
            break

    k += 1

    starting_balance = ending_balance

    interest = starting_balance * _i

    vat = interest * 0.16

    principal = ending_balance

    ending_balance = 0

    now += timedelta(days=_step)

    df.loc[k] = [now, starting_balance, interest, vat, principal, ending_balance]

    st.session_state["df"] = df.copy()


if "df" in st.session_state:
    csv0 = convert_df(st.session_state["df"])

    st.markdown("## Cuotas calculadas")

    e, f, g, h = st.columns(4)

    e.metric("Monto", f"${monto:,.2f}")
    f.metric("Cuota", f"${cuota:,.2f}")
    g.metric("Interés mensual", f"{interes:.0%}")
    h.metric("Frecuencia", frecuenca)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Intereses por pagar", f"${st.session_state['df']['interest'].sum():,.2f}")
    c2.metric("IVA por pagar", f"${st.session_state['df']['vat'].sum():,.2f}")
    c3.metric("Cuotas por pagar", f"{len(st.session_state['df'])}")
    c4.metric("Fin del préstamo", str(st.session_state['df'].iloc[-1, 0]))



    st.markdown("#### → Evolución de los pagos acumulados")
    st.dataframe(
        st.session_state["df"]
        .assign(Mes = lambda _df: _df["deadline_date"].astype(str).str[:7])
        .groupby("Mes", as_index=False)
        .agg({"principal": "sum", "interest": "sum", "vat": "sum"})
        .assign(Total = lambda _df: _df["principal"] + _df["interest"] + _df["vat"])
        .assign(
            principal = lambda _df: _df["principal"].cumsum()
            , interest = lambda _df: _df["interest"].cumsum()
            , vat = lambda _df: _df["vat"].cumsum()
            , Total = lambda _df: _df["Total"].cumsum()
        )
        .filter(["Mes", "principal", "interest", "vat", "Total"])
        .applymap(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
        .rename(columns={
            "Mes": "Mes"
            , "principal": "Capital abonado"
            , "interest": "Interés abonado"
            , "vat": "IVA abonado"
            , "Total": "Total abonado"
        })
        , use_container_width=True
    )


    st.markdown("#### → Tabla de amortización")
    st.download_button(
        label="Descargar CSV"
        , data=csv0
        , file_name='cuotas_calculadas.csv'
        , mime='text/csv'
        , key="cortes"

    )
    st.dataframe(
        st.session_state["df"]
        .applymap(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
        .rename(columns={
            "deadline_date": "Fecha de corte"
            , "starting_balance": "Saldo inicial"
            , "interest": "Interés"
            , "vat": "IVA"
            , "principal": "Capital"
            , "ending_balance": "Saldo final"
        })
        , use_container_width=True
    )







