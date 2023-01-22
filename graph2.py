import math
import os
import sys
from datetime import datetime
from math import pi

import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, Paragraph, FactorRange, LabelSet, Div
from helperMethods import fill0Get, indicatorFunction, roundB, roundBString, getFromDF, fill0GetLatest
from scrape_sharesOutstanding import scrapeTotalSharesXueqiu
import yfinance as yf

ANNUALLY = True
FIRST_TIME_GRAPHING = True
SIMPLE = False

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
# import yahoo_fin.stock_info as si
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


infoParagraph = Paragraph(width=1000, text='Blank')
# infoParagraph = Paragraph(width=1000, height=500, text='Blank')
statusInfo = Div(text='status')

otherInfo = Div(text='initial text')

# lastTradingPrice = si.get_live_price(TICKER)
lastTradingPrice = stockYF.info['currentPrice']

# price chart
gPrice = figure(title='prices chart', width=1000, x_axis_type="datetime")
gPrice.xaxis.major_label_orientation = pi / 4
gPrice.grid.grid_line_alpha = 0.3
gPrice.add_tools(HoverTool(tooltips=[('Date', '@Date{%Y-%m-%d}'), ('Close', '@Close{0.0}')],
                           formatters={'@Date': 'datetime'}, mode='vline'))

# priceChart.background_fill_color = "#f5f5f5"
gDiv = figure(title="divYld", width=1000)
gDiv.add_tools(HoverTool(tooltips=[('year', '@year'), ("yield", "@yield{0.0}")], mode='vline'))

gMarketcap = figure(title='cap(B)', x_range=FactorRange(factors=list()))
gMarketcap.title.text = 'cap(B) '
gMarketcap.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("marketCap", "@marketCapB{0.0}")], mode='vline'))

gCash = figure(title='cash(B)', x_range=FactorRange(factors=list()))
gCash.title.text = 'cash(B) '
gCash.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("cash", "@cashB{0.0}")], mode='vline'))

gCurrentAssets = figure(title='currentAssets', x_range=FactorRange(factors=list()),
                        tools="hover", tooltips="$name @dateStr: @$name{0.0}")
gCurrentAssets.title.text = 'currentAssets'
# gCurrentAssets.legend.orientation = "horizontal"
# gCurrentAssets.legend.location = "top_center"

gAssetComposition = figure(title='Assets compo', x_range=FactorRange(factors=list()),
                           tools="hover", tooltips="$name @dateStr: @$name{0.0}")
gAssetComposition.title.text = 'Assets compo'

gALE = figure(title='ALE', x_range=FactorRange(factors=list()), tools="hover", tooltips="$name @dateStr: @$name{0.0}")
gALE.title.text = 'ALE'

gBook = figure(title='book(B)', x_range=FactorRange(factors=list()),
               tools="hover", tooltips="$name @dateStr: @$name{0.0}")
gBook.title.text = 'Book(B)'
# gBook.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("bookB", "@netBookB")], mode='vline'))

gTangibleRatio = figure(title='Tangible Ratio', x_range=FactorRange(factors=list()))
gTangibleRatio.title.text = 'Tangible Ratio'
gTangibleRatio.add_tools(
    HoverTool(tooltips=[('dateStr', '@dateStr'), ("tangibleRatio", "@tangibleRatio{0.0}")], mode='vline'))

gCurrentRatio = figure(title='currentRatio', x_range=FactorRange(factors=list()))
gRetainedEarnings = figure(title='RetEarnings/A', x_range=FactorRange(factors=list()))
gDE = figure(title='D/E Ratio', x_range=FactorRange(factors=list()))
gPB = figure(title='P/B Ratio', x_range=FactorRange(factors=list()))
gEarnings = figure(title='Earnings(B)', x_range=FactorRange(factors=list()))
gPE = figure(title='P/E', x_range=FactorRange(factors=list()))
gCFO = figure(title='CFO(B)', x_range=FactorRange(factors=list()))
gFCF = figure(title='FCF(B)', x_range=FactorRange(factors=list()))
gPFCF = figure(title='P/FCF', x_range=FactorRange(factors=list()))
gDepCFO = figure(title='Dep/CFO', x_range=FactorRange(factors=list()))
gCapexCFO = figure(title='Capex/CFO', x_range=FactorRange(factors=list()))
gSA = figure(title='Sales/Assets Ratio', x_range=FactorRange(factors=list()))
gPS = figure(title='Price/Sales Ratio', x_range=FactorRange(factors=list()))
gNetnet = figure(title='netnet Ratio', x_range=FactorRange(factors=list()))
gPayAllDebt = figure(title='payAllDebt Ratio', x_range=FactorRange(factors=list()))
gFCFA = figure(title='FCF/A Ratio', x_range=FactorRange(factors=list()))
gPSPB = figure(title='PSPB', x_range=FactorRange(factors=list()))
gPSPLiq = figure(title='PSPLiq', x_range=FactorRange(factors=list()))

gCurrentRatio.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("cr", "@currentRatio{0.0}")], mode='vline'))
gRetainedEarnings.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("Re/A", "@REAssetsRatio{0.0}")], mode='vline'))
gDE.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("DERatio", "@DERatio{0.0}")], mode='vline'))
gPB.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PB", "@PB{0.0}")], mode='vline'))
gEarnings.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("netIncomeB", "@netIncomeB{0.0}")], mode='vline'))
gPE.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PE", "@PE{0.0}")], mode='vline'))
gCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("CFOB", "@CFOB{0.0}")], mode='vline'))
gFCF.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("FCFB", "@FCFB{0.0}")], mode='vline'))
gPFCF.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PFCF", "@PFCF{0.0}")], mode='vline'))
gDepCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("DepCFO", "@DepCFO{0.0}")], mode='vline'))
gCapexCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("CapexCFO", "@CapexCFO{0.0}")], mode='vline'))
gSA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("S/A Ratio", "@SalesAssetsRatio{0.0}")], mode='vline'))
gPS.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("P/S Ratio", "@PriceSalesRatio{0.0}")], mode='vline'))
gNetnet.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("netnet", "@netnetRatio{0.0}")], mode='vline'))
gPayAllDebt.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("payAllDebt", "@payAllDebtRatio{0.0}")], mode='vline'))
gFCFA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("FCF/A", "@FCFAssetRatio{0.0}")], mode='vline'))
gPSPB.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("pspb", "@pspb{0.0}")], mode='vline'))
gPSPLiq.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("pspliq", "@pspliq{0.0}")], mode='vline'))

for figu in [gPrice, gMarketcap, gCash, gCurrentAssets, gAssetComposition, gALE, gBook, gTangibleRatio,
             gDiv, gCurrentRatio, gRetainedEarnings, gDE, gPB, gEarnings, gPE, gCFO, gFCF, gPFCF, gDepCFO,
             gCapexCFO, gSA, gPS, gNetnet, gPayAllDebt, gFCFA, gPSPB, gPSPLiq]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'

grid = gridplot(
    [[gRetainedEarnings, gDE], [gCurrentRatio, gNetnet], [gPB, gPS], [gPSPB, gPSPLiq],
     [gCash, gCurrentAssets], [gAssetComposition, gALE], [gBook, gTangibleRatio]
        , [gMarketcap, gSA], [gCFO, gFCF], [gPFCF, gFCFA],
     [gEarnings, gPE], [gDepCFO, gCapexCFO], [gPayAllDebt, None]], width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    infoParagraph.text = ""
    text_input.title = ''
    gPrice.title.text = ''
    print('cleared source')


def buttonCallback():
    try:
        print(' new ticker is ', TICKER)
        print('annual is ', ANNUALLY)

        statusInfo.text = "status is running"
        stockYF = yf.Ticker(TICKER)

        try:
            listCurr = getListingCurrency(TICKER)
            print('listCurr is ', listCurr)
            bsCurr = getBalanceSheetCurrency(TICKER, listCurr)
            print("ticker, listing currency, bs currency, ", TICKER, listCurr, bsCurr)
            exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listCurr, bsCurr)
            # statusInfo.text += 'exRate is ' + exRate + '</br>'

        except Exception as e:
            print(e)
            statusInfo.text = 'error ' + str(e)
        try:
            # info = si.get_company_info(TICKER)
            info = stockYF.info

            infoText = info['country'] + "______________" + info['industry'] + \
                       '______________' + info['sector'] + "______________" + info[
                           'longBusinessSummary']
        except Exception as e:
            print(e)
            info = ''
            infoText = ''

        print('info text is ', infoText)
        infoParagraph.text = str(infoText)

        # priceData = si.get_data(TICKER)
        # priceData.index.name = 'date'

        priceData = stockYF.history(period='max')
        priceData = priceData.set_index(priceData.index.map(lambda x: x.replace(tzinfo=None).to_pydatetime()))

        oneYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-250:])) /
                                  (max(priceData['High'][-250:]) - min(priceData['Low'][-250:])))

        twoYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-500:])) /
                                  (max(priceData['High'][-500:]) - min(priceData['Low'][-500:])))

        threeYearPercentile = round(100 * (priceData['Close'][-1] - min(priceData['Low'][-750:])) /
                                    (max(priceData['High'][-750:]) - min(priceData['Low'][-750:])))

        print("1 2 3 percentile", oneYearPercentile, twoYearPercentile, threeYearPercentile)

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
        latestPrice = info['currentPrice'] if 'currentPrice' in info else 0

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

        marketCapLast = stockYF.info['marketCap']

        # progress
        #######################

        shares = marketCapLast / latestPrice
        # print(TICKER, 'shares', shares)
        bsT['marketCap'] = bsT['priceOnOrAfter'] * shares

        print('shares ', shares, 'mktCap last', marketCapLast)
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
        bsT['revenue'] = bsT.index.map(
            lambda d: incomeT[incomeT.index == d]['Total Revenue'].item() * indicatorFunction(ANNUALLY))
        bsT['netIncome'] = bsT.index.map(
            lambda d: incomeT[incomeT.index == d]['Net Income'].item() * indicatorFunction(ANNUALLY))

        bsT['netIncomeB'] = bsT['netIncome'] / 1000000000
        bsT['netIncomeBText'] = bsT['netIncomeB'].transform(lambda x: str(round(x)))

        bsT['PE'] = bsT['marketCap'] * exRate / bsT['netIncome']
        bsT['PE'] = bsT['PE'].transform(lambda x: x if x > 0 and not math.isinf(x) else 0)
        print('bstPE', bsT['PE'])
        bsT['PEText'] = bsT['PE'].transform(lambda x: str(round(x)) if x != 0 else 'undef')

        bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['Total Assets']
        bsT['SalesAssetsRatioText'] = bsT['SalesAssetsRatio'].transform(lambda x: str(round(x, 1)))

        bsT['PriceSalesRatio'] = (bsT['marketCap'] * exRate) / bsT['revenue']
        bsT['PriceSalesRatioText'] = bsT['PriceSalesRatio'].transform(lambda x: str(round(x, 1)))

        print('pb', bsT['PB'])
        print('rev', bsT['revenue'])

        bsT['pspb'] = (bsT['marketCap'] * exRate) / bsT['revenue'] * bsT['PB'] * 10000
        bsT['pspb'] = bsT['pspb'].transform(lambda x: 0 if math.isinf(x) or math.isnan(x) else x)

        bsT['pspbText'] = bsT['pspb'].transform(lambda x: str(round(x)))

        bsT['liq'] = bsT['Cash And Cash Equivalents'] + fill0Get(bsT, 'Accounts Receivable') * 0.8 \
                     + fill0Get(bsT, 'Inventory') * 0.5 - bsT['Total Liabilities Net Minority Interest']

        print('bst liq', bsT['liq'])

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
            lambda d: cfT[cfT.index == d]['Operating Cash Flow'].item() * indicatorFunction(ANNUALLY))

        if 'Depreciation' in cf.index:
            bsT['dep'] = bsT.index.map(
                lambda d: cfT[cfT.index == d]['Depreciation'].item() * indicatorFunction(ANNUALLY))
        else:
            bsT['dep'] = 0

        bsT['capex'] = bsT.index.map(
            lambda d: cfT[cfT.index == d]['Capital Expenditure'].item() * -1 * indicatorFunction(ANNUALLY)) \
            if 'Capital Expenditure' in cfT else 0

        bsT['FCF'] = bsT['CFO'] - bsT['dep']

        bsT['CFOB'] = bsT['CFO'] / 1000000000
        # print('cfo', bsT['CFOB'])
        bsT['CFOBText'] = bsT['CFOB'].fillna(0).transform(lambda x: str(round(x)))

        bsT['FCFB'] = bsT['FCF'] / 1000000000
        bsT['FCFBText'] = bsT['FCFB'].fillna(0).transform(lambda x: str(round(x)))

        bsT['PFCF'] = bsT['marketCap'] * exRate / bsT['FCF']
        bsT['PFCF'] = bsT['PFCF'].transform(lambda x: x if x > 0 else 0)
        bsT['PFCFText'] = bsT['PFCF'].fillna(0).transform(lambda x: str(round(x)) if x != 0 else 'undef')

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

        print('cash ', bsT['Cash And Cash Equivalents'])
        bsT['cashB'] = round(bsT['Cash And Cash Equivalents'].astype(float) / 1000000000, 3) \
            if 'Cash And Cash Equivalents' in bsT else 0
        bsT['cashBText'] = bsT['cashB'].fillna(0).transform(lambda x: str(round(x, 1))) if 'cashB' in bsT else ''

        bsT['netReceivablesB'] = bsT['Accounts Receivable'] / 1000000000 if 'Accounts Receivable' in bsT else 0
        bsT['inventoryB'] = bsT['Inventory'] / 1000000000 if 'Inventory' in bsT else 0
        bsT['netBookB'] = bsT['netBook'] / 1000000000 if 'netBook' in bsT else 0
        print('intang', bsT['intangibleAssetsB'])
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

        print("=============graph now===============")

        updateGraphs()
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

        text_input.title = compName1 + ' ' + compName2 + ' ' \
                           + '#:' + str(roundB(shares, 1)) + 'B ' \
                           + listCurr + bsCurr + '__MV:' + str(roundB(marketCapLast, 1)) + 'B' \
                           + "__NetB:" + str(roundB(bsT['netBook'][0] / exRate, 1)) + 'B' \
                           + "__liqR:" + str(round(latestLiqRatio, 1)) \
                           + "__nnR:" + str(round(latestNetnetRatio, 1)) \
                           + '__PS:' + (str(round(marketCapLast * exRate / bsT['revenue'][0], 1))
                                        if bsT['revenue'][0] != 0 else "na") \
                           + '__PB:' + str(round(marketCapLast * exRate / tangible_equity, 1)) \
                           + '__CR:' + str(round(bsT['currentRatio'][0], 1)) \
                           + '__DE:' + str(round(bsT['DERatio'][0], 1)) \
                           + '__RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
                           + '__P/FCF:' + (str(round(marketCapLast * exRate / bsT['FCF'][0], 1))
                                           if bsT['FCF'][0] > 0 else 'undef') \
                           + '__Div:' + (str(round(divYieldAll)) if 'yield' in divPrice else '') + '%' \
                           + '__2021Div:' \
                           + (str(round(divYield2021))) + '%' \
                           + '__p%:' + str(oneYearPercentile) + ' ' + str(twoYearPercentile) + ' ' \
                           + str(threeYearPercentile) + '_list:' + str(listYear)
        if not SIMPLE:
            otherInfo.text = "***Financials***" + '</br>' + ' '.join(["current ratio components cash", bsCurr,
                                                                      roundBString(
                                                                          getFromDF(bs, 'Cash And Cash Equivalents'),
                                                                          1), 'rec',
                                                                      roundBString(getFromDF(bs, 'Accounts Receivable'),
                                                                                   1),
                                                                      'inv',
                                                                      roundBString(getFromDF(bs, 'Inventory'), 1),
                                                                      'currL',
                                                                      roundBString(
                                                                          getFromDF(bs, 'Current Liabilities'),
                                                                          1)])

            otherInfo.text += '</br>' + ' '.join(["A", roundBString(totalAssets / exRate, 1), "B", "(",
                                                  roundBString(totalCurrentAssets / exRate, 1), ' '
                                                     , roundBString((totalAssets - totalCurrentAssets) / exRate, 1),
                                                  ")"])
            otherInfo.text += '</br>' + ' '.join(["L", roundBString(totalLiab / exRate, 1), "B", "(",
                                                  roundBString(currLiab / exRate, 1), ' ',
                                                  roundBString((totalLiab - currLiab) / exRate, 1), ")"])
            otherInfo.text += '</br>' + ' '.join(["E", roundBString((totalAssets - totalLiab) / exRate, 1), "B"])
            otherInfo.text += '</br>' + ''.join(["Tangible Equity", roundBString(tangible_equity, 1), 'B  ', bsCurr,
                                                 roundBString(tangible_equity / exRate, 1), 'B  ', listCurr])

        # otherInfo.text += '</br>' + ("Market Cap", str(roundB(marketPrice * shares, 2)) + "B", listCurr)
        # divPrice['yield'].iloc[-1]

        statusInfo.text = datetime.now().strftime('%H:%M:%S') + ' status is done' + '</br>'

        print("=============graph finished===============")
    except Exception as e:
        print(' big error is ', e)
        statusInfo.text = datetime.now().strftime('%H:%M:%S') + " big error is " + str(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def updateGraphs():
    global FIRST_TIME_GRAPHING

    print(' updating graphs. FIrst time graphing', FIRST_TIME_GRAPHING)
    print('update price graph')
    # lastPrice = round(stockData.data['close'][-1], 2) if 'close' in stockData.data else ''
    # lastPrice = round(stockData.data['close'][-1], 2) if 'close' in stockData.data else ''
    # yearsListed = priceData
    info = yf.Ticker(TICKER).info
    gPrice.title.text = ' Price chart:' + TICKER + '____' + \
                        str(round(info['currentPrice'] if 'currentPrice' in info else 0, 2))

    for figu in [gMarketcap, gCash, gCurrentAssets, gAssetComposition, gALE, gBook, gTangibleRatio,
                 gCurrentRatio, gRetainedEarnings, gDE, gPB, gEarnings, gPE, gCFO, gFCF, gPFCF,
                 gDepCFO, gCapexCFO, gSA, gPS, gNetnet, gPayAllDebt, gFCFA, gPSPB, gPSPLiq]:
        figu.x_range.factors = list(global_source.data['dateStr'][::-1])

    if FIRST_TIME_GRAPHING:
        gPrice.line(x='Date', y='Close', source=stockData, color='#D06C8A')
        gDiv.vbar(x='year', top='yield', source=divPriceData, width=0.8)
        gDiv.add_layout(LabelSet(x='year', y='yield', text='yieldText',
                                 source=divPriceData, text_align='center', render_mode='canvas'))

        # market cap
        gMarketcap.vbar(x='dateStr', top='marketCapB', source=global_source, width=0.5)
        gMarketcap.add_layout(LabelSet(x='dateStr', y='marketCapB', text='marketCapBText', source=global_source,
                                       text_align='center', text_font_size="13pt"))

        # cash
        gCash.vbar(x='dateStr', top='cashB', source=global_source, width=0.5)
        gCash.add_layout(LabelSet(x='dateStr', y='cashB', text='cashBText', source=global_source,
                                  text_align='center', text_font_size="13pt"))

        # , render_mode='canvas'

        # current assets
        colorsCurrent = ["darkgreen", "olive", "tan"]
        currentAssetItems = ['cashB', 'netReceivablesB', 'inventoryB']
        gCurrentAssets.vbar_stack(currentAssetItems, x='dateStr',
                                  source=global_source, color=colorsCurrent,
                                  legend_label=currentAssetItems, width=0.5)
        # gCurrentAssets.legend.orientation = "vertical"
        gCurrentAssets.legend.location = "top_left"

        # assets composition
        # colors = ["darkgreen", 'yellowgreen', "gold", "navy", 'salmon', 'darkred']
        colors = ['darkgreen', 'salmon', 'darkred']

        colors5 = ['darkgreen', 'olive', 'tan', 'salmon', 'darkred']
        assetCompoItems = ['cashB', 'noncashCurrentAssetsB', 'nonCurrentAssetsB', 'totalCurrentLiabB',
                           'totalNoncurrentLiabB']
        gAssetComposition.vbar_stack(assetCompoItems, x='dateStr',
                                     source=global_source, color=colors5, legend_label=assetCompoItems, width=0.5)
        # gAssetComposition.legend.orientation = "horizontal"
        gAssetComposition.legend.location = "top_left"

        # book
        bookItems = ['netBookB', 'goodWillB', 'intangibleAssetsB']
        gBook.vbar_stack(bookItems, x='dateStr', source=global_source, color=colors,
                         legend_label=bookItems, width=0.1)
        # try this
        gBook.vbar_stack(bookItems, x='dateStr', source=global_source, color=colors,
                         legend_label=bookItems, width=0.5)
        gBook.legend.location = "top_left"
        gBook.add_layout(LabelSet(x='dateStr', y='bookAllB', text='bookAllBText',
                                  source=global_source, text_align='center', text_font_size="13pt"))
        # gBook.vbar(x='dateStr', top='netBookB', source=global_source, width=0.5)

        aleItems = ['grossBookB', 'totalLiabB', 'totalAssetsB']
        gALE.vbar_stack(aleItems, x='dateStr', source=global_source, color=['darkgreen', 'darkred', 'tan']
                        , legend_label=aleItems, width=0.5)
        gALE.legend.location = "top_left"

        # tangible ratio
        gTangibleRatio.vbar(x='dateStr', top='tangibleRatio', source=global_source, width=0.5)
        gTangibleRatio.add_layout(LabelSet(x='dateStr', y='tangibleRatio', text='tangibleRatioText',
                                           source=global_source, text_align='center', text_font_size="13pt"))
        # current ratio
        gCurrentRatio.vbar(x='dateStr', top='currentRatio', source=global_source, width=0.5)
        gCurrentRatio.add_layout(LabelSet(x='dateStr', y='currentRatio', text='currentRatioText',
                                          source=global_source, text_align='center', text_font_size="13pt"))

        # retained earnings/Asset
        gRetainedEarnings.vbar(x='dateStr', top='REAssetsRatio', source=global_source, width=0.5)
        gRetainedEarnings.add_layout(LabelSet(x='dateStr', y='REAssetsRatio', text='REAssetsRatioText'
                                              , source=global_source, text_align='center', text_font_size="13pt"))

        # Debt/Equity
        gDE.vbar(x='dateStr', top='DERatio', source=global_source, width=0.5)
        gDE.add_layout(LabelSet(x='dateStr', y='DERatio', text='DERatioText'
                                , source=global_source, text_align='center', text_font_size="13pt"))

        # P/B
        gPB.vbar(x='dateStr', top='PB', source=global_source, width=0.5)
        gPB.add_layout(LabelSet(x='dateStr', y='PB', text='PBText'
                                , source=global_source, text_align='center', text_font_size="13pt"))

        # Earnings
        gEarnings.vbar(x='dateStr', top='netIncomeB', source=global_source, width=0.5)
        gEarnings.add_layout(LabelSet(x='dateStr', y='netIncomeB', text='netIncomeBText'
                                      , source=global_source, text_align='center', text_font_size="13pt"))

        # P/E
        gPE.vbar(x='dateStr', top='PE', source=global_source, width=0.5)
        gPE.add_layout(LabelSet(x='dateStr', y='PE', text='PEText'
                                , source=global_source, text_align='center', text_font_size="13pt"))

        # CFO
        gCFO.vbar(x='dateStr', top='CFOB', source=global_source, width=0.5)
        gCFO.add_layout(LabelSet(x='dateStr', y='CFOB', text='CFOBText'
                                 , source=global_source, text_align='center', text_font_size="13pt"))

        # FCF
        gFCF.vbar(x='dateStr', top='FCFB', source=global_source, width=0.5)
        gFCF.add_layout(LabelSet(x='dateStr', y='FCFB', text='FCFBText'
                                 , source=global_source, text_align='center', text_font_size="13pt"))

        # P/FCF
        gPFCF.vbar(x='dateStr', top='PFCF', source=global_source, width=0.5)
        gPFCF.add_layout(LabelSet(x='dateStr', y='PFCF', text='PFCFText'
                                  , source=global_source, text_align='center', text_font_size="13pt"))

        # Dep/CFO
        gDepCFO.vbar(x='dateStr', top='DepCFO', source=global_source, width=0.5)
        gDepCFO.add_layout(LabelSet(x='dateStr', y='DepCFO', text='DepCFOText'
                                    , source=global_source, text_align='center', text_font_size="13pt"))
        # capex/CFO
        gCapexCFO.vbar(x='dateStr', top='CapexCFO', source=global_source, width=0.5)
        gCapexCFO.add_layout(LabelSet(x='dateStr', y='CapexCFO', text='CapexCFOText'
                                      , source=global_source, text_align='center', text_font_size="13pt"))
        # Sales/Assets
        gSA.vbar(x='dateStr', top='SalesAssetsRatio', source=global_source, width=0.5)
        gSA.add_layout(LabelSet(x='dateStr', y='SalesAssetsRatio', text='SalesAssetsRatioText'
                                , source=global_source, text_align='center', text_font_size="13pt"))
        # Sales/Price
        gPS.vbar(x='dateStr', top='PriceSalesRatio', source=global_source, width=0.5)
        gPS.add_layout(LabelSet(x='dateStr', y='PriceSalesRatio', text='PriceSalesRatioText'
                                , source=global_source, text_align='center', text_font_size="13pt"))
        # netnet ratio
        gNetnet.vbar(x='dateStr', top='netnetRatio', source=global_source, width=0.5)
        gNetnet.add_layout(LabelSet(x='dateStr', y='netnetRatio', text='nnrText', source=global_source,
                                    text_align='center', text_font_size="13pt"))

        gPayAllDebt.vbar(x='dateStr', top='payAllDebtRatio', source=global_source, width=0.5)
        gPayAllDebt.add_layout(LabelSet(x='dateStr', y='payAllDebtRatio',
                                        text='payAllDebtText', source=global_source,
                                        text_align='center', text_font_size="13pt"))

        # CFO/A ratio
        gFCFA.vbar(x='dateStr', top='FCFAssetRatio', source=global_source, width=0.5)
        gFCFA.add_layout(LabelSet(x='dateStr', y='FCFAssetRatio', text='FCFAssetRatioText'
                                  , source=global_source, text_align='center', text_font_size="13pt"))

        # pspb
        gPSPB.vbar(x='dateStr', top='pspb', source=global_source, width=0.5)
        gPSPB.add_layout(LabelSet(x='dateStr', y='pspb', text='pspbText', source=global_source,
                                  text_align='center', text_font_size="13pt"))
        # pspb
        gPSPLiq.vbar(x='dateStr', top='pspliq', source=global_source, width=0.5)
        gPSPLiq.add_layout(LabelSet(x='dateStr', y='pspliq', text='pspliqText', source=global_source,
                                    text_align='center', text_font_size="13pt"))

        FIRST_TIME_GRAPHING = False


text_input = TextInput(value="0001.HK", title="Label:")
text_input.on_change("value", my_text_input_handler)

button = Button(label="Get Data")
button.on_click(buttonCallback)

button2 = Button(label='Reset')
button2.on_click(resetCallback)


def my_radio_handler(new):
    global ANNUALLY
    ANNUALLY = True if new == 0 else False
    print('ANNUAL IS', ANNUALLY)
    resetCallback()


def complexHandler(new):
    global SIMPLE
    SIMPLE = True if new == 0 else False
    print('simple is', SIMPLE)
    resetCallback()


rg = RadioGroup(labels=['Annual', 'Quarterly'], active=0)
rg.on_click(my_radio_handler)

rgComplex = RadioGroup(labels=['simple', 'full'], active=1)
rgComplex.on_click(complexHandler)

curdoc().add_root(column(row(button, button2), statusInfo, rg, rgComplex, text_input, grid, gPrice, gDiv, infoParagraph,
                         otherInfo))
