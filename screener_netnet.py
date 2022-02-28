# screens for netnets
# both HK and US

import yahoo_fin.stock_info as si
import pandas as pd

import scrape_sharesOutstanding
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, roundB

COUNT = 0

MARKET = Market.US
yearlyFlag = False


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_netnet', 'w')

# US Version Starts
if MARKET == Market.US:
    stock_df = pd.read_csv('list_US_companyInfo', sep=" ", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listingDate'])

    stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['listingDate'] < pd.to_datetime('2020-1-1'))
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    listStocks = stock_df['ticker'].tolist()
    hk_shares = pd.read_csv('list_HK_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
    # listStocks = ['0155.HK']
else:
    raise Exception("market not found")

print(MARKET, len(listStocks), listStocks)

for comp in listStocks:
    print(increment(), comp)

    try:
        info = si.get_company_info(comp)
        # print("info is", info)
        country = getFromDF(info, 'country')
        sector = info.loc['sector'][0]
        # print("country:", country, "sector", sector)

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)

        if marketPrice < 1:
            print(comp, "cent stock", marketPrice)
            continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        cash = getFromDF(bs, 'cash')
        if cash == 0:
            print(comp, 'cash is 0 ')
            continue

        currentAssets = getFromDF(bs, "totalCurrentAssets")
        totalLiab = getFromDF(bs, "totalLiab")

        if currentAssets < totalLiab:
            print(comp, " current assets < total liab", roundB(currentAssets, 2), roundB(totalLiab, 2))
            continue

        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        # shares = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(comp)
        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]
        else:
            raise Exception("market not found ", MARKET)

        marketCap = marketPrice * shares

        if MARKET == Market.HK:
            if marketCap < 1000000000:
                print(comp, "HK market cap less than 1B", marketCap / 1000000000)
                continue

        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if (cash + receivables + inventory - totalLiab) / exRate < marketCap:
            print(comp, listingCurr, bsCurr,
                  'cash + rec + inventory - total liab < mv. cash rec inv Liab MV:',
                  roundB(cash, 2), roundB(receivables, 2),
                  roundB(inventory, 2), roundB(totalLiab, 2), roundB(marketCap, 2))
            continue

        additionalComment = ""
        if (cash - totalLiab) / exRate - marketCap > 0:
            profit = (cash - totalLiab) / exRate - marketCap
            additionalComment = " CASH netnet, profit:" + str(round(profit, 2))
        elif (cash + receivables - totalLiab) / exRate - marketCap > 0:
            additionalComment = " receivable conversion rate:" \
                                + str(round((totalLiab + marketCap * exRate - cash) / receivables, 2))
        elif (cash + 0.5 * receivables + inventory - totalLiab) / exRate - marketCap > 0:
            additionalComment = " inventory conversion rate:" \
                                + str(round((totalLiab + marketCap * exRate - cash - 0.5 * receivables)
                                            / inventory, 2))
        elif (cash + receivables + inventory - totalLiab) / exRate - marketCap > 0:
            additionalComment = "鸡肋:CA-L>MV"

        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'] \
            .to_string(index=False, header=False) + " " \
                       + listingCurr + bsCurr + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + " cash:" + str(roundB(cash, 2)) \
                       + " rec:" + str(roundB(receivables, 2)) \
                       + " inv:" + str(roundB(inventory, 2)) \
                       + " CA:" + str(roundB(currentAssets, 2)) \
                       + " L:" + str(roundB(totalLiab, 2)) \
                       + " mv:" + str(roundB(marketCap, 2)) \
                       + additionalComment

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        # print(comp, "exception", e)
        # raise Exception(comp, "raising exception again", e)
        print(comp, "exception", e)
        # fileOutput.write("ERROR " + comp + " " + repr(e) + '\n')
        # fileOutput.flush()
