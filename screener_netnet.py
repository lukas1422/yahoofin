# screens for netnets
# both HK and US

import yahoo_fin.stock_info as si
import pandas as pd

import scrape_sharesOutstanding
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK

COUNT = 0

MARKET = Market.HK
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
    # listStocks = ['1513.HK']
else:
    raise Exception("market not found")

print(MARKET, len(listStocks), listStocks)

for comp in listStocks:
    print(increment())

    try:
        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)

        if marketPrice < 1:
            print(comp, "cent stock", marketPrice)
            continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        cash = getFromDF(bs.loc['cash']) if 'cash' in bs.index else 0.0
        if cash == 0:
            print(comp, 'cash is 0 ')
            continue

        currentAssets = getFromDF(bs.loc["totalCurrentAssets"]) if 'totalCurrentAssets' in bs.index else 0.0

        totalLiab = getFromDF(bs.loc["totalLiab"]) if 'totalLiab' in bs.index else 0.0

        if currentAssets < totalLiab:
            print(comp, " current assets < total liab", round(currentAssets / 1000000000, 2),
                  round(totalLiab / 1000000000, 2))
            continue

        receivables = getFromDF(bs.loc['netReceivables']) if 'netReceivables' in bs.index else 0.0
        inventory = getFromDF(bs.loc['inventory']) if 'inventory' in bs.index else 0.0

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
                print(comp, "HK market cap less than 1B", marketCap/1000000000)
                continue


        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if (cash + receivables + inventory - totalLiab) / exRate < marketCap:
            print(comp, listingCurr, bsCurr,
                  'cash + rec + inventory - total liab < mv. cash rec inv Liab MV:',
                  round(cash / 1000000000, 2),
                  round(receivables / 1000000000, 2),
                  round(inventory / 1000000000, 2),
                  round(totalLiab / 1000000000, 2),
                  round(marketCap / 1000000000, 2))
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
                       + " cash:" + str(round(cash / 1000000000, 2)) \
                       + " rec:" + str(round(receivables / 1000000000, 2)) \
                       + " inv:" + str(round(inventory / 1000000000, 2)) \
                       + " CA:" + str(round(currentAssets / 1000000000, 2)) \
                       + " L:" + str(round(totalLiab / 1000000000, 2)) \
                       + " mv:" + str(round(marketCap / 1000000000, 2)) \
                       + additionalComment

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
