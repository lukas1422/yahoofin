import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding
from helperMethods import getFromDF, getFromDFYearly, roundB

START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'


def fo(number):
    return str(f"{number:,}")


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

stockName = '0363.HK'
# stockName = 'VIAC'
yearlyFlag = False

info = si.get_company_info(stockName)
country = getFromDF(info, "country")
sector = getFromDF(info, 'sector')
industry = getFromDF(info, 'industry')
longName = getFromDF(info, 'longBusinessSummary')

print(stockName, country, sector, industry)
print(longName)

bs = si.get_balance_sheet(stockName, yearly=yearlyFlag)
# print("bs", bs)
print("balance sheet date:", bs.columns[0].strftime('%Y/%-m/%-d'))
# BS
retainedEarnings = getFromDF(bs, "retainedEarnings")
totalCurrentAssets = getFromDF(bs, "totalCurrentAssets")
totalCurrentLiab = getFromDF(bs, "totalCurrentLiabilities")
totalAssets = getFromDF(bs, "totalAssets")
totalLiab = getFromDF(bs, "totalLiab")
equity = totalAssets - totalLiab
cash = getFromDF(bs, 'cash')
receivables = getFromDF(bs, 'netReceivables')
inventory = getFromDF(bs, 'inventory')
goodWill = getFromDF(bs, 'goodWill')

print("goodwill is ", goodWill)

cf = si.get_cash_flow(stockName, yearly=yearlyFlag)
print("cash flow statement : ", cf)

print("cash flow statement date:", cf.columns[0].strftime('%Y/%-m/%-d'))

incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

listingCurrency = getListingCurrency(stockName)
bsCurrency = getBalanceSheetCurrency(stockName, listingCurrency)
exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

# IS
revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
ebit = getFromDFYearly(incomeStatement, "ebit", yearlyFlag)
netIncome = getFromDFYearly(incomeStatement, 'netIncome', yearlyFlag)

roa = netIncome / totalAssets

# CF
cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
cfi = getFromDFYearly(cf, "totalCashflowsFromInvestingActivities", yearlyFlag)
cff = getFromDFYearly(cf, "totalCashFromFinancingActivities", yearlyFlag)

cfoA = cfo / totalAssets

# print("cfo is ", round(cfo / 1000000000, 2), "B")

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
print("total shares xueqiu", str(roundB(sharesTotalXueqiu, 2)) + "B")
# print("floating shares xueqiu", str(floatingSharesXueqiu / 1000000000) + "B")
print("shares finviz", sharesFinviz)
print("cash", roundB(cash, 2), "rec", roundB(receivables, 2), "inv",
      roundB(inventory, 2))
print("A", roundB(totalAssets / exRate, 1), "B", "(",
      roundB(totalCurrentAssets / exRate, 1)
      , roundB((totalAssets - totalCurrentAssets) / exRate, 1), ")")
print("L", roundB(totalLiab / exRate, 1), "B", "(",
      roundB(totalCurrentLiab / exRate, 1),
      roundB((totalLiab - totalCurrentLiab) / exRate, 1), ")")
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
print("div annual yield:", round(divSum / marketPrice * 10), "%")
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
               + " 52w_p%:" + str(round(percentile)) \
               + " div10yr:" + str(round(divSum / marketPrice, 2))

print(outputString)
