import math
import pandas as pd


def getFromDF(df):
    if df.empty:
        return 0
    elif math.isnan(df[0]):
        return df[1]
    return df[0]


def getInsiderOwnership():
    ownership = pd.read_csv('list_insiderOwnership_finviz', sep=' ', index_col=False, names=['ticker', 'perc'])
    ownership['perc'] = ownership['perc'].replace('-', '0')
    ownership['perc'] = ownership['perc'].str.rstrip("%").astype(float)
    return pd.Series(ownership.perc.values, index=ownership.ticker).to_dict()
