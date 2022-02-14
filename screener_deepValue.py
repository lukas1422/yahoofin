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

fileOutput = open('list_results', 'w')
fileOutput.write("\n")

# US Version STARTS
# stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
#                        names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])
#
# listStocks = stock_df[(stock_df['price'] > 1)
#                       & (stock_df['sector'].str
#                          .contains('financial|healthcare', regex=True, case=False) == False)
#                       & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
#                       & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
# US Version Ends

# HK version STARTS
stock_df = pd.read_csv('list_hkstocks', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
# HK Version ENDS

listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        info = si.get_company_info(comp)
        # if info.loc["country"][0].lower() == "china":
        #     print(comp, "no china")
        #     continue

        bs = si.get_balance_sheet(comp)
        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio < 1:
            print(comp, "current ratio < 1")
            continue

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

        if retainedEarnings < 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        if debtEquityRatio > 1:
            print(comp, " de ratio> 1. ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=True)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if ebit < 0 or netIncome < 0:
            print(comp, "ebit or net income < 0 ", ebit, " ", netIncome)
            continue

        cf = si.get_cash_flow(comp)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])

        if cfo < 0:
            print(comp, "cfo < 0 ", cfo)
            continue

        equity = getFromDF(bs.loc["totalStockholderEquity"])
        shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)

        print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)

        print(bsCurrency, listingCurrency)
        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)
        # pe = marketCap / (netIncome / exRate)
        pcfo = marketCap / (cfo / exRate)

        if pb > 1:
            print(comp, ' pb > 1', pb)
            continue

        if pcfo > 10 or pcfo < 0:
            print(comp, ' pcfo > 10 or < 0', pcfo)
            continue

        revenue = getFromDF(incomeStatement.loc["totalRevenue"])

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        ebitAssetRatio = ebit / totalAssets

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
                data['adjclose'].max() - data['adjclose'].min())
        divSum = divs['dividend'].sum() if not divs.empty else 0

        #                       # + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
        #     .to_string(index=False, header=False) + " " \

        outputString = comp + " " \
                       + listingCurrency + bsCurrency + str(round(exRate, 2)) \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Eq:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                       + " P/CFO " + str(round(pcfo, 1)) \
                       + " PB:" + str(round(pb, 1)) \
                       + " C/R:" + str(round(currentRatio, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                       + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                       + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                       + " S/A " + str(round(revenue / totalAssets, 2)) \
                       + " 52w p%: " + str(round(percentile)) \
                       + " div10yr: " + str(round(divSum / marketPrice, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
