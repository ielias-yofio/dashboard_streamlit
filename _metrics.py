import pandas as pd
import streamlit as st
from datetime import datetime, timedelta


def roi_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)
    return (dataframe
            .assign(roi = dataframe["ingreso_cumulative"]-dataframe["total_amount_disbursed_cumulative"])
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("roi", "sum"))
            .reset_index()
            .filter(_to_group + ["Metric"])
           )

def roi_ratio_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)
    return (dataframe
            .groupby(_to_group)
            .agg(ingreso = pd.NamedAgg("ingreso_cumulative", "sum")
                 , desembolso = pd.NamedAgg("total_amount_disbursed_cumulative", "sum")
                )
            .assign(Metric = lambda df: df["ingreso"] / df["desembolso"])
            .reset_index()
            .filter(_to_group + ["Metric"])
           )

def roi_interes_ratio_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)

    return (dataframe
            .groupby(_to_group)
            .agg(ingreso = pd.NamedAgg("interes_cumulative", "sum")
                 , desembolso = pd.NamedAgg("total_amount_disbursed_cumulative", "sum")
                )
            .assign(Metric = lambda df: df["ingreso"] / df["desembolso"])
            .reset_index()
            .filter(_to_group + ["Metric"])
           )


def Default_rate_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)
    return (dataframe
            .assign(OS120 = (dataframe["Dias_de_atraso"]>=120).astype(int) * dataframe["balance"]
                    , balance = dataframe["balance"]
                    , antiguedad = (pd.to_datetime(dataframe["Fecha_reporte"]) - pd.to_datetime(dataframe["Fecha_apertura"])).dt.days/30
                    , N_OS120 = (dataframe["Dias_de_atraso"]>=120).astype(int)
                    , N_balance = (dataframe["Dias_de_atraso"]<120).astype(int)
                   )
            .groupby(_to_group)
            .agg({"OS120": "sum", "balance": "sum", "N_OS120": "sum", "N_balance": "sum", "antiguedad": "mean"})
            .reset_index()
            # .assign(Metric = lambda df: 12 * (df["OS120"] / df["balance"] ) / df["antiguedad"])
            .assign(Metric = lambda _df: _df["OS120"] / _df["balance"]  )
            .filter(_to_group + ["Metric"])

           )

def lim_credito_avg_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    return (dataframe
            .query("Status_credito != 'I'")
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("Monto_credito", "mean"))
            .reset_index()
            .filter(_to_group + ["Metric"])
           )

def current_pct_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(Current = dataframe["Bucket"].str.contains('Current') * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"Current": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["Current"] / (df["balance"] + (df["balance"] == 0).astype(int)))
            .filter(_to_group + ["Metric"])
           )


def current_sin_ip_pct_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(Current = dataframe["Bucket"].str.contains('Current') * dataframe["balance_sin_ip"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"Current": "sum", "balance_sin_ip": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["Current"] / (df["balance_sin_ip"] + (df["balance_sin_ip"] == 0).astype(int)))
            .filter(_to_group + ["Metric"])

           )

def total_amount_disbursed_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    return (dataframe
            .groupby(_to_group, as_index=False)
            .agg(Metric = pd.NamedAgg("total_amount_disbursed_cumulative", "sum"))
            .filter(_to_group + ["Metric"])
            )

def os_8_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)
    return (dataframe
            .assign(OS8 = (dataframe["Dias_de_atraso"]>=8).astype(int) * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"OS8": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["OS8"] / df["balance"])
            .filter(_to_group + ["Metric"])

           )

def os_30_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)

    return (dataframe
            .assign(OS30 = (dataframe["Dias_de_atraso"]>=30).astype(int) * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"OS30": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["OS30"] / df["balance"])
            .filter(_to_group + ["Metric"])
           )

def os_30_task_con_WO(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if vista == "Mes":
        _to_group.pop(0)

    return (dataframe
            .assign(OS30 = (dataframe["Dias_de_atraso"]>=30).astype(int) * dataframe["balance"])
            .groupby(_to_group)
            .agg({"OS30": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["OS30"] / df["balance"])
            .filter(_to_group + ["Metric"])

           )

def os_60_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(OS60 = (dataframe["Dias_de_atraso"]>=60).astype(int) * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"OS60": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["OS60"] / df["balance"])
            .filter(_to_group + ["Metric"])

           )

def os_90_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(OS60 = (dataframe["Dias_de_atraso"]>=90).astype(int) * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg({"OS60": "sum", "balance": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["OS60"] / df["balance"])
            .filter(_to_group + ["Metric"])

           )

def coincidential_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(Coincidential = ((dataframe["Dias_de_atraso"]>=120) & (dataframe["Dias_de_atraso_ant"]<120)).astype(int) * dataframe["balance"]
                , OSTotal = (dataframe["Dias_de_atraso"]<120).astype(int) * dataframe["balance"]
               )
            .groupby(_to_group)
            .agg({"Coincidential": "sum", "OSTotal": "sum"})
            .reset_index()
            .assign(Metric = lambda df: df["Coincidential"] / df["OSTotal"])
            .filter(_to_group + ["Metric"])

           )

def OSTotal_sincastigos_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .query("Dias_de_atraso < 120")
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("balance", "sum"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def OSTotal_concastigos_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("balance", "sum"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def credit_limit(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("Monto_credito", "sum"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def metrica_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    


    _df = (dataframe
            .groupby(_to_group, as_index=False)
            .agg(Metric=pd.NamedAgg("Monto_credito", "sum"))
            .filter(_to_group + ["Metric"])
           )

    return _df 

def lagged_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    _df = (dataframe
            .assign(Coincidential = ((dataframe["Dias_de_atraso"]>=120) & (dataframe["Dias_de_atraso_ant"]<120)).astype(int) * dataframe["balance"])
            .groupby(_to_group)
            .agg({"Coincidential": "sum"})
            .reset_index()
           )
    OS = OSTotal_sincastigos_task(dataframe, vista, auxiliares=[])
    if len(auxiliares) == 0:
        raise ValueError("No se ha especificado el auxiliares.")
    
    # auxiliares[0]:: YoFio dataframe
    _df = (auxiliares[0]
            .sort_values(by="Fecha_reporte", ignore_index=True)
            .merge(_df, how="left")
            .merge(OS, how="left")
            .fillna({"Coincidential": 0, "Metric": 0})
            .assign(OS_t_5 = lambda df: df["Metric"].shift(5).fillna(0))
            .assign(Metric = lambda df: df["Coincidential"] / (df["OS_t_5"]))
            .filter(_to_group + ["Metric"])
            )
    return _df


def SaldoVencido_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .query("Status_credito=='L'") # LATE
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("balance", "sum"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def imora_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    _x =  (dataframe
            .assign(balance_limpio = dataframe["balance"] * (dataframe["Dias_de_atraso"]<120).astype(int)
                    , delta = dataframe["balance"] * ((dataframe["Dias_de_atraso"]>=120) & (dataframe["Dias_de_atraso_ant"]<120)).astype(int)
                   )
            .groupby(_to_group, as_index=False)
            .agg(balance_limpio = pd.NamedAgg("balance_limpio", "sum")
                 , delta = pd.NamedAgg("delta", "sum")
                 )
            # Sumar últimos 12 deltas por cada Fecha_reporte
            .sort_values(by=_to_group[::-1], ignore_index=True)
            .assign(dummies = 1)
            )
    _vista = vista if vista != "" else "dummies"
            
    return (_x
            .assign(delta_12m = lambda df: df.groupby(_vista)["delta"].rolling(window=12, min_periods=1).sum().reset_index(drop=True))
            .assign(Metric = lambda df: df["delta_12m"] / (df["balance_limpio"] + df["delta_12m"] + (df["balance_limpio"] + df["delta_12m"] == 0).astype(int)))
            .filter(_to_group + ["Metric"])
           )

def delta_pct_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    _x =  (dataframe
            .assign(delta = dataframe["balance"] * ((dataframe["Dias_de_atraso"]>=120) & (dataframe["Dias_de_atraso_ant"]<120)).astype(int)
                    , balance_limpio = dataframe["balance"] * (dataframe["Dias_de_atraso"]<120).astype(int)
                   )
            .groupby(_to_group, as_index=False)
            .agg(delta = pd.NamedAgg("delta", "sum")
                 , balance = pd.NamedAgg("balance_limpio", "sum")
                 )
            .sort_values(by=_to_group[::-1], ignore_index=True)
            .assign(dummies = 1)
            )
    _vista = vista if vista != "" else "dummies"
            
    return (_x
            .assign(delta_12m = lambda df: df.groupby(_vista)["delta"].rolling(window=12, min_periods=1).sum().reset_index(drop=True))
            .assign(Metric = lambda df: 12* df["delta"] / (df["balance"] + df["delta_12m"] + (df["balance"] + df["delta_12m"] == 0).astype(int)))
            .filter(_to_group + ["Metric"])
           )

def NumCuentas_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("ID_Credito", "nunique"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )


def Activas_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .query("Status_credito.isin(['L', 'C'])") # LATE & CURRENT
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("ID_Credito", "nunique"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def Mora_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .query("Status_credito.isin(['L'])") # LATE
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("ID_Credito", "nunique"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def reestructura_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group)
            .agg(Metric = pd.NamedAgg("reestructura", "mean"))
            .reset_index()
            .filter(_to_group + ["Metric"])

           )

def perdida_task(dataframe, vista, auxiliares=[]):
    _df = dataframe.copy()
    if vista == "":
        vista = "P"
        _df[vista] = "P"

    if len(auxiliares) == 0:
        raise ValueError("No se ha especificado el auxiliares.")
    
    No_fechas = list(_df["Fecha_reporte"].unique())
    No_fechas.sort()
    No_fechas = No_fechas[:{"Mensual": 3, "Semanal": 12, "Catorcenal": 6}[auxiliares[0]]]

    saldos = (_df
              .groupby(["Bucket", "Fecha_reporte", vista])
              .agg({"balance": "sum"})
              .reset_index()
             )
    
    _N = auxiliares[1]

    t = pd.concat([saldos
                    .query("Bucket.str.contains('120') == False")
                    , _df
                       .query("Dias_de_atraso >= 120 and Dias_de_atraso_ant < 120")
                       .assign(Bucket = "%s. delta" % str(_N+1).zfill(2 - int(_N+1 < 10)))
                       .groupby(["Bucket", "Fecha_reporte", vista])
                       .agg(balance = pd.NamedAgg("balance", "sum"))
                       .reset_index()])

    t = (t[[vista]]
         .drop_duplicates()
         .assign(f=1)
         .merge(t[["Bucket"]]
                .drop_duplicates()
                .assign(f=1))
         .merge(t[["Fecha_reporte"]]
                .drop_duplicates()
                .assign(f=1))
         .drop(columns=["f"])
         .merge(t
                , how="left"
               )
         .fillna({"balance":0})
         .assign(N_Bucket = lambda df: df.Bucket.apply(lambda x: int(x.split(".")[0])))
         .sort_values(by=[vista, "Bucket", "Fecha_reporte"], ignore_index=True)
        )
    _N = {"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 6}[auxiliares[0]]
    t["Num"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N+1, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t["Den"] - t["balance"]

    t = (t
         .drop(columns=["balance", "Num", "Bucket"])
         .merge(t
                .drop(columns=["balance", "Den", "Bucket"])
                .assign(N_Bucket = t["N_Bucket"]-1)
                , on=[vista, "Fecha_reporte", "N_Bucket"]
               )
         .query("not Fecha_reporte.isin(%s)" % str(No_fechas))
        )

    t["Roll"] = t["Num"] / (t["Den"] + (t["Den"]==0).astype(int))

    _N = {"Mensual": 12, "Semanal": 4.5 * 12, "Todos": 12, "Catorcenal": 4.5 * 6, "Quincena comercial": 4.5 * 6}[auxiliares[0]]

    def prod(iterable):
        _p = 1
        for i in iterable:
            _p = _p * i
        return _p
    
    t = (t
         .groupby(["Fecha_reporte", vista])
         .agg({"Roll": prod})
         .reset_index()
         .assign(Anualizado = lambda df: df["Roll"]* _N)
         .merge(saldos
                .query("Bucket.str.contains('Current')")
                .drop(columns=["Bucket"])
                .rename(columns={"balance": "Current"})
                , how="left"
               )
         .merge(saldos
                .groupby(["Fecha_reporte", vista])
                .agg(OS_Total = pd.NamedAgg("balance", "sum"))
                .reset_index()
                , how="left"
               )
         .assign(Metric = lambda df: df["Anualizado"]*df["Current"] / (df["OS_Total"])) # Pérdida esperada
        )
    return (t
            .filter(["Fecha_reporte", vista, "Metric"])
            )

def perdida_hasta_120_task(dataframe, vista, auxiliares=[]):
    _df = dataframe.copy()
    if vista == "":
        vista = "P"
        _df[vista] = "P"
    else:
        pass

    if len(auxiliares) == 0:
        raise ValueError("No se ha especificado el auxiliares.")

    No_fechas = list(_df["Fecha_reporte"].unique())
    No_fechas.sort()
    No_fechas = No_fechas[:{"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 6}[auxiliares[0]]]

    saldos = (_df
              .groupby(["Bucket", "Fecha_reporte", vista])
              .agg({"balance": "sum"})
              .reset_index()
             )
    
    _N = auxiliares[1]
    _df = (_df
            .query("Dias_de_atraso >= 120 and Dias_de_atraso_ant < 120")
            .assign(Bucket = "%s. delta" % str(_N+1).zfill(2 - int(_N+1 < 10)))
            .groupby(["Bucket", "Fecha_reporte", vista])
            .agg(balance = pd.NamedAgg("balance", "sum"))
            .reset_index()
            )
    t = pd.concat([saldos.query("Bucket.str.contains('120') == False"), _df])
    t = (t[[vista]]
         .drop_duplicates()
         .assign(f=1)
         .merge(t[["Bucket"]]
                .drop_duplicates()
                .assign(f=1))
         .merge(t[["Fecha_reporte"]]
                .drop_duplicates()
                .assign(f=1))
         .drop(columns=["f"])
         .merge(t
                , how="left"
               )
         .fillna({"balance":0})
         .assign(N_Bucket = lambda df: df.Bucket.apply(lambda x: int(x.split(".")[0])))
         .sort_values(by=[vista, "Bucket", "Fecha_reporte"], ignore_index=True)
        )
    _N = {"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 6}[auxiliares[0]]
    t["Num"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N+1, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t["Den"] - t["balance"]

    t = (t
         .drop(columns=["balance", "Num", "Bucket"])
         .merge(t
                .drop(columns=["balance", "Den", "Bucket"])
                .assign(N_Bucket = t["N_Bucket"]-1)
                , on=[vista, "Fecha_reporte", "N_Bucket"]
               )
         .query("not Fecha_reporte.isin(%s)" % str(No_fechas))
        )

    t["Roll"] = t["Num"] / (t["Den"] + (t["Den"]==0).astype(int))

    _N = {"Mensual": 12, "Semanal": 4.5 * 12, "Todos": 12, "Catorcenal": 4.5 * 6, "Quincena comercial": 4.5*6}[auxiliares[0]]

    def prod(iterable):
        _p = 1
        for i in iterable:
            _p = _p * i
        return _p
    
    t = (t
         .groupby(["Fecha_reporte", vista])
         .agg({"Roll": prod})
         .reset_index()
         .assign(Anualizado = lambda df: df["Roll"]* _N)
         .merge(saldos
                .query("Bucket.str.contains('Current')")
                .drop(columns=["Bucket"])
                .rename(columns={"balance": "Current"})
                , how="left"
               )
         .merge(saldos
                .query("Bucket.str.contains('120') == False")
                .groupby(["Fecha_reporte", vista])
                .agg(OS_Total = pd.NamedAgg("balance", "sum"))
                .reset_index()
                , how="left"
               )
         .assign(Metric = lambda df: df["Anualizado"]*df["Current"] / (df["OS_Total"])) # Pérdida esperada
        )
    return (t
            .filter(["Fecha_reporte", vista, "Metric"])
            )



def roll_0_1_task(dataframe, vista, auxiliares=[]):
    _df = dataframe.copy()
    if vista == "":
        vista = "P"
        _df[vista] = "P"

    if len(auxiliares) == 0:
        raise ValueError("No se ha especificado el auxiliares.")
    
    No_fechas = list(_df["Fecha_reporte"].unique())
    No_fechas.sort()
    No_fechas = No_fechas[:{"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 6}[auxiliares[0]]]

    saldos = (_df
              .groupby(["Bucket", "Fecha_reporte", vista])
              .agg({"balance": "sum"})
              .reset_index()
             )
    
    _N = auxiliares[1]
    t = (pd.concat([saldos
                    .query("Bucket.str.contains('120') == False")
                    , (_df
                       .query("Dias_de_atraso >= 120 and Dias_de_atraso_ant < 120")
                       .assign(Bucket = "%s. delta" % str(_N+1).zfill(2 - int(_N+1 < 10)))
                       .groupby(["Bucket", "Fecha_reporte", vista])
                       .agg(balance = pd.NamedAgg("balance", "sum"))
                       .reset_index()
                      )
                   ])
        )
    t = (t[[vista]]
         .drop_duplicates()
         .assign(f=1)
         .merge(t[["Bucket"]]
                .drop_duplicates()
                .assign(f=1))
         .merge(t[["Fecha_reporte"]]
                .drop_duplicates()
                .assign(f=1))
         .drop(columns=["f"])
         .merge(t
                , how="left"
               )
         .fillna({"balance":0})
         .assign(N_Bucket = lambda df: df.Bucket.apply(lambda x: int(x.split(".")[0])))
         .sort_values(by=[vista, "Bucket", "Fecha_reporte"], ignore_index=True)
        )
    _N = {"Mensual": 3, "Semanal": 12, "Catorcenal": 6, "Quincena comercial": 6}[auxiliares[0]]
    t["Num"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t.groupby([vista, "Bucket"])['balance'].rolling(window=_N+1, min_periods=1).sum().reset_index(drop=True)
    t["Den"] = t["Den"] - t["balance"]

    t = (t
         .drop(columns=["balance", "Num", "Bucket"])
         .merge(t
                .drop(columns=["balance", "Den", "Bucket"])
                .assign(N_Bucket = t["N_Bucket"]-1)
                , on=[vista, "Fecha_reporte", "N_Bucket"]
               )
         .query("not Fecha_reporte.isin(%s)" % str(No_fechas))
         
        )

    t["Roll"] = t["Num"] / (t["Den"] + (t["Den"]==0).astype(int))

    
    t = (t
         .query("N_Bucket == 0")
         .rename(columns={"Roll": "Metric"})
         .filter(["Fecha_reporte", vista, "Metric"])
        )
    return t.filter(["Fecha_reporte", vista, "Metric"])
            
def os_60_monto_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(Metric = (dataframe["Dias_de_atraso"]>=60).astype(int) * dataframe["balance"])
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group, as_index=False)
            .agg({"Metric": "sum"})
            .filter(_to_group + ["Metric"])
           )

def os_60_cuentas_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]

    return (dataframe
            .assign(Metric = (dataframe["Dias_de_atraso"]>=60).astype(int))
            .query("Bucket.str.contains('120') == False")
            .groupby(_to_group, as_index=False)
            .agg({"Metric": "sum"})
            .filter(_to_group + ["Metric"])
           )

def tiempo_hasta_primera_ampliacion_task(dataframe, vista, auxiliares=[]):
    _to_group = ["Fecha_reporte", vista] if vista != "" else ["Fecha_reporte"]
    if len(auxiliares) == 0:
        raise ValueError("No se ha especificado el auxiliares.")
    
    # Calcular la diferencia entre la fecha de apertura y la fecha de la primera ampliación
    x = (auxiliares[0]
         .query("n_ampliaciones == 1")
         .groupby(["ID_Credito"], as_index=False)
         .agg(Fecha_ampliacion = pd.NamedAgg("Fecha_reporte", "min"))
        )

    _df = (dataframe
            .merge(x, how="inner")
            .assign(Fecha_ampliacion = lambda _df: _df.apply(lambda row: row["Fecha_ampliacion"] if row["Fecha_ampliacion"] <= row["Fecha_reporte"] else pd.NaT, axis=1))
            .query("Fecha_ampliacion.notna()")
            .assign(Dias_hasta_primera_ampliacion = lambda _df: (pd.to_datetime(_df["Fecha_ampliacion"]) - pd.to_datetime(_df["Fecha_apertura"])).dt.days)
            .groupby(_to_group, as_index=False)
            .agg(Metric = pd.NamedAgg("Dias_hasta_primera_ampliacion", "mean"))
            .filter(_to_group + ["Metric"])
           )
    return _df
