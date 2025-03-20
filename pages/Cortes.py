# Erick Santillan


#
# Importar modulos
#
import json
import streamlit as st
import os
import pandas as pd
import plotly.express as px 
import socket
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
    , ('Por mes', 'Por quincena comercial', 'Por quincenas', 'Por semanas')
)
    
cortes = {"Por quincena comercial": 'Quincena comercial'
          , "Por catorcena": 'Catorcenal'
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
    st.session_state["BQ"] = (pd.concat([pd.read_csv("Data/"+f) for f in os.listdir("Data/") if "BQ_reduced" in f and "csv" in f]))
    if socket.gethostname() == "erick-huawei":
        print(st.session_state["BQ"].columns)
    st.session_state["BQ"] = (st.session_state["BQ"]
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

try:
    YoFio = (st.session_state["BQ"]
            .query("Fecha_reporte in (%s)" % f2)
            .assign(Bucket = lambda df: df.Dias_de_atraso.apply(filtro_dict["Bucket"]))
            .sort_values(by=["ID_Credito", "Fecha_reporte"]
                            , ignore_index=True)
            )
except AttributeError:
    # Pedir al usuario que actualice la página F5
    st.warning("Por favor actualiza la página (CTRL + SHIFT + R) para recargar los datos.")

    # Hay una imagen en "Data/shortcuts.png" que se puede mostrar para ayudar al usuario
    st.image("Data/shortcuts.png")

    # No se puede continuar con el script, detener todo
    st.stop()
except KeyError:
    st.warning("Por favor actualiza la página (CTRL + SHIFT + R) para recargar los datos.")
    st.image("Data/shortcuts.png")
    st.stop()



YoFio["Mes"] = YoFio.apply(lambda x: "M" + str(diff_month(x['Fecha_reporte'], x['Fecha_apertura']+"-01")).zfill(3), axis=1)

temp = temp.query(filtro_BQ)

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
    
    
    
    
    
    st.markdown('### Cortes')
    st.markdown("Saldo de compra de central de abastos o a distribuidor (aún no desembolsado)")
    flag_sort = ~st.checkbox("Ordenar columnas al revés")
    cols = list(temp["Fecha_reporte"].unique())
    cols.sort(reverse=flag_sort)


    st.dataframe(temp
                 .groupby(["Fecha_reporte"])
                 .agg({"saldo": "sum"})
                 .transpose()
                 .applymap(lambda x: "${:,.0f}".format(x))
                 .filter(cols)
                 .assign(Saldo="Total")
                 .rename(columns={"Saldo": "Saldo current"})
                 .set_index("Saldo current")
                 , use_container_width=True)
    
    _d1, _d2, _d3 = st.columns((4,7,2))
    
    _by = _d1.selectbox("Selecciona la métrica:", ["Por saldo", "Por número de cuentas"])
    agg_by = pd.NamedAgg("balance", "sum") if _by == "Por saldo" else pd.NamedAgg("ID_Credito", "nunique")
    temp_agg_to_show = pd.concat([
        (temp
          .groupby(["Bucket", "Fecha_reporte"])
          .agg(Value = agg_by)
          .reset_index()
          .pivot(index=["Bucket"]
                 , columns="Fecha_reporte"
                 , values="Value"
                 )
          )
        , (temp
           .query("Dias_de_atraso >= 120 and Dias_de_atraso_ant < 120")
           .assign(Bucket = "%s. delta" % str(N+2).zfill(2 - int(N+2 < 10)))
           .groupby(["Bucket", "Fecha_reporte"])
           .agg(Value = agg_by)
           .reset_index()
           .pivot(index="Bucket"
                  , columns="Fecha_reporte"
                  , values="Value"
                  )
           )
        ]).fillna(0)
        
    
    
    # cols = list(temp_agg_to_show.columns)[::-1]
    
    temp_agg_to_show = (pd.DataFrame({"Bucket": filtro_dict["buckets"]})
                        .merge(temp_agg_to_show
                                .reset_index()
                                , how="left")
                            .set_index("Bucket")
                            .fillna(0)
                            .filter(cols)
                        )
    
    csv0 = convert_df(temp_agg_to_show.reset_index())

    # DuplicateWidgetID: There are multiple identical st.download_button widgets with the same generated key. To fix this error, please pass a unique key argument to st.download_button.
    _d3.download_button(
        label="Descargar CSV"
        , data=csv0
        , file_name='cortes.csv'
        , mime='text/csv'
        , key="cortes"

    )

    
    
    st.dataframe(temp_agg_to_show
                 .applymap(lambda x: "${:,.0f}".format(x) if _by == "Por saldo" else "{:,.0f}".format(x))
                 , use_container_width=True)
    _renamed = "Saldo menor a 120 días" if _by == "Por saldo" else "Cuentas con atraso <120 días"
    st.dataframe(temp_agg_to_show
                 .iloc[:N+1]
                 .sum()
                 .apply(lambda x: "${:,.0f}".format(x) if _by == "Por saldo" else "{:,.0f}".format(x))
                 .to_frame()
                 .transpose()
                 .assign(i="Total")
                 .rename(columns={"i": _renamed})
                 .set_index(_renamed)
                 , use_container_width=True)
    
    st.markdown('### Métricas')
    col1, col2, col3, col5 = st.columns(4)
    kpi_selected = col1.selectbox("Selecciona la métrica", 
                                  ["Current %"
                                   , "Current % (sin compras inventario o proveedor)"
                                   , "%IMORA"
                                   , "Delta %"
                                   , "Saldo OS+120 %"
                                   , "ROI"
                                   , "ROI ratio"
                                   , "ROI interes ratio"
                                   , "OS 8 mas %"
                                   , "OS 30 mas %"
                                   , "OS 60 mas %"
                                   , "OS 90 mas %"
                                   , "Roll 0 a 1"
                                #    , "Pérdida esperada"
                                   , "Pérdida esperada (saldo hasta 120 días)"
                                   , "Coincidential WO"
                                   , "Lagged WO"
                                   , "Total monto desembolsado"
                                   , "Saldo Total (sin castigos)"
                                   , "Saldo Total (con castigos)"
                                   , "Saldo Vencido"
                                   , "Monto promedio"
                                   , "Número de cuentas"
                                   , "Número de cuentas Activas"
                                   , "Número de cuentas Mora"
                                   , "Reestructuras %"
                                   , "Saldo mayor a 60 días"
                                   , "Cuentas en mora mayor a 60 días"
                                   , "Límite de crédito promedio"
                                   , "Días hasta la primera ampliación"
                                   ]
                                   +
                                   ["Métrica que necesito"]*("erick" in os.getcwd())
                                   )

    vista_selected = col2.selectbox("Selecciona la vista a desagregar:", 
                                   ["-- Sin vista --"
                                    , "Por tipo de corte"
                                    , "Por número de ampliaciones"
                                    , "Por zona"
                                    , "Por analista"
                                    , "Por estado de la tienda"
                                    , "Por edad del tiendero"
                                    , "Por rango de crédito"
                                    , "Por cohort"
                                    , "Por semestre de cohort"
                                    , "Por municipio"
                                    , "Por género del tiendero"
                                    , "Por giro del negocio"
                                    ])
    Promedio_comparar = col3.selectbox("Selecciona el promedio a comparar:"
                                       , ["Promedio YoFio", "Promedio sin la cartera seleccionada"])
    
           
    vista = {"Por tipo de corte": "term_type"
              , "Por zona": "ZONA"
              , "Por número de ampliaciones": "n_ampliaciones"
              , "Por analista": "Analista"
              , "Por edad del tiendero": "Edad"
              , "Por estado de la tienda": "Estado"
              , "Por cohort": "Fecha_apertura"
              , "Por semestre de cohort": "Semestre_cohort"
              , "Por rango de crédito": "Rango"
              , "Por municipio": "Municipio"
              , "Por género del tiendero": "genero_estimado"
              , "Por giro del negocio": "industry"
              , "-- Sin vista --": ""
             }[vista_selected]
    
    kpi = {"Current %": "porcentaje" 
            , "Current % (sin compras inventario o proveedor)": "porcentaje"
            , "%IMORA": "porcentaje"
            , "Delta %": "porcentaje"
            , "Saldo OS+120 %": "porcentaje"
            , "ROI": "dinero"
             , "OS 8 mas %": "porcentaje"
             , "OS 30 mas %": "porcentaje"
             , "OS 60 mas %": "porcentaje"
             , "OS 90 mas %": "porcentaje"
             , "Roll 0 a 1": "porcentaje"
             , "Pérdida esperada": "porcentaje"
             , "Pérdida esperada (saldo hasta 120 días)": "porcentaje"
             , "Coincidential WO": "porcentaje"
             , "Total monto desembolsado": "dinero"
             , "Lagged WO": "porcentaje"
             , "Saldo Total (sin castigos)": "dinero"
             , "Saldo Total (con castigos)": "dinero"
             , "Saldo Vencido": "dinero" 
             , "Monto promedio": "dinero"
             , "Número de cuentas": "cuentas"
             , "Número de cuentas Activas": "cuentas"
             , "Número de cuentas Mora": "cuentas"
             , "Reestructuras %": "porcentaje"
             , "Saldo mayor a 60 días": "dinero"
             , "Cuentas en mora mayor a 60 días": "cuentas"
             , "Límite de crédito promedio": "dinero"
             , "Días hasta la primera ampliación": "cuentas"
             , "Métrica que necesito": "cuentas"
             , "ROI ratio": "cuentas"
             , "ROI interes ratio": "cuentas"
             }[kpi_selected]

    kpi_task = {"Current %": current_pct_task 
                , "Current % (sin compras inventario o proveedor)": current_sin_ip_pct_task
                , "%IMORA": imora_task
                , "Delta %": delta_pct_task
                 , "Saldo OS+120 %": Default_rate_task
                 , "ROI": roi_task
                 , "ROI ratio": roi_ratio_task
                 , "ROI interes ratio": roi_interes_ratio_task
                 , "OS 8 mas %": os_8_task
                 , "OS 30 mas %": os_30_task
                 , "OS 60 mas %": os_60_task
                 , "OS 90 mas %": os_90_task
                 , "Roll 0 a 1": roll_0_1_task
                 , "Pérdida esperada": perdida_task
                 , "Pérdida esperada (saldo hasta 120 días)": perdida_hasta_120_task
                 , "Coincidential WO": coincidential_task
                 , "Lagged WO": lagged_task
                 , "Total monto desembolsado": total_amount_disbursed_task
                 , "Saldo Total (sin castigos)": OSTotal_sincastigos_task
                 , "Saldo Total (con castigos)": OSTotal_concastigos_task
                 , "Monto promedio": credit_limit
                 , "Saldo Vencido": SaldoVencido_task 
                 , "Número de cuentas": NumCuentas_task
                 , "Número de cuentas Activas": Activas_task
                 , "Número de cuentas Mora": Mora_task
                 , "Reestructuras %": reestructura_task
                 , "Saldo mayor a 60 días": os_60_monto_task
                 , "Cuentas en mora mayor a 60 días": os_60_cuentas_task
                 , "Límite de crédito promedio": lim_credito_avg_task
                #  , "Días hasta la primera ampliación": tiempo_hasta_primera_ampliacion_task
                 }
    if "erick" in os.getcwd():
        kpi_task["Métrica que necesito"] = metrica_task

    kpi_task = kpi_task[kpi_selected]


    if kpi_selected == 'Lagged WO':
        _auxiliares = [YoFio[["Fecha_reporte"]].drop_duplicates()]
    elif kpi_selected in ['Pérdida esperada', 'Pérdida esperada (saldo hasta 120 días)', 'Roll 0 a 1']:
        _auxiliares = [cortes, N]
    elif kpi_selected in ['Días hasta la primera ampliación']:
        _auxiliares = [st.session_state["BQ"]]
    else:
        _auxiliares = []

    
    
    kpi_des = {"Current %": "Saldo en Bucket_Current dividido entre Saldo Total (sin castigos)" 
               , "Current % (sin compras inventario o proveedor)": "Saldo en Bucket_Current sin incluir saldo de compras a proveedor o inventario dividido entre Saldo Total (sin castigos)"
               , "%IMORA": "Suma de últimos 12 deltas móviles dividido entre Saldo Total (sin castigos) más suma de últimos 12 deltas móviles."
               , "Delta %": "Saldo en bucket delta del mes multiplicado por 12 dividido entre Saldo Total (sin castigos) más suma de últimos 12 deltas móviles."
               , "Saldo OS+120 %": "Saldo a más de 120 días dividido entre Saldo Total (incluyendo castigos)"
               , "ROI": "Pagos a capital, interés y moratorios menos capital desembolsado"
               , "OS 8 mas %": "Saldo a más de 8 días de atraso dividido entre Saldo Total (sin castigos)"
               , "OS 30 mas %": "Saldo a más de 30 días de atraso dividido entre Saldo Total (sin castigos)"
               , "OS 60 mas %": "Saldo a más de 60 días de atraso dividido entre Saldo Total (sin castigos)"
               , "OS 90 mas %": "Saldo a más de 90 días de atraso dividido entre Saldo Total (sin castigos)"
               , "Roll 0 a 1": "Saldo rodado de bucket 0 a 1."
               , "Total monto desembolsado": "Monto desembolsado acumulado (desembolsos y compras)."
               , "Pérdida esperada": "Roll anualizado por saldo Current entre Saldo Total (incluyendo castigos). Valor probabilístico."
               , "Pérdida esperada (saldo hasta 120 días)": "Roll anualizado por saldo Current entre Saldo Total (sin incluir castigos). Valor probabilístico."
               , "Coincidential WO": "Bucket Delta dividido entre Saldo Total (sin castigos)"
               , "Lagged WO": "Bucket Delta dividido entre Saldo Total (sin castigos) de hace 5 períodos."
               , "Saldo Total (sin castigos)": "Saldo Total sin bucket 120"
               , "Saldo Vencido": "Saldo en status LATE"
               , "Saldo Total (con castigos)": "Saldo Total incluyendo bucket 120"
               , "Monto promedio": "Límite de crédito promedio."
               , "Número de cuentas": "Total cuentas colocadas (acumuladas)"
               , "Reestructuras %": "Porcentaje de cuentas reestructuradas sin considerar castigadas."
               , "Número de cuentas Activas": "Cuentas en CURRENT o LATE"
               , "Número de cuentas Mora": "Cuentas en LATE"
               , "Saldo mayor a 60 días": "Saldo mayor a 60 días (sin castigos)"
               , "Cuentas en mora mayor a 60 días": "Cuentas en mora mayor a 60 días (sin castigos)"
               , "Límite de crédito promedio": "Límite de crédito promedio"
               , "Días hasta la primera ampliación": "Días hasta la primera ampliación"
               , "ROI ratio": "Pagos a capital, interés y moratorios dividido entre capital desembolsado."
               , "ROI interes ratio": "Pagos a interés y moratorios dividido entre capital desembolsado."
              }
    if "erick" in os.getcwd():
        kpi_des["Métrica que necesito"] = ""

    kpi_des = kpi_des[kpi_selected]
    
    formateada, temp = format_column(temp, vista)
    formateada, YoFio = format_column(YoFio, vista)
    vista = vista + "_formato" * int(formateada)


    if vista == "":
        Cartera = kpi_task(temp, vista, _auxiliares).assign(Vista="Cartera seleccionada")
    else: 
        Cartera = kpi_task(temp, vista, _auxiliares).rename(columns={vista: "Vista"})



    
    if kpi in ("dinero", "cuentas"):

        to_plot = pd.concat([Cartera])

        fig1 = px.line(to_plot
                        , x="Fecha_reporte"
                        , y="Metric"
                        , color="Vista"
                       )

        if kpi in ("dinero"):
            fig1.layout.yaxis.tickformat = '$,'
        else:
            fig1.layout.yaxis.tickformat = ','
        if vista == "genero_estimado":
            fig1["data"][1]["line"]["color"] = "purple"
            fig1["data"][0]["line"]["color"] = "green"
            fig1["data"][2]["line"]["color"] = "pink"
    else:
        if Promedio_comparar == "Promedio YoFio":
            Promedio = kpi_task(YoFio, "", _auxiliares).assign(Vista="Promedio YoFio")
        else:
            Promedio = (
                kpi_task(
                    YoFio
                    .merge(
                        temp[["ID_Credito"]]
                        .drop_duplicates()
                        , how="left"
                        , indicator=True
                    )
                    .query(
                        "_merge == 'left_only'"
                    )
                    , ""
                    , _auxiliares
                )
                .assign(
                    Vista="Promedio YoFio sin cartera seleccionada"
                )
                .sort_values(
                    by="Fecha_reporte"
                    , ignore_index=True
                )
            )
        to_plot = pd.concat([Promedio, Cartera])

        if kpi_selected == 'Pérdida esperada' and _cortes in ("Mensual", "Por mes"):
            # Calculate the moving average with a window size equal to 6 periods
            Promedio_ma = (Promedio
                           .assign(Metric = lambda df: df.Metric.rolling(window=6).mean()
                                    , Vista = "Promedio YoFio (MA)"
                                   )
                           .dropna()
                           .sort_values(by="Fecha_reporte", ignore_index=True)
                           )
            to_plot = pd.concat([to_plot, Promedio_ma])

        

        fig1 = px.line(to_plot
                        , x="Fecha_reporte"
                        , y="Metric"
                        , color="Vista"
                       )
        fig1["data"][0]["line"]["color"] = "black"
        if kpi_selected == 'Pérdida esperada' and _cortes in ("Mensual", "Por mes"):
            fig1["data"][2]["line"]["dash"] = "dash"
        if vista == "genero_estimado":
            fig1["data"][2]["line"]["color"] = "red"
            
        # Fill between 18% and 22% of the y-axis
        if kpi_selected == 'Pérdida esperada' and _cortes in ("Mensual", "Por mes"):
            fig1.update_layout(
                shapes=[
                    dict(
                        type= 'rect', 
                        xref= 'paper', 
                        yref= 'y', 
                        x0= 0, 
                        y0= 0.18, 
                        x1= 1, 
                        y1= 0.22,
                        fillcolor= 'LightSalmon',
                        opacity= 0.3,
                        layer= 'below', 
                        line_width= 0
                    )
                ]
            )
            # Set a legend for the fill between trace named "Apetito de riesgo"
            fig1.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color='LightSalmon', opacity=0.3),
                showlegend=True,
                name=r"Apetito de riesgo 18% - 22%",
                hoverinfo='none'
            ))



        fig1.layout.yaxis.tickformat = ',.2%'
        
    
    fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke')
    fig1.update_layout(
        xaxis_title="Fecha reporte"
        , yaxis_title=kpi_selected
    )


    csv_metricas = convert_df(to_plot
                              .filter(["Vista", "Fecha_reporte", "Metric"])
                              .sort_values(by=["Vista", "Fecha_reporte"], ignore_index=True)
                              )

    col5.download_button(
        label="Descargar CSV",
        data=csv_metricas,
        file_name='Metricas.csv',
        mime='text/csv',
    )
    st.markdown("**Definición métrica:** "+kpi_des)
    zoom = st.checkbox("¿Hacer zoom a la gráfica?")
    if zoom and not (kpi in ("dinero", "cuentas")):
        fig1.update_yaxes(range=[0, 1])

    st.plotly_chart(fig1
                    , use_container_width=True
                    , height = 450
                    , theme="streamlit"
                    )
    # if "erick" in os.getcwd():
    #     st.write("Nota: Esto solo se verá si estás en local de Erick")
    #     st.dataframe(to_plot
    #                  .query("Fecha_reporte.isin(['2023-08-31', '2023-09-30']) and Vista != 'Promedio YoFio'")
    #                  .filter(["Vista", "Fecha_reporte", "Metric"])
    #                  .sort_values(by=["Vista", "Fecha_reporte"], ignore_index=True)
    #                  , width=500
    #                 )
    del fig1, Cartera, to_plot, csv_metricas, formateada, vista, kpi_des, zoom
    try:
        del Promedio
    except:
        pass










