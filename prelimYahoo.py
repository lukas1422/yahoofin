import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding
from helperMethods import getFromDF

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'


def fo(number):
    return str(f"{number:,}")


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

stockName = '1812.HK'
# stockName = 'VIAC'
yearlyFlag = False

info = si.get_company_info(stockName)
country = info.loc["country"][0]
sector = info.loc['sector'][0]
industry = info.loc['industry'][0]
longName = info.loc['longBusinessSummary'][0]

print(stockName, country, sector, industry)
print(longName)

bs = si.get_balance_sheet(stockName, yearly=yearlyFlag)
print("balance sheet date:", bs.columns[0].strftime('%Y/%-m/%-d'))
print(bs)
# BS
retainedEarnings = bs.loc["retainedEarnings"][0]
# equity = bs.loc["totalStockholderEquity"][0]
totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
totalAssets = bs.loc["totalAssets"][0]
totalLiab = bs.loc["totalLiab"][0]
equity = totalAssets - totalLiab
cash = getFromDF(bs.loc['cash']) if 'cash' in bs.index else 0.0
receivables = getFromDF(bs.loc['netReceivables']) if 'netReceivables' in bs.index else 0.0
inventory = getFromDF(bs.loc['inventory']) if 'inventory' in bs.index else 0.0
goodWill = getFromDF(bs.loc['goodWill'] if 'goodWill' in bs.index else 0.0)

print("goodwill is ", goodWill)

cf = si.get_cash_flow(stockName, yearly=yearlyFlag)
print("cash flow statement date:", cf.columns[0].strftime('%Y/%-m/%-d'))

incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

listingCurrency = getListingCurrency(stockName)
bsCurrency = getBalanceSheetCurrency(stockName, listingCurrency)
exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

# IS
revenue = incomeStatement.loc["totalRevenue"][0]
ebit = incomeStatement.loc["ebit"][0]
netIncome = incomeStatement.loc['netIncome'][0]

roa = netIncome / totalAssets

# CF
cfo = cf.loc["totalCashFromOperatingActivities"][0]
cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
cff = cf.loc["totalCashFromFinancingActivities"][0]
cfoA = cfo / totalAssets

marketPrice = si.get_live_price(stockName)
# sharesYahoo = si.get_quote_data(stockName)['sharesOutstanding']
sharesTotalXueqiu = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(stockName)
floatingSharesXueqiu = scrape_sharesOutstanding.scrapeFloatingSharesXueqiu(stockName)
sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)

marketCap = marketPrice * sharesTotalXueqiu
currentRatio = totalCurrentAssets / totalCurrentLiab
debtEquityRatio = totalLiab / (totalAssets - totalLiab)
retainedEarningsAssetRatio = retainedEarnings / totalAssets
cfoAssetRatio = cfo / totalAssets
ebitAssetRatio = ebit / totalAssets

pb = marketCap / (equity / exRate)
data = si.get_data(stockName, start_date=START_DATE, interval=PRICE_INTERVAL)
divs = si.get_dividends(stockName, start_date=DIVIDEND_START_DATE)

# print(data)
percentile = 100.0 * (marketPrice - data['low'].min()) / (data['high'].max() - data['low'].min())

# if not divs.empty:
divSum = divs['dividend'].sum() if not divs.empty else 0.0
# else:
#     divSum = 0.0

# PRINTING*****

###exchange rate override?
exRate = 1

print("listing Currency:", listingCurrency, "balance sheet currency", bsCurrency, "ExRate ", exRate)
# print("shares Yahoo", sharesYahoo / 1000000000.0, "B")
print("total shares xueqiu", str(sharesTotalXueqiu / 1000000000) + "B")
# print("floating shares xueqiu", str(floatingSharesXueqiu / 1000000000) + "B")
print("shares finviz", sharesFinviz)
print("cash", round(cash / 1000000000, 2), "rec", round(receivables / 1000000000, 2), "inv",
      round(inventory / 1000000000, 2))
print("A", round(totalAssets / exRate / 1000000000, 1), "B", "(",
      round(totalCurrentAssets / exRate / 1000000000.0, 1)
      , round((totalAssets - totalCurrentAssets) / exRate / 1000000000.0, 1), ")")
print("L", round(totalLiab / exRate / 1000000000, 1), "B", "(",
      round(totalCurrentLiab / exRate / 1000000000.0, 1),
      round((totalLiab - totalCurrentLiab) / exRate / 1000000000.0, 1), ")")
print("E", round((totalAssets - totalLiab) / exRate / 1000000000.0, 1), "B")
print("BV per share", round((totalAssets - totalLiab) / exRate / sharesTotalXueqiu, 2))
print("Market price", round(marketPrice, 2), listingCurrency)
print("Market Cap", str(round(marketPrice * sharesTotalXueqiu / 1000000000.0, 1)) + "B")
# print("Eq USD", round((equity / exRate) / 1000000000.0), "B")


print("P/B", round(marketPrice * sharesTotalXueqiu / (equity / exRate), 2))
print("P/E", round(marketPrice * sharesTotalXueqiu / (netIncome / exRate), 2))
print("S/B", round(revenue / equity, 2))
print("                         ")
print("********ALTMAN**********")
print("CR", round(totalCurrentAssets / totalCurrentLiab, 2))
print("D/E", round(totalLiab / (totalAssets - totalLiab), 2))
print("EBIT", round(ebit / exRate / 1000000000, 2), "B")
print("netIncome", round(netIncome / exRate / 1000000000, 2), "B")
print("CFO", round(cfo / exRate / 1000000000, 2), "B")
print("CFI", round(cfi / exRate / 1000000000, 2), "B")
print("CFF", round(cff / 1000000000 / exRate, 2), "B")
print("RE", round(retainedEarnings / 1000000000 / exRate, 2), "B")
print("RE/A", round(retainedEarnings / totalAssets, 2))
print("S/A", round(revenue / totalAssets, 2))
print("div annual yield:", round(divSum / marketPrice * 10))
print("divsum marketprice:", round(divSum, 2), round(marketPrice, 2))
print('roa', roa)
print('cfoA', cfoA)

outputString = stockName + " " + country + " " + sector \
               + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
               + " Equity:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
               + " CR:" + str(round(currentRatio, 2)) \
               + " D/E:" + str(round(debtEquityRatio, 2)) \
               + " RE/A:" + str(round(retainedEarningsAssetRatio, 2)) \
               + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
               + " ebit/A:" + str(round(ebitAssetRatio, 2)) \
               + " pb:" + str(round(pb, 2)) \
               + " 52w p%:" + str(round(percentile)) \
               + " div10yr:" + str(round(divSum / marketPrice, 2))

print(outputString)
