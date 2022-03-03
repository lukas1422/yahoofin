import yahoo_fin.stock_info as si
import datetime
from helperMethods import getFromDF
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_netnet', 'w')

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


with open("list_NewLowTopLoser", "r") as file:
    lines = file.read().rstrip().splitlines()

print(lines)

for comp in lines:
    print(increment())

    try:
        info = si.get_company_info(comp)
        print(comp, info.loc['country'][0])

        if info.loc["country"][0].lower() == "china":
            print(comp, "NO CHINA")
            continue

        bs = si.get_balance_sheet(comp)
        retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

        if retainedEarnings < 0:
            print(comp, "RE < 0", retainedEarnings)
            continue

        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])

        if totalCurrentAssets - totalLiab < 0:
            print(datetime.datetime.now().time().strftime("%H:%M"), comp, "not a net net")
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])

        if totalLiab / (totalAssets - totalLiab) > 1:
            print(comp, "DE > 1")
            continue

        totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio < 1:
            print(comp, "current ratio < 1", currentRatio)
            continue

        cf = si.get_cash_flow(comp)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])

        if cfo < 0:
            print(comp, 'cfo < 0', cfo)
            continue

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)
        equity = getFromDF(bs.loc["totalStockholderEquity"])
        marketPrice = si.get_live_price(comp)
        shares = si.get_quote_data(comp)['sharesOutstanding']
        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)

        if pb > 1:
            print(comp, 'pb > 1', pb)
            continue

        # IS
        incomeStatement = si.get_income_statement(comp)
        revenue = getFromDF(incomeStatement.loc["totalRevenue"])
        ebit = getFromDF(incomeStatement.loc["ebit"])
        # netIncome = getFromDF(incomeStatement.loc['netIncome'])
        # cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
        # cff = cf.loc["totalCashFromFinancingActivities"][0]
        # retainedEarningsAssetRatio = retainedEarnings / totalAssets

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)

        divSum = divs['dividend'].sum() if not divs.empty else 0

        percentile = 100.0 * (marketPrice - data['adjclose'].min()) / (
                data['adjclose'].max() - data['adjclose'].min())

        outputString = "NN " + comp + " " \
                       + info.loc["country"][0].replace(" ", "_") + " " \
                       + info.loc['sector'][0].replace(" ", "_") \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " Equity:" + str(round((totalAssets - totalLiab) / 1000000000.0, 1)) + 'B' \
                       + " CR:" + str(round(currentRatio, 1)) \
                       + " D/E:" + str(round(totalLiab / (totalAssets - totalLiab), 1)) \
                       + " EBIT/A:" + str(round(ebit / totalAssets, 1)) \
                       + " RE/A:" + str(round(retainedEarnings / totalAssets, 1)) \
                       + "S/A:" + str(round(revenue / totalAssets, 1)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " 52w p%: " + str(round(percentile)) \
                       + " div10yr: " + str(round(divSum / marketPrice, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "netnet exception", e)
        raise Exception(comp, "raising exception again", e)

