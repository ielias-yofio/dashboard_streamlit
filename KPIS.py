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
# Mo'dulos propios, están a la par de este script
#
from _utils import convert_df, format_column, get_date, rango_lim_credito, Roll_t, prod, clean_roll
from _utils import Bucket_Monthly, Bucket_Biweekly, Bucket_Weekly, diff_month
from _metrics import current_pct_task, current_sin_ip_pct_task, imora_task, delta_pct_task, Default_rate_task, roi_task, roi_ratio_task
from _metrics import roi_interes_ratio_task, os_8_task, os_30_task, os_60_task, os_90_task, roll_0_1_task, perdida_task, perdida_hasta_120_task
from _metrics import coincidential_task, lagged_task, total_amount_disbursed_task, OSTotal_sincastigos_task, OSTotal_concastigos_task, credit_limit
from _metrics import  SaldoVencido_task, NumCuentas_task, Activas_task, Mora_task, reestructura_task, os_60_monto_task, os_60_cuentas_task
from _metrics import lim_credito_avg_task, metrica_task, os_30_task_con_WO

#
# Logo de YoFio
#
if "logo_yofio" not in st.session_state:
    import requests
    url = "https://v.fastcdn.co/u/c2e5d077/58473217-0-Logo.png"
    st.session_state["logo_yofio"] = Image.open(requests.get(url, stream=True).raw)

if "autor" not in st.session_state:
    st.session_state["autor"] = "Erick Santillan de Mauleón"

show_pages_from_config()

st.set_page_config(
    layout='wide'
    , initial_sidebar_state='expanded'
    , page_title="KPIS de riesgo"
    , page_icon=st.session_state["logo_yofio"]
    , menu_items={"About": "This is a description of the app."}
)

# Optional -- adds the title and icon to the current page
st.title("KPIS de riesgo")

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
# Primer filtro
###########################################
if "style_css" not in st.session_state:
    import requests
    response = requests.get("https://raw.githubusercontent.com/ErickdeMauleon/data/main/style.css")
    st.session_state["style_css"] = response.text

st.markdown(f'<style>{st.session_state["style_css"]}</style>', unsafe_allow_html=True)
st.sidebar.header('Dashboard KPIS de riesgo')

st.sidebar.subheader('Selecciona parametros:')

if "corte_seleccionado" not in st.session_state:
    st.session_state["corte_seleccionado"] = "Mensual"

_cortes = st.sidebar.selectbox(
    'Selecciona los cierres:'
    , ('Por mes', 'Por quincenas', 'Por semanas')
)
    
cortes = {"Por quincenas": 'Catorcenal'
        , "Por mes": 'Mensual'
        , "Por semanas":  'Semanal'
        }[_cortes]

if cortes != st.session_state["corte_seleccionado"]:
    st.session_state["corte_seleccionado"] = cortes
    nueva_vista = True
else:
    nueva_vista = False


# Definir el año de inicio
año_inicio = 2021

# Obtener el año actual para iterar hasta el presente
año_actual = datetime.now().year
mes_actual = datetime.now().month

# Crear una lista de comprensión con los días 15 y últimos días de cada mes desde 2021
dias_15_y_ultimos = [
    (datetime(año, mes, 15).strftime('%Y-%m-%d'),  # Día 15
     (datetime(año, mes, 1) - timedelta(days=1)).strftime('%Y-%m-%d'))  # Último día
    for año in range(año_inicio, año_actual + 1)
    for mes in range(1, 13)
    if año <
      año_actual or (año == año_actual and mes <= mes_actual)
]

# Convertir la lista de tuplas a una lista de strings
dias_15_y_ultimos = [x[0] for x in dias_15_y_ultimos] + [x[1] for x in dias_15_y_ultimos]



filtro_dict = {'Catorcenal': {"f2": ", ".join(["'%s'" % get_date(i) for i in range(160) if i % 2 == 0])
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
               , 'Quincena comercial': {"f2": ", ".join(["'%s'" % i for i in dias_15_y_ultimos])
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
                                                                                            , periods=70
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


###########################################
# Data
###########################################

if ("BQ" not in st.session_state) or (nueva_vista):
    
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
    st.session_state["BQ"] = (
        pd.concat([pd.read_csv("Data/"+f) for f in os.listdir("Data/") if "BQ_reduced" in f and "csv" in f])
        .query("Fecha_reporte in (%s)" % f2)
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
    st.session_state["BQ"]["Edad"] = (
        st.session_state["BQ"]["Edad"]
        .apply(lambda x: "De %i a %i" % (int(x//5)*5, int(x//5)*5+4))
        .replace({"De 60 a 64": "Mayor de 60"
                , "De 65 a 69": "Mayor de 60"
                , "De 70 a 74": "Mayor de 60"
                , "De 75 a 79": "Mayor de 60"
                , "De 80 a 84": "Mayor de 60"
                , "De 20 a 24": "De 20 a 29"
                , "De 25 a 29": "De 20 a 29"
                })
    )
    st.session_state["BQ"]["allow_disbursements"] = st.session_state["BQ"]["allow_disbursements"].fillna(0) # 0: Not allowed, 1: Allowed
    st.session_state["BQ"]["Bucket"] = st.session_state["BQ"]["Dias_de_atraso"].apply(filtro_dict["Bucket"])
    st.session_state["BQ"] = (
        st.session_state["BQ"]
        .groupby(
            [
                "Fecha_reporte"
                , "term_type"
                , "Cartera_YoFio"
                , "n_ampliaciones"
                , "genero_estimado"
                , "Fecha_apertura"
                , "Edad"
                , "CP"
                , "Rango"
                , "industry_cve"
                , "Status_credito"
                , "Creado_dsoto"
                , "Bucket"
                , "allow_disbursements"
            ]
            , as_index=False
        )
        .agg(
            account_id = ("ID_Credito", "count")
            , balance = ("balance", "sum")
        )
    )
    st.session_state["BQ"] = st.session_state["BQ"][st.session_state["BQ"]["Fecha_reporte"] == st.session_state["BQ"]["Fecha_reporte"].max()]
    

temp = st.session_state["BQ"].copy()
###########################################












##################################################################
##
## STREAMLIT APP
##
##################################################################





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
    temp = temp[temp["Edad"].isin(edad)]

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



rangos_list = list(st.session_state["BQ"]["Rango"].unique())
rangos_list.sort()
rangos = st.sidebar.multiselect('Selecciona el rango del límite de credito'
                                 , ['Todos'] + rangos_list
                                 , default='Todos'
                                 )

industry_list = list(st.session_state["cat_industry"]["industry"].unique())
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
    

# YoFio = (st.session_state["BQ"]
#          .query("Fecha_reporte in (%s)" % f2)
#          .assign(Bucket = lambda df: df.Dias_de_atraso.apply(filtro_dict["Bucket"]))
#          .sort_values(by=["ID_Credito", "Fecha_reporte"]
#                          , ignore_index=True)
#         )
# YoFio["Mes"] = YoFio.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

temp = temp.query(filtro_BQ)


if len(temp) == 0:
    st.write("No hay clientes con las condiciones que pides.")
else:
    
    # Row A
    _max = temp.Fecha_reporte.max()
    
    st.markdown("### Tamaño cartera (fotografía al %s)" % _max)

    _b1, _b2, _b3 = st.columns(3)
    _b4, _b5 = st.columns(2)
    _b7, _, _, _, _b6 = st.columns(5)

    kpi_sel_0 = _b1.selectbox("Selecciona la métrica", 
                              ["Número de cuentas"
                              , "Cuentas (sin castigo)"
                              , "Cuentas (castigadas)"
                              , "Cuentas activas"
                              , "Cuentas inactivas"
                              , "Cuentas bloqueadas"
                              , "Cuentas bloqueadas 2"
                              , "Saldo Total"
                              , "Saldo Total (sin castigos)"
                              , "Saldo Total (castigado)"
                              ])

    factor_sel_0 = _b2.selectbox("Selecciona la vista a desagregar", 
                                ["Por tipo de corte"
                                , "Por zona"
                                , "Por analista"
                                , "Por edad del tiendero"
                                , "Por estado de la tienda"
                                , "Por rango de crédito"
                                , "Por cohort"
                                , "Por semestre de cohort"
                                , "Por municipio"
                                , "Por género del tiendero"
                                , "Por giro del negocio"
                                ])
    
    _kpi = {"Número de cuentas": {"y": "account_id", "query": ""}
            , "Cuentas (sin castigo)": {"y": "account_id", "query": "and Bucket.str.contains('120') == False"}
            , "Cuentas (castigadas)": {"y": "account_id", "query": "and Bucket.str.contains('120')"}
            , "Cuentas activas": {"y": "account_id", "query": "and Status_credito != 'I' and Bucket.str.contains('120') == False"}
            , "Cuentas inactivas": {"y": "account_id", "query": "and (Status_credito == 'I' or Bucket.str.contains('120'))"}
            , "Cuentas bloqueadas 2": {"y": "account_id", "query": "and allow_disbursements == 0 and Status_credito == 'I' and Bucket.str.contains('120')"}
            , "Cuentas bloqueadas": {"y": "account_id", "query": "and allow_disbursements == 0 and Status_credito == 'I' and Bucket.str.contains('120') == False"}
            , "Saldo Total": {"y": "balance", "query": ""}
            , "Saldo Total (sin castigos)": {"y": "balance", "query": "and Bucket.str.contains('120') == False"}
            , "Saldo Total (castigado)": {"y": "balance", "query": "and Bucket.str.contains('120')"}
           }[kpi_sel_0]
           
    factor = {"Por tipo de corte": "term_type"
              , "Por zona": "ZONA"
              , "Por analista": "Analista"
              , "Por edad del tiendero": "Edad"
              , "Por estado de la tienda": "Estado"
              , "Por rango de crédito": "Rango"
              , "Por cohort": "Fecha_apertura"
              , "Por municipio": "Municipio"
              , "Por semestre de cohort": "Semestre"
              , "Por género del tiendero": "genero_estimado"
              , "Por giro del negocio": "industry"
             }[factor_sel_0]

    comp_sel_0 = _b3.selectbox("Selecciona la comparación", 
                                ["Valores absolutos"
                                , "Valores porcentuales"
                                ])
    
    status_list = ["CURRENT", "APPROVED", "LATE", "INACTIVE"] 
    status_list.sort()
    status_selected = _b4.multiselect("Selecciona el status de la cuenta"
                                      , status_list
                                      , default=status_list
                                    )
    status_selected = [s[0] for s in status_selected]
    flag_sort = _b7.checkbox("Ordenar alfabéticamente", value=False)

    if factor in ["Estado", "Municipio"]:
        cat_auxiliar = st.session_state["cat_municipios"]
    elif factor == "Analista":
        cat_auxiliar = st.session_state["cat_advisors"]
    elif factor == "industry":
        cat_auxiliar = st.session_state["cat_industry"]
    else:
        cat_auxiliar = None

    formateada, temp = format_column(temp, factor, cat_auxiliar)
    formateada, YoFio = format_column(st.session_state["BQ"], factor, cat_auxiliar)
    factor = factor + "_formato" * int(formateada)


    # _start, _end = st.select_slider(
    #     "Selecciona el rango de días de atraso",
    #     options=list(range(0,122)),
    #     value=(0, 121)
    # )
    # if _end == 121:
    #     _end = 10000

    _to_plot = (temp
                .query("Fecha_reporte == '%s'" % _max)
                # .query("Dias_de_atraso >= %i and Dias_de_atraso <= %i" % (_start, _end))
                .query("Status_credito.isin(@status_selected)")
                # .assign(account_id = 1)
                .query("Fecha_reporte == '%s' %s" % (_max, _kpi["query"]))
                .groupby([factor])
                .agg({"account_id": "sum"
                        , "balance": "sum"})
                .reset_index()
               )
    _to_plot0 = (YoFio
                #  .query("Dias_de_atraso >= %i and Dias_de_atraso <= %i" % (_start, _end))
                 .query("Status_credito.isin(@status_selected)")
                 .query("Fecha_reporte == '%s'" % _max)
                #  .assign(account_id = 1)
                 .groupby([factor])
                 .agg({"account_id": "sum"
                       , "balance": "sum"})
                 .reset_index()
                )



    if comp_sel_0 == 'Valores porcentuales':
        _to_plot["account_id"] = _to_plot["account_id"] / _to_plot["account_id"].sum()
        _to_plot["balance"] = _to_plot["balance"] / _to_plot["balance"].sum()
        _to_plot0["account_id"] = _to_plot0["account_id"] / _to_plot0["account_id"].sum()
        _to_plot0["balance"] = _to_plot0["balance"] / _to_plot0["balance"].sum()
    

    _to_plot0 = (_to_plot0
                 .merge(_to_plot
                    , how="left"
                    , on=[factor]
                    , suffixes=["_avg", ""]
                    )
                 .fillna(0)
                 .sort_values(by=[factor if flag_sort else _kpi["y"]]
                            , ascending=[flag_sort]
                                  )
                )

    if comp_sel_0 != 'Valores porcentuales':
        fig0 = px.bar(_to_plot
                      .sort_values(by=[factor if flag_sort else _kpi["y"]]
                                   , ascending=[flag_sort]
                                  )
                     , y=_kpi["y"]
                     , x=factor
                     , labels={factor: factor_sel_0
                               , _kpi["y"]: kpi_sel_0
                              }
                    )
        if comp_sel_0 == 'Valores porcentuales':
            fig0.layout.yaxis.tickformat = ',.1%'
            fig0.layout.yaxis.range = [0, 1]
        else:
            fig0.layout.yaxis.tickformat = ',.0f'
            if _kpi["y"] == "balance":
                fig0.layout.yaxis.tickprefix = '$'
        
    else:
        fig0 = go.Figure()
        fig0.add_trace(go.Bar(x=_to_plot0[factor]
                              , y=_to_plot0[_kpi["y"]+"_avg"]
                              , name="Promedio YoFio"
                              , marker_color="lightblue"
                             )
                      )
        fig0.add_trace(go.Bar(x=_to_plot0[factor]
                              , y=_to_plot0[_kpi["y"]]
                              , width=len(_to_plot0)*[0.5]
                              , name="Cartera seleccionada"
                              , marker_color='royalblue'
                             )
                       )
        fig0.update_layout(barmode = 'overlay')
        fig0.layout.yaxis.tickformat = ',.1%'
        fig0.layout.yaxis.range = [0, 1]


    fig0.layout.xaxis.type = 'category'
    fig0.update_traces(textfont_size=12
                      , textangle=0
                      , textposition="inside"
                      , cliponaxis=False
                      )
    fig0.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')




    _csv = convert_df(_to_plot)

    _b6.download_button(
        label="Descargar CSV",
        data=_csv,
        file_name='cortes.csv',
        mime='text/csv',
    )


    st.plotly_chart(fig0
                    , use_container_width=True
                    , height = 450
                    , theme="streamlit"
                    )


