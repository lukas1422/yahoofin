import yahoo_fin.stock_info as si


def main():
    with open("tickerList", "r") as file:
        lines = file.read().splitlines()

    print(lines)
    for comp in lines:
        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]
        bs = si.get_balance_sheet(comp)
        # print(comp, country)
        if (country.lower()) == "china":
            print(comp, "NO CHINA")
        # elif not ("retainedEarnings" in bs.index):
        #     print(comp, "has no retained earnings")
        else:
            print(comp, country)
            # bs = si.get_balance_sheet(comp)
            cf = si.get_cash_flow(comp)
            incomeStatement = si.get_income_statement(comp)
            #
            # if "retainedEarnings" in bs.index:
            #     retainedEarnings = bs.loc["retainedEarnings"][0]
            # else:
            #     print("retained earnings does not exist for ", comp)
            #     retainedEarnings = 0.0

            try:
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
                print("error when getting data", e)
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
                    print(comp, "fails EBIT", ebit, ae)

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
                        print(comp, country, sector,
                              "MV USD", round(marketCap / 1000000000.0, 2),
                              "CR", round(currentRatio, 2),
                              "D/E", round(debtEquityRatio, 2),
                              "RE/A", round(retainedEarningsAssetRatio, 2),
                              "cfo/A", round(cfoAssetRatio, 2),
                              "ebit/A", round(ebitAssetRatio, 2))

                    # print(comp,country, "CR",currentRatio, "DE",debt<1, RE>0, CFO>0, EBIT>0")


if __name__ == "__main__":
    main()
