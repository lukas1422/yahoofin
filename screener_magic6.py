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

fileOutput = open('list_magic6', 'w')

if MARKET == Market.US:
    stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

    finvizDiv = pd.read_csv('list_divYieldFinvizUS', sep=' ', index_col=False, names=['ticker', 'divi'])
    finvizDiv['divi'] = finvizDiv['divi'].replace('-', '0')
    finvizDiv['divi'] = finvizDiv['divi'].str.rstrip("%").astype(float)
    finvizDic = pd.Series(finvizDiv.divi.values, index=finvizDiv.ticker).to_dict()

    xueqiuDiv = pd.read_csv('list_divYieldXueqiuUS', sep=' ', index_col=False, names=['ticker', 'divi'])
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('-', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('none', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('error', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].astype(float)
    xueqiuDic = pd.Series(xueqiuDiv.divi.values, index=xueqiuDiv.ticker).to_dict()

elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_hkstocks', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    hk_shares = pd.read_csv('list_hk_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    listStocks = stock_df['ticker'].tolist()
    listStocks = ['0857.HK']
    # print(stock_df)
    # listStocks = stock_df['ticker'].tolist()

    xueqiuDiv = pd.read_csv('list_divYieldXueqiuHK', sep=' ', index_col=False, names=['ticker', 'divi'])
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('-', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('none', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].replace('error', '0')
    xueqiuDiv['divi'] = xueqiuDiv['divi'].astype(float)
    xueqiuDic = pd.Series(xueqiuDiv.divi.values, index=xueqiuDiv.ticker).to_dict()

else:
    raise Exception(" market not found")

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        # comp = convertHK(ticker)
        # companyName = stock_df[stock_df['ticker'] == ticker]['name'][0]

        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1:', marketPrice)
            continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)
        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]
        else:
            raise Exception(str(comp + " no shares"))

        # equity = getFromDF(bs.loc["totalStockholderEquity"])
        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        equity = totalAssets - totalLiab
        # shares = si.get_quote_data(comp)['sharesOutstanding']

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = cf.loc["totalCashFromOperatingActivities"][0]

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)
        pCfo = marketCap / (cfo / exRate)

        if pb > 0.6:
            print(comp, ' pb > 0.6 ', pb)
            continue

        if pCfo > 6 or pCfo < 0:
            print(comp, ' pCfo > 6 or < 0', pCfo)
            continue

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        divSum = divs['dividend'].sum() if not divs.empty else 0

        if divSum / marketPrice < 0.6:
            print(comp, "div yield per year < 6%")
            continue

        finvizComment = " finviz div:" + str(round(finvizDic[comp], 1)) if MARKET == Market.US else ""

        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'] \
            .to_string(index=False, header=False) \
                       + " " + listingCurr + bsCurr + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " PCFO " + str(round(pCfo, 1)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " div10yr Yr Yld: " + str(round(divSum / marketPrice * 10)) \
                       + finvizComment \
                       + " xueqiu div:" + str(round(xueqiuDic[comp], 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
