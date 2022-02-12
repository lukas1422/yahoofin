import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'


def fo(number):
    return str(f"{number:,}")


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

stockName = 'CLPS'

info = si.get_company_info(stockName)
country = info.loc["country"][0]
sector = info.loc['sector'][0]
print(stockName, country, sector)

bs = si.get_balance_sheet(stockName)
#print(bs)

# BS
retainedEarnings = bs.loc["retainedEarnings"][0]
equity = bs.loc["totalStockholderEquity"][0]
totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
totalAssets = bs.loc["totalAssets"][0]
totalLiab = bs.loc["totalLiab"][0]

cf = si.get_cash_flow(stockName)
incomeStatement = si.get_income_statement(stockName)

bsCurrency = getBalanceSheetCurrency(stockName)
listingCurrency = getListingCurrency(stockName)
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

marketPrice = si.get_live_price(stockName)
sharesYahoo = si.get_quote_data(stockName)['sharesOutstanding']
sharesXueqiu = scrape_sharesOutstanding.scrapeSharesOutstandingXueqiu(stockName)
sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)

marketCap = marketPrice * sharesYahoo
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

print(listingCurrency, bsCurrency, "ExRate ", exRate)
print("shares Yahoo", sharesYahoo / 1000000000.0, "B")
print("shares xueqiu", sharesXueqiu)
print("shares finviz", sharesFinviz)
print("A", round(totalAssets / exRate / 1000000000, 1), "B", "(",
      round(totalCurrentAssets / exRate / 1000000000.0, 1)
      , round((totalAssets - totalCurrentAssets) / exRate / 1000000000.0, 1), ")")
print("L", round(totalLiab / exRate / 1000000000, 1), "B", "(",
      round(totalCurrentLiab / exRate / 1000000000.0, 1),
      round((totalLiab - totalCurrentLiab) / exRate / 1000000000.0, 1), ")")
print("E", round((totalAssets - totalLiab) / exRate / 1000000000.0, 1), "B")
print("price shs", round(marketPrice, 2))
print("BV/Shs", round((totalAssets - totalLiab) / exRate / sharesYahoo, 2))
print("MV USD", round(marketPrice * sharesYahoo / 1000000000.0, 1), "B")
# print("Eq USD", round((equity / exRate) / 1000000000.0), "B")

print("P/B", round(marketPrice * sharesYahoo / (equity / exRate), 2))
print("P/E", round(marketPrice * sharesYahoo / (netIncome / exRate), 2))
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
print(" div return over 10 yrs ", round(divSum / marketPrice, 2))
print("divsum marketprice", round(divSum, 2), round(marketPrice, 2))
print('roa', roa)


outputString = stockName + " " + country + " " + sector \
               + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
               + " Equity:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
               + " CR:" + str(round(currentRatio, 1)) \
               + " D/E:" + str(round(debtEquityRatio, 1)) \
               + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
               + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
               + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
               + " pb:" + str(round(pb, 1)) \
               + " 52w p%: " + str(round(percentile)) \
               + " div10yr: " + str(round(divSum / marketPrice, 2))

print(outputString)
