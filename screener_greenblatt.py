# maximize CFO/Asset/PB

import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, getFromDFYearly

COUNT = 0



def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'
yearly=False

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_greenblatt', 'w')

stock_df = pd.read_csv('list_US_companyInfo', sep=" ", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listingDate'])
stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['listingDate'] < pd.to_datetime('2020-1-1'))
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        cf = si.get_cash_flow(comp, yearly=False)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearly)
        if cfo < 0:
            print(comp, "cfo < 0")
            continue

        bs = si.get_balance_sheet(comp, yearly=False)
        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])

        if totalAssets < totalLiab:
            print(comp, "total A less than total L")
            continue

        shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares

        goodWill = getFromDF(bs.loc['goodWill']) if 'goodWill' in bs.index else 0.0
        intangibles = getFromDF(bs.loc['intangibleAssets']) if 'intangibleAssets' in bs.index else 0.0
        equity = totalAssets - totalLiab - goodWill - intangibles

        pb = marketCap / (equity / exRate)
        cfoAssetRatio = cfo / totalAssets

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurr + bsCurr \
                       + " cfoAssetRatio:" + str(round(cfoAssetRatio * 100, 2)) \
                       + " PB:" + str(round(pb, 1)) \
                       + " cfoAsset/PB:" + str(round(cfoAssetRatio * 100 / pb, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        raise Exception(comp, "raising exceptiona again", e)
