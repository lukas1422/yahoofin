import yahoo_fin.stock_info as si
import datetime

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

fileOutput = open('reportList', 'w')
fileOutput.write("\n")

with open("tickerList", "r") as file:
    lines = file.read().rstrip().splitlines()

for comp in lines:
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
                totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
                totalLiab = bs.loc["totalLiab"][0]
            except Exception as e:
                print("error when getting data ", comp, e)
            else:
                netnet = totalCurrentAssets - totalLiab
                try:
                    assert netnet > 0
                except AssertionError as ae:
                    print(datetime.datetime.now().time().strftime("%H:%M"), comp, "fails assertion", ae)
                else:
                    try:
                        cf = si.get_cash_flow(comp)
                        incomeStatement = si.get_income_statement(comp)

                        # BS
                        retainedEarnings = bs.loc["retainedEarnings"][0]
                        equity = bs.loc["totalStockholderEquity"][0]
                        totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
                        totalAssets = bs.loc["totalAssets"][0]

                        # IS
                        revenue = incomeStatement.loc["totalRevenue"][0]
                        ebit = incomeStatement.loc["ebit"][0]

                        # CF
                        cfo = cf.loc["totalCashFromOperatingActivities"][0]
                        cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
                        cff = cf.loc["totalCashFromFinancingActivities"][0]

                        marketPrice = si.get_live_price(comp)
                        shares = si.get_quote_data(comp)['sharesOutstanding']

                        marketCap = marketPrice * shares
                        currentRatio = totalCurrentAssets / totalCurrentLiab
                        debtEquityRatio = totalLiab / (totalAssets - totalLiab)
                        retainedEarningsAssetRatio = retainedEarnings / totalAssets
                        cfoAssetRatio = cfo / totalAssets
                        ebitAssetRatio = ebit / totalAssets

                        pb = marketCap / equity
                        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
                        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)

                        divSum = divs['dividend'].sum() if not divs.empty else 0

                        percentile = 100.0 * (marketPrice - data['adjclose'].min()) / (
                                data['adjclose'].max() - data['adjclose'].min())

                    except Exception as e:
                        print("except is ", e)
                    else:
                        outputString = "NN " + comp + " " + country.replace(" ", "_") + " " \
                                       + sector.replace(" ", "_") \
                                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                                       + " Equity:" + str(round((totalAssets - totalLiab) / 1000000000.0, 1)) + 'B' \
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
