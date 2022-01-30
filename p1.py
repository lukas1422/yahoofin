import yahoo_fin.stock_info as si


def fo(number):
    return str(f"{number:,}")

def main():
    stockName = "IMOS"
    bs = si.get_balance_sheet(stockName)
    cf = si.get_cash_flow(stockName)
    incomeStatement = si.get_income_statement(stockName)

    info = si.get_company_info(stockName)
    country = info.loc["country"][0]
    sector= info.loc['sector'][0]


    #BS
    retainedEarnings = bs.loc["retainedEarnings"][0]
    equity = bs.loc["totalStockholderEquity"][0]
    totalCurrentAssets= bs.loc["totalCurrentAssets"][0]
    totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
    totalAssets = bs.loc["totalAssets"][0]
    totalLiab = bs.loc["totalLiab"][0]

    #IS
    revenue = incomeStatement.loc["totalRevenue"][0]
    EBIT = incomeStatement.loc["ebit"][0]

    #CF
    cfo = cf.loc["totalCashFromOperatingActivities"][0]
    cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
    cff = cf.loc["totalCashFromFinancingActivities"][0]

    marketPrice = si.get_live_price(stockName)
    shares = si.get_quote_data(stockName)['sharesOutstanding']


    #PRINTING*****
    print(stockName,country, sector)
    print("shares",shares/1000000000.0,"B")
    print("A",totalAssets/1000000000,"(", totalCurrentAssets/1000000000.0
          ,(totalAssets-totalCurrentAssets)/1000000000.0,")")
    print("L",totalLiab/1000000000,"(", totalCurrentLiab/1000000000.0,
          (totalLiab-totalCurrentLiab)/1000000000.0,")")
    print("E", (totalAssets-totalLiab) / 1000000000.0, "B")
    print("market cap USD", marketPrice*shares/1000000000.0,"B")
    print("shareholder equity", equity/1000000000.0, "B")

    #print("P/B", marketPrice*shares/equity)
    print("                         ")
    print("********ALTMAN**********")
    print("current ratio", totalCurrentAssets/totalCurrentLiab)
    print("D/E ratio", totalLiab/(totalAssets-totalLiab))
    print("EBIT", EBIT/1000000000,"B")
    print("CFO", cfo/1000000000,"B")
    print("CFI", cfi/1000000000,"B")
    print("CFF", cff / 1000000000, "B")
    print("retailed earnings", retainedEarnings/1000000000,"B")
    print("retailed earnings/totalAssets", retainedEarnings/totalAssets)
    print("revenue/totalAssets",revenue/totalAssets)


if __name__ == "__main__":
    main()
