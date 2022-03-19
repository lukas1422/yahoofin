import math
from datetime import timedelta

import pandas as pd


def getFromDF(df, attribute):
    # print(df, attribute)
    if isinstance(df, str):
        return ''

    if df.empty:
        return 0
    if attribute not in df.index:
        return 0
    return df.loc[attribute].dropna()[0]
    # elif math.isnan(df[0]):
    #     if math.isnan(df[1]):
    #         return 0
    #         # raise ValueError("no value")
    #     else:
    #         return df[1]
    # return df[0]


def roundB(num, decPlace):
    return round(num / 1000000000, decPlace)


def getFromDFYearly(df, attribute, yearly):
    if not isinstance(df, pd.DataFrame):
        return ""

    if df.empty:
        return 0
    if attribute not in df.index:
        return 0
    if yearly:
        return df.loc[attribute].dropna()[0]
    else:
        colsToSum = sum(df.columns > df.columns[0] - timedelta(weeks=51))
        # print(df.columns, df.columns[0] - timedelta(weeks=51))
        # print("cols to sum ", colsToSum)
        #print("DF: latest*4", df.loc[attribute].dropna()[0] * colsToSum, "sum4", df.loc[attribute][:colsToSum].sum())
        return min(df.loc[attribute].dropna()[0] * colsToSum, df.loc[attribute][:colsToSum].sum())


def getInsiderOwnership():
    ownership = pd.read_csv('list_insiderOwnership_finviz', sep=' ', index_col=False, names=['ticker', 'perc'])
    ownership['perc'] = ownership['perc'].replace('-', '0')
    ownership['perc'] = ownership['perc'].str.rstrip("%").astype(float)
    return pd.Series(ownership.perc.values, index=ownership.ticker).to_dict()


def convertHK(ticker):
    if ticker.endswith('HK'):
        return ticker

    if ticker.startswith('0'):
        return ticker[1:] + '.HK'
    return ticker + '.HK'


def boolToString(bool, string):
    return " " + string + "!" if bool else ""

def chinaTickerToYahoo(nameInstring):
    if nameInstring.startswith('6'):
        return nameInstring + '.SS'
    else:
        return nameInstring + '.SZ'

# import inspect

# random = True
# random1 = True
# print(boolToString(random1, ""))

#
# def myfunc(model, arg_is_list, num):
#     print('Your passed args are:')
#     arg_names = inspect.getfullargspec(myfunc).args
#     # print(repr(locals()[arg_names[1]]))
#     for name in arg_names:
#         print(repr(locals()[name]))
#
#
# myfunc(model='the model', arg_is_list='arrrggg', num=42)
