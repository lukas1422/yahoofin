# schloss method
# no financials,
# PB < 1
# no long term debt
# price < 1.1 * 52 week low
# insider  ownership > median

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

fileOutput = open('list_schlossOutput', 'w')

ownership = pd.read_csv('list_insiderOwnership_finviz', sep=' ',
                        index_col=False, names=['ticker', 'perc'])
ownership['perc'] = ownership['perc'].replace('-', '0')
ownership['perc'] = ownership['perc'].str.rstrip("%").astype(float)
ownershipDic = pd.Series(ownership.perc.values, index=ownership.ticker).to_dict()
print(ownershipDic)

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

# print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        insiderPerc = ownershipDic[comp]
        if insiderPerc < 10:
            print(comp, "insider ownership < 10%", insiderPerc)
            continue

        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        # info = si.get_company_info(comp)
        # if info.loc["country"][0].lower() == "china":
        #     print(comp, "no china")
        #     continue

        # totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        # totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        # currentRatio = totalCurrentAssets / totalCurrentLiab
        #
        # if currentRatio < 1:
        #     print(comp, "current ratio < 1")
        #     continue

        bs = si.get_balance_sheet(comp)
        # retainedEarnings = getFromDF(bs.loc["retainedEarnings"])
        #
        # if retainedEarnings < 0:
        #     print(comp, " retained earnings < 0 ", retainedEarnings)
        #     continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        currentLiab = getFromDF(bs.loc['totalCurrentLiabilities'])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        longTermDebtRatio = (totalLiab - currentLiab) / totalAssets

        if debtEquityRatio > 1 or totalAssets < totalLiab:
            print(comp, " de ratio> 1 or A<L. ", debtEquityRatio)
            continue

        # incomeStatement = si.get_income_statement(comp, yearly=True)
        # ebit = getFromDF(incomeStatement.loc["ebit"])
        # netIncome = getFromDF(incomeStatement.loc['netIncome'])
        #
        # if ebit < 0 or netIncome < 0:
        #     print(comp, "ebit or net income < 0 ", ebit, " ", netIncome)
        #     continue

        # cf = si.get_cash_flow(comp)
        # cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])
        #
        # if cfo < 0:
        #     print(comp, "cfo < 0 ", cfo)
        #     continue

        equity = getFromDF(bs.loc["totalStockholderEquity"])

        if equity < 0:
            print(comp, "equity < 0", equity)

        shares = si.get_quote_data(comp)['sharesOutstanding']

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)
        # pe = marketCap / (netIncome / exRate)

        if pb > 1:
            print(comp, ' pb > 1', pb)
            continue

        # if pe > 10 or pe < 0:
        #     print(comp, ' pe > 10 or < 0')
        #     continue

        # revenue = getFromDF(incomeStatement.loc["totalRevenue"])
        #
        # retainedEarningsAssetRatio = retainedEarnings / totalAssets
        # cfoAssetRatio = cfo / totalAssets
        # ebitAssetRatio = ebit / totalAssets

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        low_52wk = data['adjclose'].min()

        if marketPrice > low_52wk * 1.1:
            print(comp, "exceeding 52wk low * 1.1")
            continue

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Eq:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " LT debt ratio" + str(round(longTermDebtRatio, 1)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " insider%:" + str(round(insiderPerc, 1)) \
                       + " p/52low: " + str(round(marketPrice / low_52wk))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
