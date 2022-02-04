import yahoo_fin.stock_info as si
import datetime

from scrapeYahooCurrency import getBalanceSheetCurrency
import math
import getExchangeRate

COUNT = 0


def getFromDF(df):
    if df.empty:
        return 0
    elif math.isnan(df[0]):
        return df[1]
    return df[0]


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = getExchangeRate.getExchangeRateDict()

fileOutput = open('reportList', 'w')
fileOutput.write("\n")

with open("listNewLowTopLoser", "r") as file:
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
        if (country.lower()) == "china":
            print(comp, "NO CHINA")
        else:
            try:
                cf = si.get_cash_flow(comp)
                incomeStatement = si.get_income_statement(comp)

                equity = getFromDF(bs.loc["totalStockholderEquity"])
                totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
                totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
                totalAssets = getFromDF(bs.loc["totalAssets"])
                totalLiab = getFromDF(bs.loc["totalLiab"])
                retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

                # print(comp, "bs.loc[total assets ]", bs.loc['totalAssets'])
                # print(comp, "bs.loc[retained Earnings]", bs.loc['retainedEarnings'])
                # print(comp, "retained earnings ", retainedEarnings)

                # IS
                # revenue = incomeStatement.loc["totalRevenue"][0]
                ebit = getFromDF(incomeStatement.loc["ebit"])

                # CF
                cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])
                #print("cfo ", cfo, cf.loc["totalCashFromOperatingActivities"])
                # cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
                # cff = cf.loc["totalCashFromFinancingActivities"][0]
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
                    assert currentRatio > 1, 'current ratio needs to be bigger than one'
                    assert debtEquityRatio < 1, 'debt equity ratio needs to be less than one'
                    assert retainedEarnings > 0, "retained earnings needs to be greater than 0"
                    assert cfo > 0, "cfo needs to be greater than 0"
                    assert ebit > 0, "ebit needs to be postive"
                except AssertionError as ae:
                    print(datetime.datetime.now().time().strftime("%H:%M"), comp, "fails assertion", ae)
                else:
                    if (currentRatio > 1 and debtEquityRatio < 1 and retainedEarnings > 0
                            and cfo > 0 and ebit > 0):
                        try:
                            balanceSheetCurrency = getBalanceSheetCurrency(comp)
                            exRate = getExchangeRate.getExchangeRate(exchange_rate_dict, balanceSheetCurrency)
                            print("bal sheet currency is ", balanceSheetCurrency, " rate is ", exRate)

                            pb = marketCap / (equity / exRate)

                            data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
                            divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
                            # dataSize = data['adjclose'].size
                            # print(" percentile current min max ", marketPrice, data['adjclose'].max(),
                            #       data['adjclose'].min())

                            percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
                                    data['adjclose'].max() - data['adjclose'].min())

                            divSum = divs['dividend'].sum() if not divs.empty else 0

                        except Exception as e:
                            print(comp, "exception issue ", e)
                        else:
                            outputString = comp + " " + country.replace(" ", "_") + " " \
                                           + sector.replace(" ", "_") + " " \
                                           + balanceSheetCurrency \
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
                            fileOutput.write(outputString + '\n')
                            fileOutput.flush()
