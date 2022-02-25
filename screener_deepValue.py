import yahoo_fin.stock_info as si
import pandas as pd
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, getFromDFYearly

MARKET = Market.HK
yearlyFlag = False

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


PRICE_START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_deepValue', 'w')

if MARKET == Market.US:
    # US Version STARTS
    stock_df = pd.read_csv('list_US_companyInfo', sep=" ", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listDate'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
    # listStocks = ['CRUS']

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
        if marketPrice <= 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        info = si.get_company_info(comp)

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            # fileOutput.write("ERROR BS IS EMPTY " + comp + '\n')
            # fileOutput.flush()
            continue

        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"]) if 'totalCurrentAssets' in bs.index else 0.0
        totalCurrentLiab = getFromDF(
            bs.loc["totalCurrentLiabilities"]) if 'totalCurrentLiabilities' in bs.index else 0.0
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio <= 1:
            print(comp, "current ratio < 1", currentRatio)
            continue

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0.0

        if retainedEarnings <= 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        goodWill = getFromDF(bs.loc['goodWill']) if 'goodWill' in bs.index else 0.0
        intangibles = getFromDF(bs.loc['intangibleAssets']) if 'intangibleAssets' in bs.index else 0.0
        tangibleEquity = totalAssets - totalLiab - goodWill - intangibles
        debtEquityRatio = totalLiab / tangibleEquity

        if debtEquityRatio > 1:
            print(comp, "de ratio> 1. ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)
        ebit = getFromDFYearly(incomeStatement, "ebit", yearlyFlag)
        netIncome = getFromDFYearly(incomeStatement, 'netIncome', yearlyFlag)

        if ebit <= 0 or netIncome <= 0:
            print(comp, "ebit or net income < 0 ", ebit, " ", netIncome)
            continue

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]
        else:
            raise Exception(str(comp + " no shares"))

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)

        print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        print(bsCurrency, listingCurrency)
        marketCap = marketPrice * shares
        pb = marketCap / (tangibleEquity / exRate)
        # pe = marketCap / (netIncome / exRate)
        pCfo = marketCap / (cfo / exRate)

        if pb >= 1 or pb <= 0:
            print(comp, 'pb > 1 or pb <= 0', pb)
            continue

        if pCfo > 6 or pCfo <= 0:
            print(comp, 'pcfo > 10 or <= 0', pCfo)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        ebitAssetRatio = ebit / totalAssets

        data = si.get_data(comp, start_date=PRICE_START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        percentile = 100.0 * (marketPrice - data['low'].min()) / (data['high'].max() - data['low'].min())
        divSum = divs['dividend'].sum() if not divs.empty else 0

        country = info.loc["country"][0]
        sector = info.loc['sector'][0]

        outputString = comp + " " + " " + stock_df[stock_df['ticker'] == comp]['name'] \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Eq:" + str(round(tangibleEquity / exRate / 1000000000.0, 1)) + 'B' \
                       + " P/CFO:" + str(round(pCfo, 2)) \
                       + " P/B:" + str(round(pb, 1)) \
                       + " CurRatio:" + str(round(currentRatio, 2)) \
                       + " D/E:" + str(round(debtEquityRatio, 2)) \
                       + " RetEarnings/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                       + " ebit/A:" + str(round(ebitAssetRatio, 2)) \
                       + " S/A:" + str(round(revenue / totalAssets, 2)) \
                       + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                       + " 52w_p%:" + str(round(percentile)) \
                       + " divYld: " + str(round(divSum / marketPrice * 10))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        fileOutput.flush()
