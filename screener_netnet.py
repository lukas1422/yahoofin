import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_netnet', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks), listStocks)

listStocks = ['apwc']

for comp in listStocks:
    print(increment())
    try:
        marketPrice = si.get_live_price(comp)

        bs = si.get_balance_sheet(comp)
        currentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])

        cash = getFromDF(bs.loc['cash'])
        receivables = getFromDF(bs.loc['netReceivables'])
        inventory = getFromDF(bs.loc['inventory'])

        shares = si.get_quote_data(comp)['sharesOutstanding']
        marketCap = marketPrice * shares

        # equity = getFromDF(bs.loc["totalStockholderEquity"])
        bsCurr = getBalanceSheetCurrency(comp)
        listingCurr = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if currentAssets < totalLiab:
            print(comp, 'current assets < total liab',
                  round(currentAssets / 1000000000, 2), round(totalLiab / 1000000000, 2))
            continue

        if (cash - totalLiab) / exRate > marketCap:
            outputString = "cash netnet:" + comp \
                           + listingCurr + bsCurr \
                           + " cash:" + str(round(cash / 1000000000, 2)) \
                           + " L:" + str(round(totalLiab / 1000000000, 2))

        elif (cash + receivables * 0.8 - totalLiab) / exRate > marketCap:
            outputString = "cash receivable netnet:" + comp \
                           + listingCurr + bsCurr \
                           + " cash:" + str(round(cash / 1000000000, 2)) \
                           + " rec:" + str(round(receivables / 1000000000, 2)) \
                           + " L:" + str(round(totalLiab / 1000000000, 2))

        elif (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate > marketCap:
            outputString = "cash rec inv netnet " + comp \
                           + listingCurr + bsCurr \
                           + " cash:" + str(round(cash / 1000000000, 2)) \
                           + " rec:" + str(round(receivables / 1000000000, 2)) \
                           + " inv:" + str(round(inventory / 1000000000, 2)) \
                           + " L:" + str(round(totalLiab / 1000000000, 2))

        elif (currentAssets - totalLiab) / exRate > marketCap:
            outputString = 'currentAsset netnet ' + comp \
                           + listingCurr + bsCurr \
                           + " CA:" + str(round(currentAssets / 1000000000, 2)) \
                           + " totalLiab" + str(round(totalLiab / 1000000000, 2))
        else:
            outputString = 'undefined net net, check' + comp

        print(outputString + " mv:" + str(marketCap))
        fileOutput.write(outputString + "mv:" + str(marketCap) + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
