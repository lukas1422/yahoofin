import yahoo_fin.stock_info as si

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'


def fo(number):
    return str(f"{number:,}")


def processStock(si, stockName):
    bs = si.get_balance_sheet(stockName)
    cf = si.get_cash_flow(stockName)
    incomeStatement = si.get_income_statement(stockName)

    info = si.get_company_info(stockName)
    country = info.loc["country"][0]
    sector = info.loc['sector'][0]

    # BS
    retainedEarnings = bs.loc["retainedEarnings"][0]
    equity = bs.loc["totalStockholderEquity"][0]
    totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
    totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
    totalAssets = bs.loc["totalAssets"][0]
    totalLiab = bs.loc["totalLiab"][0]

    # IS
    revenue = incomeStatement.loc["totalRevenue"][0]
    ebit = incomeStatement.loc["ebit"][0]

    # CF
    cfo = cf.loc["totalCashFromOperatingActivities"][0]
    cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
    cff = cf.loc["totalCashFromFinancingActivities"][0]

    marketPrice = si.get_live_price(stockName)
    shares = si.get_quote_data(stockName)['sharesOutstanding']

    marketCap = marketPrice * shares
    currentRatio = totalCurrentAssets / totalCurrentLiab
    debtEquityRatio = totalLiab / (totalAssets - totalLiab)
    retainedEarningsAssetRatio = retainedEarnings / totalAssets
    cfoAssetRatio = cfo / totalAssets
    ebitAssetRatio = ebit / totalAssets

    pb = marketCap / equity
    data = si.get_data(stockName, start_date=START_DATE, interval=PRICE_INTERVAL)
    divs = si.get_dividends(stockName, start_date=DIVIDEND_START_DATE)
    #dataSize = data['adjclose'].size

    percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
            data['adjclose'].max() - data['adjclose'].min())

    divSum = divs['dividend'].sum()

    # PRINTING*****
    print(stockName, country, sector)
    print("shares", shares / 1000000000.0, "B")
    print("A", totalAssets / 1000000000, "(", totalCurrentAssets / 1000000000.0
          , (totalAssets - totalCurrentAssets) / 1000000000.0, ")")
    print("L", totalLiab / 1000000000, "(", totalCurrentLiab / 1000000000.0,
          (totalLiab - totalCurrentLiab) / 1000000000.0, ")")
    print("E", (totalAssets - totalLiab) / 1000000000.0, "B")
    print("market cap USD", marketPrice * shares / 1000000000.0, "B")
    print("shareholder equity", equity / 1000000000.0, "B")

    # print("P/B", marketPrice*shares/equity)
    print("                         ")
    print("********ALTMAN**********")
    print("current ratio", totalCurrentAssets / totalCurrentLiab)
    print("D/E ratio", totalLiab / (totalAssets - totalLiab))
    print("EBIT", ebit / 1000000000, "B")
    print("CFO", cfo / 1000000000, "B")
    print("CFI", cfi / 1000000000, "B")
    print("CFF", cff / 1000000000, "B")
    print("retailed earnings", retainedEarnings / 1000000000, "B")
    print("retailed earnings/totalAssets", retainedEarnings / totalAssets)
    print("revenue/totalAssets", revenue / totalAssets)

    outputString = stockName + " " + country + " " + sector \
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
    return outputString

processStock(si, "PKX")
