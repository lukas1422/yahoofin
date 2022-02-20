import yahoo_fin.stock_info as si
import datetime

from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import math
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

fileOutput = open('list_deepValue', 'w')
fileOutput.write("\n")

with open("list_test", "r") as file:
    lines = file.read().rstrip().splitlines()

print(lines)
for comp in lines:
    print(increment())
    try:
        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]
        bs = si.get_balance_sheet(comp)
    except Exception as e:
        print(comp, "exception on info or BS")
    else:
        if (country.lower()) == " testFile ":
            print(comp, "NO CHINA")
        else:
            try:
                cf = si.get_cash_flow(comp)
                incomeStatement = si.get_income_statement(comp, yearly=False)

                totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
                totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
                totalAssets = getFromDF(bs.loc["totalAssets"])
                totalLiab = getFromDF(bs.loc["totalLiab"])
                goodWill = getFromDF(bs.loc['goodWill'] if 'goodWill' in bs.index else 0.0)
                intangibles = getFromDF(bs.loc['intangibleAssets'] if 'intangibleAssets' in bs.index else 0.0)
                equity = totalAssets - totalLiab - goodWill - intangibles

                retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

                ebit = getFromDF(incomeStatement.loc["ebit"])

                cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])
                marketPrice = si.get_live_price(comp)
                shares = si.get_quote_data(comp)['sharesOutstanding']
            except Exception as e:
                print("error when getting data ", comp, e)
            else:
                marketCap = marketPrice * shares
                currentRatio = totalCurrentAssets / totalCurrentLiab
                debtEquityRatio = totalLiab / (totalAssets - totalLiab)
                retainedEarningsAssetRatio = retainedEarnings / totalAssets
                cfoAssetRatio = cfo / totalAssets
                ebitAssetRatio = ebit / totalAssets

                try:
                    listingCurr = getListingCurrency(comp)

                    bsCurr = getBalanceSheetCurrency(comp, listingCurr)
                    exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)
                    pb = marketCap / (equity / exRate)
                    data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
                    divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
                    percentile = 100.0 * (marketPrice - data['low'].min()) / (data['high'].max() - data['low'].min())
                    divSum = divs['dividend'].sum() if not divs.empty else 0

                except Exception as e:
                    print(comp, "exception issue ", e)
                else:

                    outputString = comp + " " + country.replace(" ", "_") + " " \
                                   + sector.replace(" ", "_") + " " \
                                   + listingCurr + bsCurr \
                                   + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                                   + " Equity:" + str(
                        round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                                   + " CR:" + str(round(currentRatio, 1)) \
                                   + " D/E:" + str(round(debtEquityRatio, 1)) \
                                   + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                                   + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                                   + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                                   + " pb:" + str(round(pb, 1)) \
                                   + " 52w p%: " + str(round(percentile)) \
                                   + " div10yr: " + str(round(divSum / marketPrice, 2))

                    print(outputString)
                    # fileOutput.write(outputString + '\n')
                    # fileOutput.flush()
