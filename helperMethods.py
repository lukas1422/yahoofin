import math


def getFromDF(df):
    if df.empty:
        return 0
    elif math.isnan(df[0]):
        return df[1]
    return df[0]