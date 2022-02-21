import yahoo_fin.stock_info as si
import pandas as pd

from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK

COUNT = 0

MARKET = Market.HK
yearlyFlag = False


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_HK_ticker_errors', 'w')

if MARKET == Market.US:
    # US Version STARTS
    stock_df = pd.read_csv('list_US_companyInfo', sep=" ", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listDate'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
    # listStocks = ['AESC']
# US Version Ends

elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    hk_shares = pd.read_csv('list_HK_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
    listStocks = stock_df['ticker'].tolist()
    # listStocks = ['1513.HK']
else:
    raise Exception("market not found")

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment(), comp)
    try:
        marketPrice = si.get_live_price(comp)

        info = si.get_company_info(comp)
        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)
        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        currentRatio = totalCurrentAssets / totalCurrentLiab

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        goodWill = getFromDF(bs.loc['goodWill']) if 'goodWill' in bs.index else 0.0
        intangibles = getFromDF(bs.loc['intangibleAssets'])
        equity = totalAssets - totalLiab - goodWill - intangibles
        debtEquityRatio = totalLiab / equity
        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])
        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])
        # shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]

        revenue = getFromDF(incomeStatement.loc["totalRevenue"])

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)

        country = info.loc["country"][0]
        sector = info.loc['sector'][0]

        # fileOutput.write(outputString + '\n')
        # fileOutput.flush()

        print(comp, " success ")

    except Exception as e:
        print(comp, "exception", e)
        fileOutput.write(str("ERROR " + comp + ' ' + repr(e)) + '\n')
        fileOutput.flush()

        # raise Exception(comp, "raising exceptiona again", e)
