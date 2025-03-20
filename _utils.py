import pandas as pd
import streamlit as st
from datetime import datetime, timedelta


def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

def diff_month(d1, d2):
    # d1 sea la fecha mayor y d2 la fecha menor
    if isinstance(d1, str):
        d1 = datetime.fromisoformat(d1)
    if isinstance(d2, str):
        d2 = datetime.fromisoformat(d2)
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def prod(iterable):
    _p = 1
    for i in iterable:
        _p = _p * i
    return _p
#
# Funciones generales
#
def clean_roll(Roll, cortes):
    if Roll == "Roll[0 to 1]":
        return "01. Roll[0 to 1]"
    if Roll == "Roll[1 to 2]":
        return "02. Roll[1 to 2]"
    if Roll == "Roll[2 to 3]":
        return "03. Roll[2 to 3]"
    if Roll == "Roll[3 to 4]":
        return "04. Roll[3 to 4]"
    if Roll == "Roll[4 to WO]":
        return "05. Roll[4 to WO]"
    if Roll == "Roll[0 to WO]" and cortes in ('Mensual', 'Todos'):
        return "06. Roll[0 to WO]"
    if Roll == "Roll anualizado" and cortes in ('Mensual', 'Todos'):
        return "07. Roll anualizado"
    if Roll == "Pérdida" and cortes in ('Mensual', 'Todos'):
        return "08. Pérdida"
    if Roll == "Pérdida (sin WO)" and cortes in ('Mensual', 'Todos'):
        return "09. Pérdida (sin WO)"
    if Roll == "Roll[4 to 5]":
        return "05. Roll[4 to 5]"
    if Roll == "Roll[5 to 6]":
        return "06. Roll[5 to 6]"
    if Roll == "Roll[6 to 7]":
        return "07. Roll[6 to 7]"
    if Roll == "Roll[7 to 8]":
        return "08. Roll[7 to 8]"
    if Roll == "Roll[8 to WO]":
        return "09. Roll[8 to WO]"
    if Roll == "Roll[0 to WO]" and cortes in ('Catorcenal', 'Quincena comercial'):
        return "10. Roll[0 to WO]"
    if Roll == "Roll anualizado" and cortes in ('Catorcenal', 'Quincena comercial'):
        return "11. Roll anualizado"
    if Roll == "Pérdida" and cortes in ('Catorcenal', 'Quincena comercial'):
        return "12. Pérdida"
    if Roll == "Roll[8 to 9]":
        return "09. Roll[8 to 9]"
    if Roll == "Roll[9 to 10]":
        return "10. Roll[9 to 10]"
    if Roll == "Roll[10 to 11]":
        return "11. Roll[10 to 11]"
    if Roll == "Roll[11 to 12]":
        return "12. Roll[11 to 12]"
    if Roll == "Roll[12 to 13]":
        return "13. Roll[12 to 13]"
    if Roll == "Roll[13 to 14]":
        return "14. Roll[13 to 14]"
    if Roll == "Roll[14 to 15]":
        return "15. Roll[14 to 15]"
    if Roll == "Roll[15 to 16]":
        return "16. Roll[15 to 16]"
    if Roll == "Roll[16 to 17]":
        return "17. Roll[16 to 17]"
    if Roll == "Roll[17 to WO]":
        return "18. Roll[17 to WO]"
    if Roll == "Roll[0 to WO]" and cortes == 'Semanal':
        return "19. Roll[0 to WO]"
    if Roll == "Roll anualizado" and cortes == 'Semanal':
        return "20. Roll anualizado"
    if Roll == "Pérdida" and cortes == 'Semanal':
        return "21. Pérdida"

def format_column(df, column, cat_auxiliar=None):
    flag = False
    if column == "Edad": 
        df["Edad_formato"] = (df["Edad"]
                            .apply(lambda x: "De %i a %i" % (int(x//5)*5, int(x//5)*5+4))
                            .replace({"De 60 a 64": "Mayor de 60"
                                      , "De 65 a 69": "Mayor de 60"
                                      , "De 70 a 74": "Mayor de 60"
                                      , "De 75 a 79": "Mayor de 60"
                                      , "De 80 a 84": "Mayor de 60"
                                      , "De 20 a 24": "De 20 a 29"
                                      , "De 25 a 29": "De 20 a 29"
                                      }))
        flag = True
    elif column == "genero_estimado":
        factor_dict = {"Todos": "Todos", "Hombre": "H", "Mujer": "M", "Vacio": "?"}
        factor_dict = {value:key for (key, value) in factor_dict.items()}
        df["genero_estimado_formato"] = df["genero_estimado"].apply(lambda x: factor_dict[x])
        flag = True
    elif column == "term_type":
        factor_dict = {"Todos": "Todos", "W": "Semanal", "B": "Catorcenal", "M": "Mensual"}
        df["term_type_formato"] = df["term_type"].apply(lambda x: factor_dict[x])
        flag = True
    elif column == "Municipio":
        # st.session_state["cat_municipios"]
        df = df.merge(cat_auxiliar
                      .assign(Municipio_formato = (st.session_state["cat_municipios"]["Estado"].replace({'E': 'Edo Mex', 'C': 'CDMX', 'H': 'Hgo', 'P': 'Pue', 'J': 'Jal', 'T': 'Tlaxcala'})
                                                   + ", " + st.session_state["cat_municipios"]["Municipio"])
                            )
                      .filter(["CP", "Municipio_formato"])
                      .drop_duplicates()
                      , how="left"
                      , on="CP"
                     )
        flag = True
    elif column == "Estado":
        # st.session_state["cat_municipios"]
        df = df.merge(cat_auxiliar
                      .filter(["CP", "Estado"])
                      .drop_duplicates()
                      .rename(columns={"Estado": "Estado_formato"})
                      , how="left"
                      , on="CP"
                    )
        df["Estado_formato"] = df["Estado_formato"].replace({'E': 'Edo Mex', 'C': 'CDMX', 'H': 'Hgo', 'P': 'Pue', 'J': 'Jal', 'T': 'Tlaxcala'})
        flag = True
    elif column == "industry":
        # st.session_state["cat_industry"]
        df = df.merge(cat_auxiliar
                      .filter(["industry", "industry_cve"])
                      .drop_duplicates()
                      .rename(columns={"industry": "industry_formato"})
                      , how="left"
                      , on="industry_cve"
                     )
        flag = True
    elif column == "Analista":
        # st.session_state["cat_advisors"]
        df = df.merge(cat_auxiliar
                        .filter(["Analista", "Cartera_YoFio"])
                        .drop_duplicates()
                        .rename(columns={"Analista": "Analista_formato"})
                        , how="left"
                        , on="Cartera_YoFio"
                         )
        flag = True
    elif column == 'ZONA':
        # st.session_state["cat_advisors"]
        df = df.merge(cat_auxiliar
                        .filter(["ZONA", "Cartera_YoFio"])
                        .drop_duplicates()
                        .rename(columns={"ZONA": "ZONA_formato"})
                        , how="left"
                        , on="Cartera_YoFio"
                         )
        flag = True
    elif column == 'n_ampliaciones':
        df = df.assign(n_ampliaciones_formato = df["n_ampliaciones"].apply(lambda x: "%i" % x if x < 4 else "4+"))
        flag = True


    return flag, df


def get_date(i):
    return str(datetime.fromisoformat("2023-01-01")+timedelta(days=7*i))[:10]

def Bucket_Monthly(x):
    if x <= 0 :
        return '0. Bucket_Current'
    elif x >= 1 and x < 30 :
        return '1. Bucket_1_29'
    elif x >= 30 and x < 60 :
        return '2. Bucket_30_59'
    elif x >= 60 and x < 90 :
        return '3. Bucket_60_89'
    elif x >= 90 and x < 120 :
        return '4. Bucket_90_119'
    elif x >= 120 :
        return '5. Bucket_120_more'

def Bucket_Weekly(x):
    if x < 1 :
        return '0. Bucket_Current'
    elif x >= 1 and x <= 7 :
        return '01. Bucket_1_7'
    elif x >= 8 and x <= 14 :
        return '02. Bucket_8_14'
    elif x >= 15 and x <= 21 :
        return '03. Bucket_15_21'
    elif x >= 22 and x <= 28 :
        return '04. Bucket_22_28'
    elif x >= 29 and x <= 35 :
        return '05. Bucket_29_35'
    elif x >= 36 and x <= 42 :
        return '06. Bucket_36_42'
    elif x >= 43 and x <= 49 :
        return '07. Bucket_43_49'
    elif x >= 50 and x <= 56 :
        return '08. Bucket_50_56'
    elif x >= 57 and x <= 63 :
        return '09. Bucket_57_63'
    elif x >= 64 and x <= 70 :
        return '10. Bucket_64_70'
    elif x >= 71 and x <= 77 :
        return '11. Bucket_71_77'
    elif x >= 78 and x <= 84 :
        return '12. Bucket_78_84'
    elif x >= 85 and x <= 91 :
        return '13. Bucket_85_91'
    elif x >= 92 and x <= 98 :
        return '14. Bucket_92_98'
    elif x >= 99 and x <= 105 :
        return '15. Bucket_99_105'
    elif x >= 106 and x <= 112 :
        return '16. Bucket_106_112'
    elif x >= 113 and x <= 119 :
        return '17. Bucket_113_119'
    elif x >= 120 :
        return '18. Bucket_120_more'
    
def Bucket_Biweekly(x):
    if x < 1 :
        return '0. Bucket_Current'
    elif x >= 1 and x <= 15 :
        return '01. Bucket_1_15'
    elif x >= 16 and x <= 30 :
        return '02. Bucket_16_30'
    elif x >= 31 and x <= 45 :
        return '03. Bucket_31_45'
    elif x >= 46 and x <= 60 :
        return '04. Bucket_46_60'
    elif x >= 61 and x <= 75 :
        return '05. Bucket_61_75'
    elif x >= 76 and x <= 90 :
        return '06. Bucket_76_90'
    elif x >= 91 and x <= 105 :
        return '07. Bucket_91_105'
    elif x >= 106 and x <= 119 :
        return '08. Bucket_106_119'
    elif x >= 120 :
        return '09. Bucket_120_more'

def inferior(Bucket):
    if "Current" in Bucket:
        x = 0
    elif "delta" in Bucket:
        x = 120
    else:
        x = int(Bucket.split("_")[1])
    return x    

def Roll_t(i, j, mes, term_type, dataframe, meses, cortes, flag=False):
    t = meses.index(mes)
    N = {"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 14}[cortes]
    N = min(t, N)
    
    Num = [meses[t-i] for i in range(N)]
    Den = [meses[t-i-1] for i in range(N)]
    if t-1 >= 0:
        
        n = dataframe[Num].loc[j].sum() #numerador
        d = dataframe[Den].loc[i].sum() #denominador
        
        return n/(d+int(d == 0))
    else:
        return None


def rango_lim_credito(x):
    if x <= 5000:
        return "0. Menor a $5000"
    elif x <= 15000:
        return "1. Entre $5001 y $15,0000"
    elif x <= 30000:
        return "2. Entre $15,001 y $30,0000"
    elif x <= 45000:
        return "3. Entre $30,001 y $45,0000"
    else:
        return "4. Mayor de $45,001"