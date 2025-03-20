# Erick Santillan


#
# Importar modulos
#
import json
import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from plotly import graph_objs as go
from PIL import Image
from st_pages import show_pages_from_config, add_page_title, show_pages, Page

#
# Módulos propios, están a la par de este script
#
from _utils import convert_df, format_column, get_date, rango_lim_credito, Roll_t, prod, clean_roll
from _utils import Bucket_Monthly, Bucket_Biweekly, Bucket_Weekly, diff_month
from _metrics import current_pct_task, current_sin_ip_pct_task, imora_task, delta_pct_task, Default_rate_task, roi_task, roi_ratio_task
from _metrics import roi_interes_ratio_task, os_8_task, os_30_task, os_60_task, os_90_task, roll_0_1_task, perdida_task, perdida_hasta_120_task
from _metrics import coincidential_task, lagged_task, total_amount_disbursed_task, OSTotal_sincastigos_task, OSTotal_concastigos_task, credit_limit
from _metrics import  SaldoVencido_task, NumCuentas_task, Activas_task, Mora_task, reestructura_task, os_60_monto_task, os_60_cuentas_task
from _metrics import lim_credito_avg_task, metrica_task, os_30_task_con_WO


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

###########################################
# Data
###########################################

if "BQ" not in st.session_state:
    
    ###########################################
    #  Catalogos
    ###########################################
    st.session_state["cat_advisors"] = pd.read_csv("Data/cat_advisors.csv")
    st.session_state["cat_advisors"].loc[st.session_state["cat_advisors"]["Cartera_YoFio"] == 'C044', ["Analista"]] = "Adriana Alcantar"
    st.session_state["cat_advisors"].loc[st.session_state["cat_advisors"]["ZONA"] == 'Iztacalco', ["ZONA"]] = "Nezahualcoyotl"
    st.session_state["cat_advisors"]["ZONA"] = st.session_state["cat_advisors"]["ZONA"].fillna("-- Sin zona --")
    st.session_state["cat_advisors"]["Analista"] = st.session_state["cat_advisors"]["Analista"].fillna("-- Sin analista --")

    st.session_state["cat_municipios"] = pd.read_csv("Data/cat_municipios.csv", dtype={"CP": str})
    st.session_state["cat_municipios"]["CP"] = st.session_state["cat_municipios"]["CP"].str.zfill(5)
    municipios_list = (st.session_state["cat_municipios"]["Estado"]
                       .replace({'E': 'Edo Mex', 'C': 'CDMX', 'H': 'Hgo', 'P': 'Pue', 'J': 'Jal', 'T': 'Tlaxcala'})
                       + ", " + st.session_state["cat_municipios"]["Municipio"]
                      ).fillna('?').unique().tolist()
    municipios_list.sort()
    st.session_state["municipios_list"] = municipios_list

    st.session_state["cat_industry"] = pd.read_csv("Data/cat_industry.csv")
    ###########################################



    ###########################################
    #  BQ
    ###########################################
    fines_de_mes = ", ".join(["'%s'" % str(d)[:10] for d in pd.date_range("2021-03-31", periods=50, freq="M")])
    st.session_state["BQ"] = (pd.concat([pd.read_csv("Data/"+f) for f in os.listdir("Data/") if "BQ_reduced" in f and "csv" in f])
                              .query("(Fecha_reporte in (%s)) or (Fecha_reporte >= '2023-01-01')" % fines_de_mes)
                              .assign(CP = lambda df: df["CP"].fillna(0).astype(int).astype(str).str.zfill(5))
                              .fillna({"Dias_de_atraso": 0})
                              .drop_duplicates()
                             )


    for c in ["Monto_credito", "Dias_de_atraso", "saldo", "balance"]:
        st.session_state["BQ"][c] = st.session_state["BQ"][c].apply(lambda x: float(x) if x!="" else 0)

    st.session_state["BQ"]["Fecha_apertura"] = st.session_state["BQ"]["Fecha_apertura"].str[:7]
    st.session_state["BQ"]["Semestre_cohort"] = st.session_state["BQ"]["Fecha_apertura"].str[:4] + "-" + st.session_state["BQ"]["Fecha_apertura"].str[5:7].apply(lambda x: "01" if int(x) <= 6 else "02")
    st.session_state["BQ"]["Rango"] = st.session_state["BQ"]["Monto_credito"].apply(rango_lim_credito)
    # st.session_state["BQ"]["Status_credito"] = st.session_state["BQ"]["Status_credito"]#.replace({'I': 'INACTIVE', 'C': 'CURRENT', 'A': 'APPROVED', 'L': 'LATE'})
    st.session_state["BQ"]["balance_sin_ip"] = st.session_state["BQ"]["balance"].values
    st.session_state["BQ"]["balance"] = st.session_state["BQ"][["balance", "saldo"]].fillna(0).sum(axis=1)
    st.session_state["BQ"]["Edad"] = (pd.to_datetime(st.session_state["BQ"]["Fecha_reporte"]) - pd.to_datetime(st.session_state["BQ"]["birth_date"])).dt.days / 365.25
    st.session_state["BQ"] = st.session_state["BQ"].drop(columns=["birth_date"])
    st.session_state["BQ"]["Edad"] = st.session_state["BQ"]["Edad"].fillna(st.session_state["BQ"]["Edad"].mean())
    st.session_state["BQ"]["allow_disbursements"] = st.session_state["BQ"]["allow_disbursements"].fillna(0) # 0: Not allowed, 1: Allowed

temp = st.session_state["BQ"].copy()
###########################################












##################################################################
##
## STREAMLIT APP
##
##################################################################


if "style_css" not in st.session_state:
    import requests
    response = requests.get("https://raw.githubusercontent.com/ErickdeMauleon/data/main/style.css")
    st.session_state["style_css"] = response.text

st.markdown(f'<style>{st.session_state["style_css"]}</style>', unsafe_allow_html=True)
#st.sidebar.image("https://v.fastcdn.co/u/c2e5d077/58473217-0-Logo.png")
#st.table(BQ.sample(5).head())
st.sidebar.header('Dashboard KPIS de riesgo')

st.sidebar.subheader('Selecciona parametros:')
_cortes = st.sidebar.selectbox('Selecciona los cierres:'
                                 , ('Por mes', 'Por quincenas', 'Por semanas')) 
cortes = {"Por quincenas": 'Catorcenal'
          , "Por mes": 'Mensual'
          , "Por semanas":  'Semanal'
         }[_cortes]


##### Filter term_type on temp
term_type = st.sidebar.multiselect('Selecciona tipo de corte de cartera'
                                 , ('Todos', 'Catorcenal', 'Mensual', 'Semanal')
                                 , default='Todos'
                                 ) 
if "Todos" not in term_type:
    term_type_dict = {'Catorcenal': "B", 'Mensual': "M", 'Semanal': "W"}
    term_type = [term_type_dict[t] for t in term_type]
    temp = temp[temp["term_type"].isin(term_type)]


zona_list = list(st.session_state["cat_advisors"].ZONA.drop_duplicates().values)
zona_list.sort()
zona = st.sidebar.multiselect('Selecciona la zona del analista'
                            , ['Todas'] + zona_list
                            , default='Todas'
                            )
if "Todas" not in zona:
    temp = temp[temp["Cartera_YoFio"].isin(st.session_state["cat_advisors"].loc[st.session_state["cat_advisors"]["ZONA"].isin(zona), "Cartera_YoFio"].values)]



Analista_list = list(st.session_state["cat_advisors"].Analista.dropna().drop_duplicates().values)
Analista_list.sort()
analista = st.sidebar.multiselect('Selecciona el analista'
                                  , ['Todos'] + Analista_list
                                  , default='Todos'
                                 )
if "Todos" not in analista:
    temp = temp[temp["Cartera_YoFio"].isin(st.session_state["cat_advisors"].loc[st.session_state["cat_advisors"]["Analista"].isin(analista), "Cartera_YoFio"].values)]



ampl = st.sidebar.multiselect('Selecciona el número de ampliación'
                                 , ["Todas", 0, 1, 2, 3, "4+"]
                                 , default='Todas'
                                 )

if "Todas" in ampl:
    pass
elif  "4+" not in ampl:
    temp = temp.query("n_ampliaciones.isin(@ampl)")
else:
    temp = temp.query("n_ampliaciones.isin(@ampl) or n_ampliaciones >= 4")

##### Filter genero on temp
genero = st.sidebar.multiselect('Selecciona el género del tiendero'
                                 , ["Todos", "Hombre", "Mujer", "Vacio"]
                                 , default='Todos'
                                 )
genero_dict = {"Todos": "Todos", "Hombre": "H", "Mujer": "M", "Vacio": "?"}
genero = [genero_dict[g] for g in genero]
if "Todos" not in genero:
    temp = temp[temp["genero_estimado"].isin(genero)]

##### Filter cohort on temp
cohort = st.sidebar.multiselect('Selecciona el cohort'
                                , ['Todos'] + list(temp.Fecha_apertura.unique())
                                , default='Todos'
                               )
cohort = [str(c) for c in cohort]
if "Todos" not in cohort:
    temp = temp[temp["Fecha_apertura"].isin(cohort)]
    
##### Filter edad on temp
Edades_list = ["De 20 a 29", "De 30 a 34", "De 35 a 39", "De 40 a 44", "De 45 a 49", "De 50 a 54", "De 55 a 59", "Mayor de 60"]
Edades_list.sort()
edad = st.sidebar.multiselect('Selecciona la edad del tiendero'
                              , ['Todos'] + Edades_list
                              , default='Todos'
                             )
if "Todos" not in edad:
    temp = temp[temp["Edad"]
            .apply(lambda x: "De %i a %i" % (int(x//5)*5, int(x//5)*5+4))
            .replace({"De 60 a 64": "Mayor de 60"
                      , "De 65 a 69": "Mayor de 60"
                      , "De 70 a 74": "Mayor de 60"
                      , "De 75 a 79": "Mayor de 60"
                      , "De 80 a 84": "Mayor de 60"
                      , "De 20 a 24": "De 20 a 29"
                      , "De 25 a 29": "De 20 a 29"
                     })
            .isin(edad)
            ]

estados_list = ["CDMX", "Edo Mex", "Hidalgo", "Jalisco", "Puebla", "Tlaxcala"]
estados_list.sort()
estado = st.sidebar.multiselect('Selecciona el estado de la tienda'
                             , ['Todos'] + estados_list
                             , default='Todos'
                            )
if "Todos" not in estado:
    estado = [e[0] for e in estado]
    temp = (temp
            .merge(st.session_state["cat_municipios"]
                   [st.session_state["cat_municipios"]["Estado"].isin(estado)]
                   .filter(["CP"]))
            )

municipio = st.sidebar.multiselect('Selecciona el municipio de la tienda'
                                 , ['Todos'] + st.session_state["municipios_list"]
                                 , default='Todos'
                                 )
if "Todos" not in municipio:
    temp = temp[temp["CP"].isin(st.session_state["cat_municipios"]
                                [st.session_state["cat_municipios"]["Municipio"].isin(municipio)]
                                ["CP"]
                                .values
                                )
               ]



rangos_list = list(st.session_state["BQ"].Rango.unique())
rangos_list.sort()
rangos = st.sidebar.multiselect('Selecciona el rango del límite de credito'
                                 , ['Todos'] + rangos_list
                                 , default='Todos'
                                 )

industry_list = list(st.session_state["cat_industry"].industry.unique())
industry_list.sort()
industry = st.sidebar.multiselect('Selecciona el giro del negocio'
                                 , ['Todos'] + industry_list
                                 , default='Todos'
                                 )
if "Todos" not in industry:
    temp = temp[temp["industry_cve"].isin(st.session_state["cat_industry"]
                                          [st.session_state["cat_industry"]["industry"].isin(industry)]
                                          ["industry_cve"]
                                          .values
                                          )
                ]

dsoto = st.sidebar.multiselect('¿Evaluación virtual? (dsoto)'
                               , ['Si', 'No']
                               , default=['Si', 'No']
                               )




filtro_dict = {'Todos': {"f2": ", ".join(["'%s'" % str(d)[:10] for d in pd.date_range("2021-03-31"
                                                                                        , periods=50
                                                                                        , freq="M")])
                         , "Bucket": Bucket_Monthly
                         , "buckets": ['0. Bucket_Current'
                                       , '1. Bucket_1_29'
                                       , '2. Bucket_30_59'
                                       , '3. Bucket_60_89'
                                       , '4. Bucket_90_119'
                                       , '5. Bucket_120_more'
                                       , '6. delta']
                         , "top_rolls": 4
                         , "term_type": "Monthly"
                        }
               , 'Catorcenal': {"f2": ", ".join(["'%s'" % get_date(i) for i in range(160) if i % 2 == 0])
                                , "Bucket": Bucket_Biweekly
                                , "buckets": ['0. Bucket_Current'
                                              , '01. Bucket_1_15'
                                              , '02. Bucket_16_30'
                                              , '03. Bucket_31_45'
                                              , '04. Bucket_46_60'
                                              , '05. Bucket_61_75'
                                              , '06. Bucket_76_90'
                                              , '07. Bucket_91_105'
                                              , '08. Bucket_106_119'
                                              , '09. Bucket_120_more'
                                              , '10. delta']
                                , "top_rolls": 8
                                , "term_type": "Biweekly"
                               }
               , 'Semanal': {"f2": ", ".join(["'%s'" % get_date(i) for i in range(160)])
                             , "Bucket": Bucket_Weekly
                             , "buckets": ['0. Bucket_Current'
                                           , '01. Bucket_1_7'
                                           , '02. Bucket_8_14'
                                           , '03. Bucket_15_21'
                                           , '04. Bucket_22_28'
                                           , '05. Bucket_29_35'
                                           , '06. Bucket_36_42'
                                           , '07. Bucket_43_49'
                                           , '08. Bucket_50_56'
                                           , '09. Bucket_57_63'
                                           , '10. Bucket_64_70'
                                           , '11. Bucket_71_77'
                                           , '12. Bucket_78_84'
                                           , '13. Bucket_85_91'
                                           , '14. Bucket_92_98'
                                           , '15. Bucket_99_105'
                                           , '16. Bucket_106_112'
                                           , '17. Bucket_113_119'
                                           , '18. Bucket_120_more'
                                           , '19. delta']
                             , "top_rolls": 17
                             , "term_type": "Weekly"
                            }
               , 'Mensual': {"f2": ", ".join(["'%s'" % str(d)[:10] for d in pd.date_range("2021-03-31"
                                                                                            , periods=50
                                                                                            , freq="M")])
                             , "Bucket": Bucket_Monthly
                             , "buckets": ['0. Bucket_Current'
                                           , '1. Bucket_1_29'
                                           , '2. Bucket_30_59'
                                           , '3. Bucket_60_89'
                                           , '4. Bucket_90_119'
                                           , '5. Bucket_120_more'
                                           , '6. delta']
                             , "top_rolls": 4
                             , "term_type": "Monthly"
                            }
              }[cortes]


f2 = filtro_dict["f2"]

if 'Todos' in rangos:
    f7 = ""
else:
    f7 = " and Rango.isin(%s)" % str(rangos)



if len(dsoto) == 1:
    f12 = " and Creado_dsoto == %i" % int(dsoto[0] == 'Si')
else:
    f12 = ""



N = filtro_dict["top_rolls"]   
 
filtro_BQ = "Fecha_reporte == Fecha_reporte %s %s " % (f7, f12)
    

YoFio = (st.session_state["BQ"]
         .query("Fecha_reporte in (%s)" % f2)
         .assign(Bucket = lambda df: df.Dias_de_atraso.apply(filtro_dict["Bucket"]))
         .sort_values(by=["ID_Credito", "Fecha_reporte"]
                         , ignore_index=True)
        )
YoFio["Mes"] = YoFio.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

temp = temp.query(filtro_BQ)
df_cosechas = temp.copy()
temp = (temp
        .query("Fecha_reporte in (%s)" % f2)
        .assign(Bucket = lambda df: df.Dias_de_atraso.apply(filtro_dict["Bucket"]))
        .sort_values(by=["ID_Credito", "Fecha_reporte"]
                         , ignore_index=True)
        )

if len(temp) == 0:
    st.write("No hay clientes con las condiciones que pides.")
else:

    temp["t"] = (temp
                 .assign(t=range(len(temp)))
                 .groupby(["ID_Credito"])
                 .t.rank()
                )
    temp = (temp
            .merge(temp
                   .assign(t=lambda df: df.t+1)
                   [["ID_Credito", "Dias_de_atraso", "Fecha_reporte", "t"]]
                   , on=["ID_Credito", "t"]
                   , suffixes=("", "_ant")
                   , how="left")
            .fillna({"Dias_de_atraso_ant": 0})
            .drop(columns=["Fecha_reporte_ant"])
         )



    YoFio["t"] = (YoFio
                 .assign(t=range(len(YoFio)))
                 .groupby(["ID_Credito"])
                 .t.rank()
                )
    YoFio = (YoFio
            .merge(YoFio
                   .assign(t=lambda df: df.t+1)
                   [["ID_Credito", "Dias_de_atraso", "Fecha_reporte", "t"]]
                   , on=["ID_Credito", "t"]
                   , suffixes=("", "_ant")
                   , how="left")
            .fillna({"Dias_de_atraso_ant": 0})
            .drop(columns=["Fecha_reporte_ant"])
         )
    
    #
    # Cosechas
    #
    st.markdown('### Cosechas')
        
    def Bucket_Par8(x):
        if x <= 0 :
            return '0. Bucket_Current'
        elif x >= 1 and x < 8 :
            return '1. Bucket_1_7'
        elif x >= 8 and x < 60 :
            return '2. Bucket_8_59'
        elif x >= 60 and x < 90 :
            return '3. Bucket_60_89'
        elif x >= 90 and x < 120 :
            return '4. Bucket_90_119'
        elif x >= 120 :
            return '5. Bucket_120_more'
    
    fechas = ", ".join(["'%s'" % str(d)[:10] for d in pd.date_range("2020-01-31", periods=200, freq="M")])
    _query = " and ".join([f for f in filtro_BQ.split(" and ") if "Fecha_reporte" not in f])
    df_cosechas = (df_cosechas
                   .assign(Dias_de_atraso = lambda df: df.Dias_de_atraso.apply(lambda x: max(x, 0)))
                   .query("Fecha_reporte in (%s)" % (fechas))
                   .assign(Bucket_2 = lambda df: df.Dias_de_atraso.apply(Bucket_Monthly)
                           , Bucket_par8 = lambda df: df.Dias_de_atraso.apply(Bucket_Par8)
                           )
                   .rename(columns={"balance": "Saldo"})
                   .sort_values(by=["ID_Credito", "Fecha_reporte"], ignore_index=True)
                  )
     
    df_cosechas["t"] = df_cosechas.assign(t=range(len(df_cosechas))).groupby(["ID_Credito"]).t.rank()
    df_cosechas["Cosecha"] = df_cosechas.apply(lambda row: "M"+str(diff_month(row["Fecha_reporte"], str(row["Fecha_apertura"])[:7]+"-01" )).zfill(3), axis=1)
    df_cosechas["Mes_apertura"] = df_cosechas["Fecha_apertura"].apply(str).str[:7]
    fecha_reporte_max = df_cosechas.Fecha_reporte.sort_values().iloc[-1]
        
      
    df_cosechas = (df_cosechas
                  .merge(df_cosechas
                         .assign(t=lambda df: df.t+1)
                         [["ID_Credito", "Dias_de_atraso", "Fecha_reporte", "t"]]
                         , on=["ID_Credito", "t"]
                         , suffixes=("", "_ant")
                         , how="left")
                   .drop(columns=["t", "Fecha_reporte_ant"])
                  
                 )
    metricas_cosechas = {"Saldo Total (incluyendo castigos)": "Saldo"
                           , "Saldo Total (sin castigos)": "Saldo_no_castigado"
                           , "Saldo castigado (+120 dpd)": "Saldo_castigado"
                           , "Total compras colocadas (Acumulado)": "Monto_compra_acumulado"
                           , "Total colocado (Acumulado)": "Total_colocado_acumulado"
                           , "Número de cuentas (incluyendo castigos)": "Creditos"
                           , "Número de cuentas (sin castigos)": "Creditos_no_castigados"
                           , "Cuentas activas": "cuentas_activas"
                           , "% IMORA": "IMORA"
                           , "Par 8": "Par8"
                           , "Par 30": "Par30"
                           , "Par 60": "Par60"
                           , "Par 90": "Par90"
                           , "Par 120": "Par120"
                        }
    
    _a, _, _ = st.columns(3)
    metrica_cosecha = _a.selectbox("Selecciona métrica:"
                                   , metricas_cosechas.keys()
                                   )
    metrica_seleccionada = metricas_cosechas[metrica_cosecha]
    # st.dataframe(df_cosechas)
    if metrica_seleccionada == "Saldo" or metrica_seleccionada == "IMORA":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"].copy()
    elif metrica_seleccionada == "Saldo_no_castigado":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*(df_cosechas["Dias_de_atraso"] < 120).astype(int)
    elif metrica_seleccionada == "Saldo_castigado":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*(df_cosechas["Dias_de_atraso"] >= 120).astype(int)
    elif metrica_seleccionada == "Monto_compra_acumulado":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Monto_compra_acumulado"].copy()
    elif metrica_seleccionada == "Total_colocado_acumulado":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Monto_compra_acumulado"] + df_cosechas["amount_disbursed"]
    elif metrica_seleccionada == "cuentas_activas":
        df_cosechas["Metrica seleccionada"] = ((df_cosechas["Dias_de_atraso"] < 120) & (df_cosechas["Status_credito"] != "I")).astype(int)
    elif metrica_seleccionada == "Creditos":
        df_cosechas["Metrica seleccionada"] = 1
    elif metrica_seleccionada == "Creditos_no_castigados":
        df_cosechas["Metrica seleccionada"] = (df_cosechas["Dias_de_atraso"] < 120).astype(int)
    elif metrica_seleccionada == "Par8":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*((df_cosechas["Dias_de_atraso"] >= 8) & (df_cosechas["Dias_de_atraso"] < 120)).astype(int)
    elif metrica_seleccionada == "Par30":
        st.write("Par30")
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*((df_cosechas["Dias_de_atraso"] >= 30) & (df_cosechas["Dias_de_atraso"] < 120)).astype(int)
    elif metrica_seleccionada == "Par60":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*((df_cosechas["Dias_de_atraso"] >= 60) & (df_cosechas["Dias_de_atraso"] < 120)).astype(int)
    elif metrica_seleccionada == "Par90":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*((df_cosechas["Dias_de_atraso"] >= 90) & (df_cosechas["Dias_de_atraso"] < 120)).astype(int)
    elif metrica_seleccionada == "Par120":
        df_cosechas["Metrica seleccionada"] = df_cosechas["Saldo"]*(df_cosechas["Dias_de_atraso"] >= 120).astype(int)

    if metrica_seleccionada == 'IMORA':
        Cosechas = (imora_task(temp, "Fecha_apertura")
                    .assign(Mes_apertura = lambda df: df.Fecha_apertura.apply(str).str[:7])
                    .assign(F = lambda df: df.Mes_apertura.apply(lambda x: int(x.replace("-","")) >= 202108))
                    .query("F")
                    .drop(columns="F")
                    .assign(Cosecha = lambda df: "M"+df.apply(lambda row: diff_month(row.Fecha_reporte, row.Mes_apertura+"-01"), axis=1).astype(str).str.zfill(3))
                    .filter(["Mes_apertura", "Cosecha", "Metric"])
                   )
        formato = lambda x: "{:,.2f}%".format(x*100) if x == x else ""
        

    else:
        Cosechas = (df_cosechas
                    .groupby(["Mes_apertura", "Cosecha"], as_index=False)
                    .agg(Metric = pd.NamedAgg("Metrica seleccionada", "sum"))

                )
        if metrica_seleccionada != "cuentas_activas":
            Cosechas = Cosechas[Cosechas["Mes_apertura"].apply(lambda x: int(x.replace("-","")) >= 202108)]

        formato = (lambda x: "${:,.0f}".format(x) if x == x else x) if "cuentas" not in metrica_cosecha.lower() else (lambda x: "{:,.0f}".format(x) if x == x else x)


        
        
    # st.dataframe(Cosechas)

    
    Cosechas_toshow = (Cosechas
                       .pivot(index="Mes_apertura"
                              , columns="Cosecha"
                              , values="Metric"
                             )
                       )

    Cosechas_toshow = (Cosechas_toshow
                       .applymap(formato)
                       .fillna("")
                       )
    

    
    Cosechas = Cosechas.filter(['Mes_apertura', 'Cosecha', 'Saldo', 'Creditos'])
    ##
    ## Cosechas buckets
    ##


    df_agg = (df_cosechas
              .assign(F = lambda df: df.Mes_apertura.apply(lambda x: int(x.replace("-","")) >= 202108))
              .query("F")
              .drop(columns="F")
              .rename(columns={"Cosecha": "index"})
              .pivot_table(index=["Mes_apertura", "Bucket_2"]
                           , columns=["index"]
                           , values="Metrica seleccionada"
                           , aggfunc="sum")
              .reset_index()
              .fillna(0)
              .rename(columns={"Mes_apertura": "Cosecha"
                               , "Bucket_2": "Bucket"})
              
             )
    
    df_agg = (df_agg
             [["Cosecha"]]
             .drop_duplicates()
             .assign(f=1)
             .merge(df_agg
                    [["Bucket"]]
                    .drop_duplicates()
                    .assign(f=1)
                    , how="left"
                   )
              .assign(f=1)
             .drop(columns="f")
             .merge(df_agg
                    , how="left")
             .fillna(0)
                      .sort_values(by=["Cosecha", "Bucket"], ignore_index=True)
            )
     
    delta = (df_cosechas
             .assign(F = lambda df: df.Mes_apertura.apply(lambda x: int(x.replace("-","")) >= 202108))
             .query("Dias_de_atraso >= 120 and Dias_de_atraso_ant < 120 and F")
             .drop(columns="F")
             .assign(Bucket = "6. WO")
             .groupby(["Cosecha", "Mes_apertura", "Bucket"])
             .agg(Value = pd.NamedAgg("Saldo", "sum"))
             .reset_index()
             .rename(columns={"Mes_apertura": "Cosecha"
                              , "Cosecha": "Mes"
                             })
            )   
    
    df_agg2 = (df_agg
               .melt(id_vars=["Cosecha", "Bucket"]
                     , var_name="Mes"
                     , value_name="Value"
                    )
              )
    df_agg2 = pd.concat([df_agg2
                         , (df_agg2
                            [["Mes"]]
                            .drop_duplicates()
                            .assign(f=1)
                            .merge(df_agg2
                                   [["Cosecha"]]
                                   .drop_duplicates()
                                   .assign(f=1))
                            .drop(columns="f")
                            .merge(delta
                                   , how="left")
                            .fillna({"Bucket": "6. WO"
                                     , "Value": 0})
                           )
                        ])
    df_agg = (df_agg2
              .pivot(index=["Cosecha", "Bucket"]
                     , columns="Mes"
                     , values="Value"
                    )
              .reset_index()
             )
    
    df_agg = (df_agg
              [["Cosecha"]]
              .drop_duplicates()
              .assign(f=1)
              .merge(pd.DataFrame({"Bucket": ["0. Bucket_Current"
                                              , "1. Bucket_1_29"
                                              , "2. Bucket_30_59"
                                              , "3. Bucket_60_89"
                                              , "4. Bucket_90_119"
                                              , "5. Bucket_120_more"
                                              , "6. WO"
                                              ]})
                     .assign(f=1)
                     )
              .drop(columns="f")
              .merge(df_agg, how="left")
              .fillna(0)
             )



    tb1, tb2 = st.tabs(["Matriz cosechas", "Cosechas por buckets"])

    with tb1:
        _, _, _, _d = st.columns(4)
        csv2 = convert_df(Cosechas_toshow
                          .applymap(lambda x: x.replace("%", "").replace("$", "").replace(",", "") if isinstance(x, str) else x)
                          .reset_index()
                         )
        _d.download_button(
            label="Descargar CSV",
            data=csv2,
            file_name='cosechas.csv',
            mime='text/csv',
        )
        st.dataframe(Cosechas_toshow
                    , height=666
                    , use_container_width=True)


    with tb2:
        Cosecha_dropdown = list(df_agg.Cosecha.unique())
        Cosecha_dropdown.sort()
        st.markdown("##### Cosechas desagregadas por bucket")
        k1, _, k5 = st.columns(3)
        Cosecha_selected = k1.selectbox("Selecciona una cosecha:"
                                        , Cosecha_dropdown
                                        )

        vista_calendario = st.checkbox("¿Vista meses calendario?", value=False)

    
        if "erick" in os.getcwd():
            csv3 = convert_df(df_agg
                              .assign(Bucket = lambda df: df["Bucket"].apply(lambda x: "6. WO (delta)" if "WO" in x else x))
                              .melt(id_vars=["Cosecha", "Bucket"]
                                    , var_name="MOB"
                                    , value_name="Value"
                                   )
                             )
        else:
            csv3 = convert_df(df_agg[df_agg.Cosecha == Cosecha_selected].assign(Bucket = lambda df: df["Bucket"].apply(lambda x: "6. WO (delta)" if "WO" in x else x)))

        
        k5.download_button(
            label="Descargar CSV",
            data=csv3,
            file_name='Cosecha_Bucket_%s.csv' % Cosecha_selected,
            mime='text/csv'
        )
        def _formato(x, metrica_seleccionada):
            if metrica_seleccionada in ("Saldo", "Saldo_no_castigado", "Saldo_castigado"):
                return "${:,.0f}".format(x)
            elif "cuentas" in metrica_seleccionada.lower() or "creditos" in metrica_seleccionada.lower():
                return "{:,.0f}".format(x)

        df_agg = (df_agg
                [df_agg.Cosecha == Cosecha_selected]
                .applymap(lambda x: _formato(x, metrica_seleccionada) if not isinstance(x, str) else x)
                .assign(Bucket = lambda df: df["Bucket"].apply(lambda x: "6. WO (delta)" if "WO" in x else x))
                .reset_index(drop=True)
                .set_index(["Cosecha", "Bucket"])
                )
        
        _fechas = pd.date_range(Cosecha_selected+"-01", periods=120, freq="M")
        _fechas = [str(f)[:7] for f in _fechas if str(f)[:10] <= fecha_reporte_max]
        _fechas = {"M"+str(i).zfill(3): fecha for i, fecha in enumerate(_fechas)}

        if vista_calendario:
            df_agg = df_agg.rename(columns=_fechas).filter(list(_fechas.values()))
        else:
            df_agg = df_agg.filter(list(_fechas.keys()))

        st.dataframe(df_agg, use_container_width=True)
    
    
 
    

    st.subheader("Métricas de riesgo por cohort")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Par 8", "Par 30", "Par 120", "ROI ratio", "KPIS por cohort"])

    with tab1:
        st.markdown("### Par 8")
        
        to_plot_par8 = os_8_task(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
        to_plot_par8['Mes'] = to_plot_par8.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

        promedio_par30 = os_8_task(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes")

        to_plot_par8 = (pd.concat([to_plot_par8, promedio_par30.assign(Fecha_apertura = "Promedio General")])
                         .rename(columns={"Fecha_apertura": "Cosecha"})
                         .sort_values(by=["Mes", "Cosecha"]
                                      , ascending=[True, True]
                                      , ignore_index=True)
                        ) 

        _, _, _, _, _, _, d = st.columns(7)
        csv4 = convert_df(to_plot_par8.pivot_table(index=["Mes"], columns=["Cosecha"], values="Metric").fillna("") )
        d.download_button(
            label="Descargar CSV",
            data=csv4,
            file_name='par8.csv',
            mime='text/csv'
        )
        st.write("Doble click en la leyenda para aislar")

        fig3 = px.line(to_plot_par8
                    , x="Mes"
                    , y="Metric"
                    , color="Cosecha"
                    )
        fig3.update_traces(line=dict(width=0.8))
        
        
        
        for i in range(len(fig3['data'])):
            if fig3['data'][i]['legendgroup'] == 'Promedio General':
                fig3['data'][i]['line']['color'] = 'black'
                fig3['data'][i]['line']['width'] = 1.2
            if fig3['data'][i]['legendgroup'] == '2022-05':
                fig3['data'][i]['line']['color'] = 'brown'
        
        
        
        fig3.layout.yaxis.tickformat = ',.1%'
        fig3.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        st.plotly_chart(fig3
                        , use_container_width=True
                        , height = 450
                        , theme="streamlit"
                        )
    with tab2:
        st.markdown("### Par 30")
        flag_WO = st.checkbox("Incluir WO")

        par30_df = os_30_task(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
        temp["Mes"] = temp.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)
        par30_df["Mes"] = par30_df.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

        par30_df_WO = os_30_task_con_WO(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
        par30_df_WO["Mes"] = par30_df_WO.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

        to_plot_par30 = par30_df_WO.copy() if flag_WO else par30_df.copy()

        promedio_par30_df = os_30_task(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes").assign(Fecha_apertura = "Promedio General")
        promedio_par30_df_WO = os_30_task_con_WO(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes").assign(Fecha_apertura = "Promedio General")

        promedio_par30 = promedio_par30_df_WO.copy() if flag_WO else promedio_par30_df.copy()

        to_plot_par30 = (pd.concat([to_plot_par30, promedio_par30])
                         .rename(columns={"Fecha_apertura": "Cosecha"})
                         .sort_values(by=["Mes", "Cosecha"]
                                      , ascending=[True, True]
                                      , ignore_index=True)
                        ) 

        _, _, _, _, _, isra, d = st.columns(7)

        # st.markdown(", ".join(temp.columns))
        
        # isra.download_button(
        #     label="Descargar CSV Isra",
        #     data=convert_df(temp
        #                     .filter(["ID_Credito", "Fecha_apertura", "Mes", "balance_sin_ip", "Bucket"])
        #                     .rename(columns={"balance_sin_ip": "balance"})
        #                     .merge(pd.read_csv("Data/cat_ID_Credito.csv")
        #                            , how="left"
        #                            , on="ID_Credito"
        #                            )
        #                    ),
        #     file_name='isra.csv',
        #     mime='text/csv'
        # )
        csv5 = convert_df(to_plot_par30.pivot_table(index=["Mes"], columns=["Cosecha"], values="Metric").fillna(""))
        d.download_button(
            label="Descargar CSV",
            data=csv5,
            file_name='par30.csv',
            mime='text/csv'
        )
        st.write("Doble click en la leyenda para aislar")
        
        fig3 = px.line(to_plot_par30
                    , x="Mes"
                    , y="Metric"
                    , color="Cosecha"
                    )
        fig3.update_traces(line=dict(width=0.8))
        
        
        
        for i in range(len(fig3['data'])):
            if fig3['data'][i]['legendgroup'] == 'Promedio General':
                fig3['data'][i]['line']['color'] = 'black'
                fig3['data'][i]['line']['width'] = 1.2
            if fig3['data'][i]['legendgroup'] == '2022-05':
                fig3['data'][i]['line']['color'] = 'brown'
        
        
        
        fig3.layout.yaxis.tickformat = ',.1%'
        fig3.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        
        
        st.plotly_chart(fig3
                        , use_container_width=True
                        , height = 450
                        , theme="streamlit"
                        )
        
        l1, _, _, _, _ = st.columns(5)
        Mob_selected = l1.selectbox("Selecciona el Mob:"
                                        , [str(i).zfill(2) for i in range(1,13)]
                                        , key="Mob_selected par 30"
                                        , index=2
                                        )
        
        st.markdown("### Zoom Par 30 Mob %i" % int(Mob_selected))
        
        Par30Mob3 = (to_plot_par30
                    .query("Mes == 'M0%s'" % Mob_selected)
                    .sort_values(by=["Metric"]
                                , ascending=[False]
                                , ignore_index=True
                                )
                    .assign(Cosecha = lambda df: df.Cosecha.apply(lambda x: "Promedio" if "Promedio" in x else str(x))
                            , color = lambda df: df.Cosecha.apply(lambda x: "red" if "Promedio" in x else 'blue')

                            )
                    )
        Par30Mob3['category'] = [str(i) for i in Par30Mob3.index]
        
        
        fig4 = px.bar(Par30Mob3
                    , y='Metric'
                    , x='Cosecha'
                    , color="category"
                    , color_discrete_sequence=list(Par30Mob3["color"].values)
                    , text_auto=',.1%'
                    )
        fig4.layout.yaxis.tickformat = ',.1%'
        fig4.layout.xaxis.type = 'category'
        fig4.update_traces(textfont_size=12
                        , textangle=0
                        , textposition="inside"
                        , cliponaxis=False
                        )
        fig4.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        st.plotly_chart(fig4
                        , use_container_width=True
                        , height = 450
                        , theme="streamlit"
                        )
        
    with tab3:
        st.markdown("### Par 120")
        
        to_plot_par120 = Default_rate_task(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
        to_plot_par120['Mes'] = to_plot_par120.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

        promedio_par120 = Default_rate_task(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes")

        to_plot_par120_ = (pd.concat([to_plot_par120, promedio_par120.assign(Fecha_apertura = "Promedio General")])
                         .rename(columns={"Fecha_apertura": "Cosecha"})
                         .sort_values(by=["Mes", "Cosecha"]
                                      , ascending=[True, True]
                                      , ignore_index=True)
                        ) 

        _, _, _, _, _, _, dd = st.columns(7)
        csv6 = convert_df(to_plot_par120_.pivot_table(index=["Mes"], columns=["Cosecha"], values="Metric").fillna(""))
        dd.download_button(
            label="Descargar CSV",
            data=csv6,
            file_name='par120.csv',
            mime='text/csv'
        )
        st.write("Doble click en la leyenda para aislar")
        
        fig4 = px.line(to_plot_par120_
                    , x="Mes"
                    , y="Metric"
                    , color="Cosecha"
                    )
        fig4.update_traces(line=dict(width=0.8))
        
        
        
        for i in range(len(fig4['data'])):
            if fig4['data'][i]['legendgroup'] == 'Promedio General':
                fig4['data'][i]['line']['color'] = 'black'
                fig4['data'][i]['line']['width'] = 1.2
            if fig4['data'][i]['legendgroup'] == '2022-05':
                fig4['data'][i]['line']['color'] = 'brown'
        
        
        
        fig4.layout.yaxis.tickformat = ',.1%'
        fig4.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        
        
        st.plotly_chart(fig4
                        , use_container_width=True
        )

        m1, _, _, _, _ = st.columns(5)
        Mob_selected = m1.selectbox("Selecciona el Mob:"
                                        , [str(i).zfill(2) for i in range(1,13)]
                                        , key="Mob_selected par 120"
                                        , index=11
                                        )
        
        st.markdown("### Zoom Par 120 Mob %i" % int(Mob_selected))

        Par120Mob3 = (to_plot_par120_
                      .query("Mes == 'M0%s'" % Mob_selected)
                        .sort_values(by=["Metric"]
                                    , ascending=[False]
                                    , ignore_index=True
                                    )
                        .assign(Cosecha = lambda df: df.Cosecha.apply(lambda x: "Promedio" if "Promedio" in x else str(x))
                                , color = lambda df: df.Cosecha.apply(lambda x: "red" if "Promedio" in x else 'blue')

                                )
                        )

        Par120Mob3['category'] = [str(i) for i in Par120Mob3.index]

        fig8 = px.bar(Par120Mob3
                    , y='Metric'
                    , x='Cosecha'
                    , color="category"
                    , color_discrete_sequence=list(Par120Mob3["color"].values)
                    , text_auto=',.1%'
                    )
        fig8.layout.yaxis.tickformat = ',.1%'
        fig8.layout.xaxis.type = 'category'
        fig8.update_traces(textfont_size=12
                        , textangle=0
                        , textposition="inside"
                        , cliponaxis=False
                        )
        fig8.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        st.plotly_chart(fig8
                        , use_container_width=True
                        , height = 450
                        , theme="streamlit"
                        )


    with tab4:
        st.markdown("### ROI ratio")
        _d_, _, _, _, d = st.columns(5)

        metric = _d_.selectbox("Selecciona métrica:"
                              , ["ROI ratio", "ROI interes ratio"]
                              )
        if metric == "ROI ratio":
            to_plot_roi = roi_ratio_task(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
            to_plot_roi['Mes'] = to_plot_roi.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)
            promedio_roi = roi_ratio_task(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes")
        elif metric == "ROI interes ratio":
            to_plot_roi = roi_interes_ratio_task(temp.query("Fecha_apertura >= '2021-08'"), "Fecha_apertura")
            to_plot_roi['Mes'] = to_plot_roi.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)
            promedio_roi = roi_interes_ratio_task(YoFio.query("Fecha_apertura >= '2021-08'"), "Mes")

        to_plot_roi_ = (pd.concat([to_plot_roi, promedio_roi.assign(Fecha_apertura = "Promedio General")])
                            .rename(columns={"Fecha_apertura": "Cosecha"})
                            .sort_values(by=["Mes", "Cosecha"]
                                        , ascending=[True, True]
                                        , ignore_index=True)
                            )

        
        csv7 = convert_df(to_plot_roi_.pivot_table(index=["Mes"], columns=["Cosecha"], values="Metric").fillna(""))
        d.download_button(
            label="Descargar CSV",
            data=csv7,
            file_name='roi.csv',
            mime='text/csv'
        )
        if metric == "ROI ratio":
            st.write("Pagos a capital, intereses y moratorios dividido entre capital desembolsado. La línea punteada azul representa el retorno positivo. ")
        elif metric == "ROI interes ratio":
            st.write("Pagos a intereses y moratorios dividido entre capital desembolsado. La línea punteada azul representa el retorno positivo. ")
        st.write("(Doble click en la leyenda para aislar)")

        fig7 = px.line(to_plot_roi_.rename(columns={"Mes": "MOB"})
                    , x="MOB"
                    , y="Metric"
                    , color="Cosecha"
                    )
        fig7.update_traces(line=dict(width=0.8))

        for i in range(len(fig7['data'])):
            if fig7['data'][i]['legendgroup'] == 'Promedio General':
                fig7['data'][i]['line']['color'] = 'black'
                fig7['data'][i]['line']['width'] = 1.2
            if fig7['data'][i]['legendgroup'] == '2022-05':
                fig7['data'][i]['line']['color'] = 'brown'

        fig7.layout.yaxis.tickformat = ',.2'
        fig7.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')

        if metric == "ROI ratio":
            # Add a horizontal line at y=1 to represent the break-even point
            fig7.add_shape(type="line"
                        , x0=0
                        , x1=len(to_plot_roi_.Mes.unique())
                        , y0=1
                        , y1=1
                        , line=dict(color="darkblue", width=1, dash="dash"))

        st.plotly_chart(fig7, use_container_width=True, height = 450, theme="streamlit")







    with tab5:
        st.markdown("### KPIs por cohort")
        n1, _, _, _, _ = st.columns(5)

        cohort_sel = n1.selectbox("Selecciona el cohort:"
                                  , ["Promedio General"] + list(df_cosechas.Mes_apertura.drop_duplicates().sort_values(ignore_index=True).values)[5:]
                                  , key="cohort_sel"
                                  )
        
        flag_kpis = st.checkbox("Filtrar hasta 2022-08")
        if flag_kpis:
            promedio_par30_df = os_30_task(YoFio.query("Mes >= '2021-08' and Mes <= '2022-08'"), "Mes").assign(Fecha_apertura = "Promedio General")
            promedio_par30_df_WO = os_30_task_con_WO(YoFio.query("Mes >= '2021-08' and Mes <= '2022-08'"), "Mes").assign(Fecha_apertura = "Promedio General")
            promedio_par120 = Default_rate_task(YoFio.query("Mes >= '2021-08' and Mes <= '2022-08'"), "Mes")

            to_plot_par120_ = (pd.concat([to_plot_par120, promedio_par120.assign(Fecha_apertura = "Promedio General")])
                            .rename(columns={"Fecha_apertura": "Cosecha"})
                            .sort_values(by=["Mes", "Cosecha"]
                                        , ascending=[True, True]
                                        , ignore_index=True)
                            ) 


        to_plot = (pd.concat([par30_df, promedio_par30_df])
                   .drop(columns="Fecha_reporte")
                   .rename(columns={"Metric": "Par30"})
                   .merge(pd.concat([par30_df_WO, promedio_par30_df_WO])
                          .drop(columns="Fecha_reporte")
                          .rename(columns={"Metric": "Par30_WO"})
                          , on=["Mes", "Fecha_apertura"]
                          , how="left"
                         )
                    .rename(columns={"Fecha_apertura": "Cosecha"})
                    .merge(to_plot_par120_
                           .drop(columns="Fecha_reporte")
                           .rename(columns={"Metric": "Par120"})
                           , on=["Mes", "Cosecha"]
                           , how="left"
                          )
                    .melt(id_vars=["Mes", "Cosecha"]
                             , var_name="Metric"
                             , value_name="Value"
                             , ignore_index=True
                            )
                    
                    
                   )
        
        fig9 = px.line(to_plot
                       .query("Cosecha == '%s'" % cohort_sel)

                       , x="Mes"
                       , y="Value"
                       , color="Metric"
                      )
        fig9.layout.yaxis.tickformat = ',.0%'
        fig9.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
        fig9.update_layout(
            xaxis_title="Mes"
            , yaxis_title="Porcentaje"
        )
        fig9.update_layout(
            title={
                'text': "KPIs "+cohort_sel
                , 'y':0.9
                , 'x':0.5
                , 'xanchor': 'center'
                , 'yanchor': 'top'}
        )
        if "erick" in os.getcwd():
            csv9 = convert_df(to_plot)
        else:
            csv9 = convert_df(to_plot.query("Cosecha == '%s'" % cohort_sel))

        _, _, _, _, _, _, ff = st.columns(7)
        ff.download_button(
            label="Descargar CSV",
            data=csv9,
            file_name='pares %s.csv' % cohort_sel,
            mime='text/csv'
        )
        
        st.plotly_chart(fig9
                        , use_container_width=True
                        , height = 450
                        , theme="streamlit"
                        )



    
