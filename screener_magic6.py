import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF

finvizDiv = pd.read_csv('list_divYieldFinviz', sep=' ', index_col=False, names=['ticker', 'divi'])
finvizDiv['divi'] = finvizDiv['divi'].replace('-', '0')
finvizDiv['divi'] = finvizDiv['divi'].str.rstrip("%").astype(float)
finvizDic = pd.Series(finvizDiv.divi.values, index=finvizDiv.ticker).to_dict()

xueqiuDiv = pd.read_csv('list_divYieldXueqiu', sep=' ', index_col=False, names=['ticker', 'divi'])
xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('-', '0')
xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('none', '0')
xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('error', '0')
xueqiuDiv['divi'] = xueqiuDiv['divi'].astype(float)
xueqiuDic = pd.Series(xueqiuDiv.divi.values, index=xueqiuDiv.ticker).to_dict()

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_magic6', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        bs = si.get_balance_sheet(comp)

        equity = getFromDF(bs.loc["totalStockholderEquity"])
        shares = si.get_quote_data(comp)['sharesOutstanding']

        incomeStatement = si.get_income_statement(comp, yearly=True)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)
        pe = marketCap / (netIncome / exRate)

        if pb > 0.6:
            print(comp, ' pb > 1', pb)
            continue

        if pe > 6 or pe < 0:
            print(comp, ' pe > 6 or < 0')
            continue

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        # percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
        #         data['adjclose'].max() - data['adjclose'].min())
        divSum = divs['dividend'].sum() if not divs.empty else 0

        if divSum / marketPrice < 0.6:
            print(comp, "div yield per year < 6%")
            continue

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " PE " + str(round(pe, 1)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " div10yr: " + str(round(divSum / marketPrice / 10, 2)) \
                       + "finviz div:" + finvizDic[comp] \
                       + "xueqiu div:" + xueqiuDic[comp]

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
