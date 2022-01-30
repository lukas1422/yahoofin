import yahoo_fin.stock_info as si
import datetime

START_DATE = '3/1/2020'
PRICE_INTERVAL = '1mo'

fileOutput = open('reportList', 'w')
fileOutput.write("\n")

with open("tickerList", "r") as file:
    lines = file.read().rstrip().splitlines()

print(lines)
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
                cf = si.get_cash_flow(comp)
                incomeStatement = si.get_income_statement(comp)

                equity = bs.loc["totalStockholderEquity"][0]
                totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
                totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
                totalAssets = bs.loc["totalAssets"][0]
                totalLiab = bs.loc["totalLiab"][0]
                retainedEarnings = bs.loc["retainedEarnings"][0]

                # IS
                # revenue = incomeStatement.loc["totalRevenue"][0]
                ebit = incomeStatement.loc["ebit"][0]

                # CF
                cfo = cf.loc["totalCashFromOperatingActivities"][0]
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
                except AssertionError as ae:
                    print(comp, "fails current ratio", currentRatio, ae)

                try:
                    assert debtEquityRatio < 1, 'debt equity ratio needs to be less than one'
                except AssertionError as ae:
                    print(comp, "fails DE ratio", debtEquityRatio, ae)

                try:
                    assert retainedEarnings > 0, "retained earnings needs to be greater than 0"
                except AssertionError as ae:
                    print(comp, "fails retained earnings", retainedEarnings, ae)

                try:
                    assert cfo > 0, "cfo needs to be greater than 0"
                except AssertionError as ae:
                    print(comp, "fails CFO", cfo, ae)

                try:
                    assert ebit > 0, "ebit needs to be postive"
                except AssertionError as ae:
                    print(datetime.datetime.now().time().strftime("%H:%M"), comp, "fails EBIT", ebit, ae)

                try:
                    assert currentRatio > 1, 'current ratio needs to be bigger than one'
                    assert debtEquityRatio < 1, 'debt equity ratio needs to be less than one'
                    assert retainedEarnings > 0, "retained earnings needs to be greater than 0"
                    assert cfo > 0, "cfo needs to be greater than 0"
                    assert ebit > 0, "ebit needs to be postive"
                except AssertionError as ae:
                    print(comp, "fails assertion", ae)
                else:
                    if (currentRatio > 1 and debtEquityRatio < 1 and retainedEarnings > 0
                            and cfo > 0 and ebit > 0):
                        pb = marketCap / equity
                        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)

                        try:
                            dataSize = data['adjclose'].size
                            percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
                                    data['adjclose'].max() - data['adjclose'].min())
                        except Exception as e:
                            print(comp, "percentile issue ", e)
                        else:
                            outputString = "SUCCESS " + comp + " " + country + " " + sector \
                                           + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                                           + " Equity:" + str(round((totalAssets-totalLiab) / 1000000000.0, 1)) + 'B' \
                                           + " CR:" + str(round(currentRatio, 1)) \
                                           + " D/E:" + str(round(debtEquityRatio, 1)) \
                                           + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                                           + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                                           + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                                           + " p/b:" + str(round(pb, 1)) \
                                           + " 52wk p%: " + str(round(percentile))

                            print(outputString)
                            fileOutput.write(outputString + '\n')
                            fileOutput.flush()
