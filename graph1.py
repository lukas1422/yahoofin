import math
import os
import sys
from datetime import datetime

import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, Paragraph, FactorRange, LabelSet, Div
from helperMethods import fill0Get, indicatorFunction, roundB, roundBString, getFromDF, fill0GetLatest
from scrape_sharesOutstanding import scrapeTotalSharesXueqiu
import yfinance as yf

ANNUALLY = True
FIRST_TIME_GRAPHING = True
# SIMPLE = False

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
import currency_getExchangeRate
from currency_scrapeYahoo import getListingCurrency, getBalanceSheetCurrency
import pandas as pd

pd.set_option('display.expand_frame_repr', False)

HALF_YEAR_WIDE = 15552000000

TICKER = '0001.HK'
stockYF = yf.Ticker(TICKER)

global_source = ColumnDataSource(pd.DataFrame())
stockData = ColumnDataSource(pd.DataFrame())
divPriceData = ColumnDataSource(pd.DataFrame())
bsCurrOverride = ''


def getWidthDivGraph():
    if 'year' not in divPriceData.data:
        # print('getwidthdiv year not in data yet')
        return 0

    return 0.8


def my_text_input_handler(attr, old, new):
    global TICKER

    if str.isdigit(new):
        TICKER = new.zfill(4) + '.HK'
    else:
        TICKER = new.upper()

    print('new ticker is ', TICKER)


def bsCurrOverride_handler(attr, old, new):
    global bsCurrOverride
    bsCurrOverride = new.upper()


# infoParagraph = Paragraph(width=30, text='Blank')
# infoParagraph = Paragraph(width=1000, height=500, text='Blank')
statusInfo = Div(text='status')

otherInfo = Div(text='initial text')

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    # infoParagraph.text = ""
    text_input.title = ''
    # gPrice.title.text = ''
    print('cleared source')


def buttonCallback():
    try:
        # print(' new ticker is ', TICKER)
        # print('annual is ', ANNUALLY)

        statusInfo.text = "status is running"
        stockYF = yf.Ticker(TICKER)

        try:
            listCurr = getListingCurrency(TICKER)
            # print('listCurr is ', listCurr)
            bsCurr = bsCurrOverride if bsCurrOverride != '' else getBalanceSheetCurrency(TICKER, listCurr)
            # print("ticker, listing currency, bs currency, ", TICKER, listCurr, bsCurr)
            exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listCurr, bsCurr)
            # statusInfo.text += 'exRate is ' + exRate + '</br>'

        except Exception as e:
            print(e)
            statusInfo.text = 'error ' + str(e)
        # try:
        #     # info = si.get_company_info(TICKER)
        #     #info = stockYF.info
        #
        #     # infoText = info['country'] + "______________" + info['industry'] + \
        #     #            '______________' + info['sector'] + "______________" + info[
        #     #                'longBusinessSummary']
        # except Exception as e:
        #     print(e)
        #     info = ''
        #     infoText = ''

        # print('info text is ', infoText)
        # infoParagraph.text = str(infoText)

        # infoParagraph.text = info['country'] + '\n' + info['industry'] + \
        #                      '\n' + info['sector'] + '\n' + info['longBusinessSummary']
        # # priceData = si.get_data(TICKER)
        # priceData.index.name = 'date'

        priceData = stockYF.history(period='max')
        priceData = priceData.set_index(priceData.index.map(lambda x: x.replace(tzinfo=None).to_pydatetime()))

        oneYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-250:])) /
                                  (max(priceData['High'][-250:]) - min(priceData['Low'][-250:])))

        twoYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-500:])) /
                                  (max(priceData['High'][-500:]) - min(priceData['Low'][-500:])))

        threeYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-750:])) /
                                    (max(priceData['High'][-750:]) - min(priceData['Low'][-750:])))

        # print("1 2 3 percentile", oneYearPercentile, twoYearPercentile, threeYearPercentile)

        # divData = si.get_dividends(TICKER)
        divData = stockYF.dividends.to_frame()
        divPrice = pd.DataFrame()

        # print('divdata', divData)

        if not divData.empty:
            # divData.groupby(by=lambda a: a.year)['dividend'].sum()
            divPrice = pd.merge(divData.groupby(by=lambda d: d.year)['Dividends'].sum(),
                                priceData.groupby(by=lambda d: d.year)['Close'].mean(),
                                left_index=True, right_index=True)
            # print('divprice1', divPrice)
            divPrice.index.name = 'year'
            divPrice['yield'] = divPrice['Dividends'] / divPrice['Close'] * 100
            divPrice['yieldText'] = divPrice['yield'].transform(lambda x: str(round(x)))
            # print('divprice2', divPrice)
            divPriceData.data = ColumnDataSource.from_df(divPrice)

        # latestPrice = si.get_live_price(TICKER)
        info = stockYF.info
        fast_info = stockYF.fast_info
        latestPrice = fast_info['last_price'] if 'last_price' in fast_info else 0

        # bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
        bs = stockYF.balance_sheet
        bsT = bs.T
        bsT['REAssetsRatio'] = bsT['Retained Earnings'] / bsT['Total Assets'] if 'Retained Earnings' in bsT else 0
        bsT['REAssetsRatioText'] = bsT['REAssetsRatio'].transform(lambda x: str(round(x, 1)))

        # if 'Current Liabilities' in bsT.index:
        if 'Current Liabilities' in bsT.columns:
            bsT['currentRatio'] = (fill0Get(bsT, 'Cash And Cash Equivalents') + 0.8 * fill0Get(bsT,
                                                                                               'Accounts Receivable') +
                                   0.5 * fill0Get(bsT, 'Inventory')) / bsT['Current Liabilities']
        else:
            bsT['currentRatio'] = 0

        bsT['currentRatioText'] = bsT['currentRatio'].transform(lambda x: str(round(x, 0)))

        bsT['grossBook'] = bsT['Total Assets'] - bsT['Total Liabilities Net Minority Interest'] \
            if 'Total Liabilities Net Minority Interest' in bsT else 0
        bsT['grossBookB'] = bsT['Stockholders Equity'] / 1000000000 if 'Stockholders Equity' in bsT else 0

        bsT['netBook'] = bsT['Total Assets'] - bsT['Total Liabilities Net Minority Interest'] \
                         - fill0Get(bsT, 'Goodwill') \
                         - fill0Get(bsT, 'Other Intangible Assets')

        bsT['netBook'] = bsT['netBook'].transform(lambda x: x if x > 0 else 0)

        # bsT['noncashAssets'] = bsT['netBook'] - bsT['cash']
        bsT['tangibleRatio'] = bsT['netBook'] / (bsT['Total Assets'] -
                                                 bsT['Total Liabilities Net Minority Interest'])
        bsT['tangibleRatioText'] = bsT['tangibleRatio'].transform(lambda x: str(round(x, 1)))

        # bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook'] if bsT['netBook'] != 0 else 0

        # bsT['DERatio'] = bsT['Total Liabilities Net Minority Interest'].div(bsT['netBook']).replace(np.inf, 0)

        bsT['DERatio'] = bsT['Total Liabilities Net Minority Interest'] \
            .div(bsT['Total Assets'] - bsT['Total Liabilities Net Minority Interest'])

        bsT['DERatioText'] = bsT['DERatio'].transform(lambda x: str(round(x, 1)) if x != 0 else 'undef')

        bsT['priceOnOrAfter'] = bsT.index.map(lambda d: priceData[priceData.index >= d].iloc[0]['Close'])
        # bsT['priceOnOrAfter'][0] = latestPrice
        bsT['currentAssets'] = \
            bsT['Cash And Cash Equivalents'] + fill0Get(bsT, 'Accounts Receivable') + fill0Get(bsT, 'Inventory')
        bsT['noncashCurrentAssets'] = bsT['Current Assets'] - bsT['Cash And Cash Equivalents'] \
            if 'Current Assets' in bsT else 0
        bsT['nonCurrentAssets'] = bsT['Total Assets'] - bsT['Current Assets'] \
            if 'Total Assets' in bsT and 'Current Assets' in bsT else 0
        bsT['noncashCurrentAssetsB'] = bsT['noncashCurrentAssets'] / 1000000000 if 'noncashCurrentAssets' in bsT else 0
        bsT['nonCurrentAssetsB'] = bsT['nonCurrentAssets'] / 1000000000 if 'nonCurrentAssets' in bsT else 0

        bsT['totalLiabB'] = bsT['Total Liabilities Net Minority Interest'] / 1000000000 \
            if 'Total Liabilities Net Minority Interest' in bsT else 0
        bsT['totalAssetsB'] = bsT['Total Assets'] / 1000000000 if 'Total Assets' in bsT else 0
        bsT['totalCurrentLiabB'] = bsT['Current Liabilities'] / 1000000000 \
            if 'Current Liabilities' in bsT else 0

        bsT['totalNoncurrentLiab'] = bsT['Total Liabilities Net Minority Interest'] - bsT['Current Liabilities'] if \
            'Current Liabilities' in bsT and 'Total Liabilities Net Minority Interest' in bsT else 0
        bsT['totalNoncurrentLiabB'] = bsT['totalNoncurrentLiab'] / 1000000000
        bsT['goodWillB'] = bsT['Goodwill'] / 1000000000 if 'GoodWill' in bsT else 0
        bsT['intangibleAssetsB'] = bsT['Other Intangible Assets'] / 1000000000 \
            if 'Other Intangible Assets' in bsT else 0

        # print('bsT current assets', bsT['cash'], bsT['netReceivables'], bsT['inventory'])
        # shares = si.get_quote_data(TICKER)['sharesOutstanding']

        if TICKER.upper().endswith("HK") and bsCurr == 'CNY':
            shares = scrapeTotalSharesXueqiu(TICKER)
            print('using xueqiu total shares for china', TICKER, shares)

        # bsT['marketCap'] = bsT['priceOnOrAfter'] * shares
        # quoteData = si.get_quote_data(TICKER)
        # marketCapLast = quoteData['marketCap'] if 'marketCap' in quoteData else 0

        marketCapLast = stockYF.fast_info['market_cap']

        # progress
        #######################

        shares = marketCapLast / latestPrice
        # print(TICKER, 'shares', shares)
        bsT['marketCap'] = bsT['priceOnOrAfter'] * shares

        # print('shares ', shares, 'mktCap last', marketCapLast)
        bsT['marketCapB'] = bsT['marketCap'] / 1000000000
        bsT['marketCapBText'] = bsT['marketCapB'].transform(lambda x: str(round(x)))

        # bsT['marketCap'] = si.get_quote_data(TICKER)['marketcap']
        # bsT['PB'] = bsT['marketCap'] * exRate / bsT['netBook'] if bsT['netBook'] != 0 else 0
        bsT['PB'] = bsT['marketCap'].div(bsT['netBook']).replace(np.inf, 0) * exRate
        bsT['PBText'] = bsT['PB'].transform(lambda x: str(round(x, 1)) if x != 0 else 'undef')

        totalAssets = getFromDF(bs, "Total Assets")
        totalCurrentAssets = getFromDF(bs, "Current Assets")
        currLiab = getFromDF(bs, "Current Liabilities")
        totalLiab = getFromDF(bs, "Total Liabilities Net Minority Interest")
        intangibles = getFromDF(bs, 'Other Intangible Assets')
        goodWill = getFromDF(bs, 'Goodwill')
        tangible_equity = totalAssets - totalLiab - goodWill - intangibles

        # income = si.get_income_statement(TICKER, yearly=ANNUALLY)
        income = stockYF.income_stmt

        incomeT = income.T
        # bsT['revenue'] = bsT.index.map(
        #     lambda d: incomeT[incomeT.index == d]['Total Revenue'].item() * indicatorFunction(ANNUALLY))
        # bsT['netIncome'] = bsT.index.map(
        #     lambda d: incomeT[incomeT.index == d]['Net Income'].item() * indicatorFunction(ANNUALLY))

        bsT['revenue'] = bsT.index.map(
            lambda d: incomeT[incomeT.index == d]['Total Revenue'].item() if d in incomeT.index else 0)
        bsT['netIncome'] = bsT.index.map(
            lambda d: incomeT[incomeT.index == d]['Net Income'].item() if d in incomeT.index else 0)
        # bsT = bsT.merge(incomeT['Total Revenue'], left_index=True, right_index=True, how='outer').fillna(0)
        # bsT = bsT.merge(incomeT['Net Income'], left_index=True, right_index=True, how='outer').fillna(0)
        # bsT['netIncome'] = bsT['Net Income']
        # bsT['revenue'] = bsT['Total Revenue']

        bsT['netIncomeB'] = bsT['netIncome'] / 1000000000
        bsT['netIncomeBText'] = bsT['netIncomeB'].transform(lambda x: str(round(x)))

        bsT['PE'] = bsT['marketCap'] * exRate / bsT['netIncome']
        bsT['PE'] = bsT['PE'].transform(lambda x: x if x > 0 and not math.isinf(x) else 0)
        # print('bstPE', bsT['PE'])
        bsT['PEText'] = bsT['PE'].transform(lambda x: str(round(x)) if x != 0 else 'undef')

        bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['Total Assets']
        bsT['SalesAssetsRatioText'] = bsT['SalesAssetsRatio'].transform(lambda x: str(round(x, 1)))

        bsT['PriceSalesRatio'] = (bsT['marketCap'] * exRate) / bsT['revenue']
        bsT['PriceSalesRatioText'] = bsT['PriceSalesRatio'].transform(lambda x: str(round(x, 1)))

        # print('pb', bsT['PB'])
        # print('rev', bsT['revenue'])

        bsT['pspb'] = (bsT['marketCap'] * exRate) / bsT['revenue'] * bsT['PB'] * 10000
        bsT['pspb'] = bsT['pspb'].transform(lambda x: 0 if math.isinf(x) or math.isnan(x) else x)

        bsT['pspbText'] = bsT['pspb'].transform(lambda x: str(round(x)))

        bsT['liq'] = bsT['Cash And Cash Equivalents'] + fill0Get(bsT, 'Accounts Receivable') * 0.8 \
                     + fill0Get(bsT, 'Inventory') * 0.5 - bsT['Total Liabilities Net Minority Interest']

        # print('bst liq', bsT['liq'])

        # bsT['liq'] = bsT['liq'].transform(lambda x: 0 if x < 0 else x)

        bsT['pspliq'] = bsT['marketCap'] * bsT['marketCap'] * (exRate ** 2) \
                        / bsT['revenue'] / bsT['liq'] * 10000

        bsT['pspliq'] = bsT['pspliq'] \
            .transform(lambda x: 0 if (x < 0 or math.isinf(x) or math.isnan(x)) else x)

        # print('print pspliq', bsT['pspliq'])
        bsT['pspliqText'] = bsT['pspliq'].transform(lambda x: str(round(x)))

        # cf = si.get_cash_flow(TICKER, yearly=ANNUALLY)
        cf = stockYF.cashflow
        cfT = cf.T

        bsT['CFO'] = bsT.index.map(
            lambda d: cfT[cfT.index == d]['Operating Cash Flow'].item() * indicatorFunction(
                ANNUALLY) if d in cfT.index else 0)

        if 'Depreciation' in cf.index:
            bsT['dep'] = bsT.index.map(
                lambda d: cfT[cfT.index == d]['Depreciation'].item() * indicatorFunction(ANNUALLY)
                if d in cfT.index else 0)
        else:
            bsT['dep'] = 0

        bsT['capex'] = bsT.index.map(
            lambda d: cfT[cfT.index == d]['Capital Expenditure'].item() * -1 * indicatorFunction(ANNUALLY)
            if d in cfT.index else 0) if 'Capital Expenditure' in cfT else 0

        bsT['FCF'] = bsT['CFO'] - bsT['dep']

        bsT['CFOB'] = bsT['CFO'] / 1000000000
        # print('cfo', bsT['CFOB'])
        bsT['CFOBText'] = bsT['CFOB'].fillna(0).transform(lambda x: str(round(x)))

        bsT['FCFB'] = bsT['FCF'] / 1000000000
        bsT['FCFBText'] = bsT['FCFB'].fillna(0).transform(lambda x: str(round(x)))

        bsT['PFCF'] = bsT['marketCap'] * exRate / bsT['FCF']
        # print('PFCF', bsT['PFCF'])
        bsT['PFCF'] = bsT['PFCF'].transform(lambda x: x if x > 0 or math.isinf(x) else 0)
        bsT['PFCFText'] = bsT['PFCF'].fillna(0).transform(
            lambda x: str(round(x)) if x != 0 and not math.isinf(x) else 'undef')

        # print('fcf', bsT['FCF'])
        # print('pfcf', bsT['PFCF'])

        bsT['DepCFO'] = bsT['dep'] / bsT['CFO']

        bsT['CapexCFO'] = bsT['capex'] / bsT['CFO']

        bsT['DepCFO'] = bsT['DepCFO'].transform(lambda x: x if x > 0 else 0)
        bsT['CapexCFO'] = bsT['CapexCFO'].transform(lambda x: x if x > 0 else 0)

        bsT['DepCFOText'] = bsT['DepCFO'].transform(lambda x: str(round(x, 1)))
        bsT['CapexCFOText'] = bsT['CapexCFO'].transform(lambda x: str(round(x, 1)))

        bsT['payAllDebtRatio'] = (bsT['Cash And Cash Equivalents']
                                  + fill0Get(bsT, 'Accounts Receivable') * 0.8 +
                                  fill0Get(bsT, 'Inventory') * 0.5) \
                                 / bsT['Total Liabilities Net Minority Interest']
        bsT['payAllDebtText'] = bsT['payAllDebtRatio'].transform(lambda x: str(round(x, 1)))

        bsT['netnetRatio'] = ((bsT['Cash And Cash Equivalents'] + fill0Get(bsT, 'Accounts Receivable') * 0.8 +
                               fill0Get(bsT, 'Inventory') * 0.5) / (bsT['Total Liabilities Net Minority Interest']
                                                                    + exRate * bsT['marketCap']))
        bsT['nnrText'] = bsT['netnetRatio'].transform(lambda x: str(round(x, 1)))
        bsT['FCFAssetRatio'] = bsT['FCF'] / bsT['Total Assets']
        bsT['FCFAssetRatioText'] = bsT['FCFAssetRatio'].transform(lambda x: str(round(x, 1)))

        bsT['dateStr'] = pd.to_datetime(bsT.index)
        bsT['dateStr'] = bsT['dateStr'].transform(lambda x: x.strftime('%Y-%m-%d'))

        # print('cash ', bsT['Cash And Cash Equivalents'])
        bsT['cashB'] = round(bsT['Cash And Cash Equivalents'].astype(float) / 1000000000, 3) \
            if 'Cash And Cash Equivalents' in bsT else 0
        bsT['cashBText'] = bsT['cashB'].fillna(0).transform(lambda x: str(round(x, 1))) if 'cashB' in bsT else ''

        bsT['netReceivablesB'] = bsT['Accounts Receivable'] / 1000000000 if 'Accounts Receivable' in bsT else 0
        bsT['inventoryB'] = bsT['Inventory'] / 1000000000 if 'Inventory' in bsT else 0
        bsT['netBookB'] = bsT['netBook'] / 1000000000 if 'netBook' in bsT else 0
        # print('intang', bsT['intangibleAssetsB'])
        bsT['bookAllB'] = bsT['netBookB'] + bsT['goodWillB'] + bsT['intangibleAssetsB']
        # print('bookallb', bsT['bookAllB'], bsT['bookAllB'].fillna(0))
        bsT['bookAllBText'] = bsT['bookAllB'].fillna(0).transform(lambda x: str(round(x, 1))) \
            if 'bookAllB' in bsT else ''

        # ['netBookB', 'goodWillB', 'intangibleAssetsB']
        # bsT['noncashAssetsB'] = bsT['noncashAssets'] / 1000000000 if 'noncashAssets' in bsT else 0

        global_source.data = ColumnDataSource.from_df(bsT)
        stockData.data = ColumnDataSource.from_df(priceData)

        latestLiqRatio = (bsT['Cash And Cash Equivalents'][0] + fill0GetLatest(bsT, 'Accounts Receivable') * 0.8 +
                          fill0GetLatest(bsT, 'Inventory') * 0.5) \
                         / bsT['Total Liabilities Net Minority Interest'][0]

        latestNetnetRatio = (bsT['Cash And Cash Equivalents'][0] + fill0GetLatest(bsT, 'Accounts Receivable') * 0.8 +
                             fill0GetLatest(bsT, 'Inventory') * 0.5) / \
                            (bsT['Total Liabilities Net Minority Interest'][0] + exRate * marketCapLast)

        # print("latest netnet ratio", latestNetnetRatio, 'cash', bsT['cash'][0], 'rec', fill0GetLatest(bsT, 'netReceivables')
        #       , 'inv', fill0GetLatest(bsT, 'inventory'), 'totalliab', bsT['totalLiab'][0], 'exrate', exRate,
        #       'marketcaplast', marketCapLast)

        yearsListed = datetime.now().year - priceData.index[0].year
        listYear = priceData.index[0].year

        yearSpan = 2021 - priceData[:1].index.item().year + 1
        # print(divData)
        # print('year span', yearSpan)
        # print('divPrice', divPrice)
        divYieldAll = divPrice[divPrice.index != 2022]['yield'].sum() / yearSpan \
            if not divPrice[divPrice.index != 2022].empty else 0
        divYield2021 = divPrice.loc[2021]['yield'] if 2021 in divPrice.index else 0

        print("=============work now===============")

        # updateGraphs()
        # print('pfcf info marketcap, exrate, lastfcf', marketCapLast, exRate, bsT['FCF'][0])
        try:
            compName1 = info['longBusinessSummary'].split(' ')[0] \
                if 'longBusinessSummary' in info.keys() and len(info) != 0 else ""
            compName2 = info['longBusinessSummary'].split(' ')[1] \
                if 'longBusinessSummary' in info.keys() and len(info) != 0 else ""
        # print(' comp name ', compName1, compName2, 'summary', info.loc['longBusinessSummary'].item().split(' '))
        except Exception as e:
            print('comp name fail exception:', e)
            compName1 = ''
            compName2 = ''

        # text_input.title = compName1 + ' ' + compName2 + ' '
        # + '#:' + str(roundB(shares, 1)) + 'B ' \
        # + listCurr + bsCurr + '__MV:' + str(roundB(marketCapLast, 1)) + 'B' \
        # + "__NetB:" + str(roundB(bsT['netBook'][0] / exRate, 1)) + 'B' \
        # + "__liqR:" + str(round(latestLiqRatio, 1)) \
        # + "__nnR:" + str(round(latestNetnetRatio, 1)) \
        # + '__PS:' + (str(round(marketCapLast * exRate / bsT['revenue'][0], 1))
        #              if bsT['revenue'][0] != 0 else "na") \
        # + '__PB:' + str(round(marketCapLast * exRate / tangible_equity, 1)) \
        # + '__CR:' + str(round(bsT['currentRatio'][0], 1)) \
        # + '__DE:' + str(round(bsT['DERatio'][0], 1)) \
        # + '__RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
        # + '__P/FCF:' + (str(round(marketCapLast * exRate / bsT['FCF'][0], 1))
        #                 if bsT['FCF'][0] > 0 else 'undef') \
        # + '__Div:' + (str(round(divYieldAll)) if 'yield' in divPrice else '') + '%' \
        # + '__2021Div:' \
        # + (str(round(divYield2021))) + '%' \
        # + '__p%:' + str(oneYearPercentile) + ' ' + str(twoYearPercentile) + ' ' \
        # + str(threeYearPercentile) + '_list:' + str(listYear)
        # if not SIMPLE:
        otherInfo.text = compName1 + ' ' + compName2 + '___#Shs:' + str(roundB(shares, 1)) + 'B ' + listCurr + bsCurr \
                         + '</br>' + 'MV:' + str(roundB(marketCapLast, 0)) + 'B' + '</br>' \
                         + "BV:" + str(roundB(bsT['netBook'][0] / exRate, 0)) + 'B' \
                         + '</br>' + "liqR:" + str(round(latestLiqRatio, 1)) \
                         + "___nnR:" + str(round(latestNetnetRatio, 1)) \
                         + '</br>' + 'PS:' + (str(round(marketCapLast * exRate / bsT['revenue'][0], 1))
                                              if bsT['revenue'][0] != 0 else "na") \
                         + '___PB:' + str(round(marketCapLast * exRate / tangible_equity, 1)) \
                         + '</br>' + 'CR:' + str(round(bsT['currentRatio'][0], 1)) \
                         + '___DE:' + str(round(bsT['DERatio'][0], 1)) \
                         + '</br>' + 'RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
                         + '___P/FCF:' + (str(round(marketCapLast * exRate / bsT['FCF'][0], 1))
                                          if bsT['FCF'][0] > 0 else 'undef') \
                         + '</br>' + 'Div:' + (str(round(divYieldAll)) if 'yield' in divPrice else '') + '%' \
                         + '___2021Div:' \
                         + (str(round(divYield2021))) + '%' \
                         + '</br>' + 'p%:' + str(oneYearPercentile) + ' ' + str(twoYearPercentile) + ' ' \
                         + str(threeYearPercentile) + '___list:' + str(listYear)
        otherInfo.text += '</br>' + "***Financials***" + bsCurr + '</br>' + ' '.join(["csh",
                                                                                      roundBString(getFromDF(bs,
                                                                                                             'Cash And Cash Equivalents'),
                                                                                                   1), 'rec',
                                                                                      roundBString(
                                                                                          getFromDF(bs,
                                                                                                    'Accounts Receivable'),
                                                                                          1),
                                                                                      'inv',
                                                                                      roundBString(
                                                                                          getFromDF(bs, 'Inventory'),
                                                                                          1), ])
        otherInfo.text += '</br>' + ' '.join(['currL', roundBString(getFromDF(bs, 'Current Liabilities'), 1)])

        otherInfo.text += '</br>' + ' '.join(["A", roundBString(totalAssets / exRate, 1), "B", "(",
                                              roundBString(totalCurrentAssets / exRate, 1), ' '
                                                 , roundBString((totalAssets - totalCurrentAssets) / exRate, 1),
                                              ")"])
        otherInfo.text += '</br>' + ' '.join(["L", roundBString(totalLiab / exRate, 1), "B", "(",
                                              roundBString(currLiab / exRate, 1), ' ',
                                              roundBString((totalLiab - currLiab) / exRate, 1), ")"])
        otherInfo.text += '</br>' + ' '.join(["E", roundBString((totalAssets - totalLiab) / exRate, 1), "B"])
        otherInfo.text += '</br>' + ''.join(["Eq:", roundBString(tangible_equity, 1), 'B  ', bsCurr,
                                             roundBString(tangible_equity / exRate, 1), 'B  ', listCurr])

        # otherInfo.text += '</br>' + ("Market Cap", str(roundB(marketPrice * shares, 2)) + "B", listCurr)
        # divPrice['yield'].iloc[-1]

        statusInfo.text = datetime.now().strftime('%H:%M:%S') + ' status is done' + '</br>'

        print("=============work finished===============")
        global text_input
        text_input.value = ''

    except Exception as e:
        print(' big error is ', e)
        statusInfo.text = datetime.now().strftime('%H:%M:%S') + " big error is " + str(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


text_input = TextInput(value="0001.HK")
text_input.on_change("value", my_text_input_handler)

bsCurrInput = TextInput(value="")
bsCurrInput.title = 'Currency Override'
bsCurrInput.on_change("value", bsCurrOverride_handler)

button = Button(label="Get Data")
button.on_click(buttonCallback)

# button2 = Button(label='Reset')
# button2.on_click(resetCallback)

# def my_radio_handler(new):
#     global ANNUALLY
#     ANNUALLY = True if new == 0 else False
#     print('ANNUAL IS', ANNUALLY)
#     resetCallback()
#
#
# def complexHandler(new):
#     global SIMPLE
#     SIMPLE = True if new == 0 else False
#     print('simple is', SIMPLE)
#     resetCallback()


# rg = RadioGroup(labels=['Annual', 'Quarterly'], active=0)
# rg.on_click(my_radio_handler)
# rgComplex = RadioGroup(labels=['simple', 'full'], active=1)
# rgComplex.on_click(complexHandler)

# curdoc().add_root(column(button, button2, statusInfo, text_input, otherInfo, infoParagraph))
curdoc().add_root(column(button, text_input, bsCurrInput, otherInfo, statusInfo))
