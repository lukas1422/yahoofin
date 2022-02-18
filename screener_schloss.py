# schloss method
# no financials,
# PB < 1
# no long term debt
# price < 1.1 * 52 week low
# insider  ownership > median

import yahoo_fin.stock_info as si
import pandas as pd

from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK
from helperMethods import getInsiderOwnership
from datetime import datetime, timedelta

COUNT = 0
MARKET = Market.HK


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# START_DATE = '3/1/2020'
START_DATE = (datetime.today() - timedelta(weeks=52)).strftime('%-m/%-d/%Y')
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_schlossOutput', 'w')

ownershipDic = getInsiderOwnership()

if MARKET == Market.US:
    stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_hkstocks', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    hk_shares = pd.read_csv('list_hk_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
    listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()
    # listStocks = ['1513.HK']
else:
    raise Exception("market not found")

for comp in listStocks:
    print(increment())
    try:

        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        if MARKET == Market.US:
            insiderPerc = ownershipDic[comp]
            if insiderPerc < 10:
                print(comp, "insider ownership < 10%", insiderPerc)
                continue
        else:
            insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
            print(comp, "insider percent", insiderPerc)

        if insiderPerc < 10:
            print(comp, "insider percentage < 10 ", insiderPerc)
            continue

        bs = si.get_balance_sheet(comp)
        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        currentLiab = getFromDF(bs.loc['totalCurrentLiabilities'])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        longTermDebtRatio = (totalLiab - currentLiab) / totalAssets

        if debtEquityRatio > 1 or totalAssets < totalLiab:
            print(comp, " de ratio> 1 or A<L. ", debtEquityRatio)
            continue

        equity = getFromDF(bs.loc["totalStockholderEquity"])

        if equity < 0:
            print(comp, "equity < 0", equity)

        shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)

        if pb < 0 or pb > 1:
            print(comp, ' pb < 0 or pb > 1. mv equity exrate', pb, marketCap, equity, exRate)
            continue

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        low_52wk = data['low'].min()

        if marketPrice > low_52wk * 1.1:
            print(comp, "exceeding 52wk low * 1.1, P/Low ratio:", marketPrice, low_52wk,
                  round(marketPrice / low_52wk, 2))
            continue

        # insiderPercOutput = str(round(insiderPerc, 1)) if MARKET == Market.US else "non data"

        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]

        if sector == 'Real Estate':
            print(comp, " no real estate ")
            continue

        outputString = comp + " " + listingCurrency + bsCurrency + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Eq:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                       + " pb:" + str(round(pb, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " LT_debt_ratio:" + str(round(longTermDebtRatio, 1)) \
                       + " insider%:" + str(insiderPerc) \
                       + " p/52low: " + str(round(marketPrice / low_52wk))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
