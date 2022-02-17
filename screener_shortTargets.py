# identify short targets
# retained earnings < 0
# CFO < 0
# D/E > 1
# search for companies with a lot of debt, little cash, going bankrupt,
# fragile to crashes

import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_shortTargets', 'w')

# ## US
# stock_df = pd.read_csv('list_UScompanyInfo', sep=" ", index_col=False,
#                        names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listingDate'])
#
# stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])
#
# listStocks = stock_df[stock_df['industry'].str
#                           .contains('fund|shell', regex=True, case=False) == False]['ticker'].tolist()
# ## US

# HK version STARTS
stock_df = pd.read_csv('list_hkstocks', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
hk_shares = pd.read_csv('list_hk_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()
# listStocks = ['1513.HK']
# HK Version ENDS

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:

        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, " market price < 1 ", marketPrice)
            continue

        bs = si.get_balance_sheet(comp, yearly=False)
        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0.0

        if retainedEarnings > 0:
            print(comp, " retained earnings > 0 ", retainedEarnings)
            continue

        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"]) if 'totalCurrentAssets' in bs.index else 0.0
        totalCurrentLiab = getFromDF(
            bs.loc["totalCurrentLiabilities"]) if 'totalCurrentLiabilities' in bs.index else 0.0
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio > 1:
            print(comp, "current ratio > 1", currentRatio)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        if debtEquityRatio < 1:
            print(comp, " de ratio < 1. ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=False)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if ebit > 0 or netIncome > 0:
            print(comp, "ebit or net income > 0 ", ebit, " ", netIncome)
            continue

        cf = si.get_cash_flow(comp)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"]) \
            if 'totalCashFromOperatingActivities' in cf.index else 0.0

        if cfo > 0:
            print(comp, "cfo > 0 ", cfo)
            continue

        # equity = getFromDF(bs.loc["totalStockholderEquity"])
        equity = totalAssets - totalLiab
        # shares = si.get_quote_data(comp)['sharesOutstanding']
        shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)

        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)

        if pb < 1:
            print(comp, "pb < 1", pb)
            continue

        revenue = getFromDF(incomeStatement.loc["totalRevenue"])

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        percentile = 100.0 * (marketPrice - data['low'].min()) / (data['high'].max() - data['low'].min())
        divSum = divs['dividend'].sum() if not divs.empty else 0

        info = si.get_company_info(comp)
        country = info.loc['country'][0] if 'country' in info.index else ""
        sector = info.loc['sector'][0] if 'sector' in info.index else ""

        # + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
        #     .to_string(index=False, header=False) + " " \

        outputString = comp + " " + \
                       + info.loc["country"][0].replace(" ", "_") + " " \
                       + info.loc['sector'][0].replace(" ", "_") \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Eq:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                       + " CR:" + str(round(currentRatio, 1)) \
                       + " RE/A:" + str(round(retainedEarnings / totalAssets, 2)) \
                       + " EBIT/A:" + str(round(ebit / totalAssets, 2)) \
                       + " CFO/A" + str(round(cfo / totalAssets, 2)) \
                       + " NCA/A:" + str(round((totalCurrentAssets - totalCurrentLiab) / totalAssets, 2)) \
                       + " E/D:" + str(round((totalAssets - totalLiab) / totalAssets, 2)) \
                       + " S/A:" + str(round(revenue / totalAssets, 2)) \
                       + " pb:" + str(round(pb, 2)) \
                       + " 52w p%:" + str(round(percentile)) \
                       + " div10yr:" + str(round(divSum / marketPrice, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
