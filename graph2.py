from math import pi
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, Paragraph, Label, Range1d, LinearAxis, DataRange1d, FactorRange

from helperMethods import fill0Get, getBarWidth, indicatorFunction, roundB
from scrape_sharesOutstanding import scrapeTotalSharesXueqiu

ANNUALLY = False
FIRST_TIME_GRAPHING = True

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
import yahoo_fin.stock_info as si
import currency_getExchangeRate
from currency_scrapeYahoo import getListingCurrency, getBalanceSheetCurrency
import pandas as pd

pd.set_option('display.expand_frame_repr', False)

HALF_YEAR_WIDE = 15552000000

TICKER = '0001.HK'

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
    TICKER = new.upper()
    print('new ticker is ', TICKER)


infoParagraph = Paragraph(width=1000, height=500, text='Blank')

# price chart
gPrice = figure(title='prices chart', width=1000, x_axis_type="datetime")
gPrice.xaxis.major_label_orientation = pi / 4
gPrice.grid.grid_line_alpha = 0.3
gPrice.add_tools(HoverTool(tooltips=[('date', '@date{%Y-%m-%d}'), ('close', '@close')],
                           formatters={'@date': 'datetime'}, mode='vline'))

# priceChart.background_fill_color = "#f5f5f5"
gDiv = figure(title="divYld", width=1000)
gDiv.add_tools(HoverTool(tooltips=[('year', '@year'), ("yield", "@yield")], mode='vline'))

gCash = figure(title='cash(B)', x_range=FactorRange(factors=list()))
gCash.title.text = 'cash(B) '
gCash.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("cash", "@cashB")], mode='vline'))

gBook = figure(title='book(B)', x_range=FactorRange(factors=list()))
gBook.title.text = 'Book(B)'
gBook.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("bookB", "@netBookB")], mode='vline'))

gCurrentRatio = figure(title='currentRatio', x_range=FactorRange(factors=list()))
gRetainedEarnings = figure(title='RetEarnings/A', x_range=FactorRange(factors=list()))
gDE = figure(title='D/E Ratio', x_range=FactorRange(factors=list()))
gPB = figure(title='P/B Ratio', x_range=FactorRange(factors=list()))
gFCF = figure(title='FCF(B)', x_range=FactorRange(factors=list()))
gPFCF = figure(title='P/FCF', x_range=FactorRange(factors=list()))
gDepCFO = figure(title='Dep/CFO', x_range=FactorRange(factors=list()))
gCapexCFO = figure(title='Capex/CFO', x_range=FactorRange(factors=list()))

gSA = figure(title='Sales/Assets Ratio', x_range=FactorRange(factors=list()))
gNetnet = figure(title='netnet Ratio', x_range=FactorRange(factors=list()))
gFCFA = figure(title='FCF/A Ratio', x_range=FactorRange(factors=list()))

gCurrentRatio.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("cr", "@currentRatio")], mode='vline'))
gRetainedEarnings.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("Re/A", "@REAssetsRatio")], mode='vline'))

gDE.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("DERatio", "@DERatio")], mode='vline'))
gPB.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PB", "@PB")], mode='vline'))
gFCF.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("FCFB", "@FCFB")], mode='vline'))
gPFCF.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PFCF", "@PFCF")], mode='vline'))
gDepCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("DepCFO", "@DepCFO")], mode='vline'))
gCapexCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("CapexCFO", "@CapexCFO")], mode='vline'))

gSA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("S/A Ratio", "@SalesAssetsRatio")], mode='vline'))
gNetnet.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("netnet", "@netnetRatio")], mode='vline'))
gFCFA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("FCF/A", "@FCFAssetRatio")], mode='vline'))

for figu in [gPrice, gCash, gBook, gDiv, gCurrentRatio, gRetainedEarnings, gDE, gPB,
             gFCF, gPFCF, gDepCFO, gCapexCFO, gSA, gNetnet, gFCFA]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'

grid = gridplot(
    [[gCash, gBook], [gCurrentRatio, gRetainedEarnings], [gDE, gPB], [gFCF, gPFCF], [gDepCFO, gCapexCFO],
     [gSA, gNetnet], [gFCFA, None]], width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    infoParagraph.text = ""
    text_input.title = ''
    gPrice.title.text = ''
    print(' cleared source ')


def buttonCallback():
    print(' new ticker is ', TICKER)
    print('annual is ', ANNUALLY)

    try:
        listingCurrency = getListingCurrency(TICKER)
        bsCurrency = getBalanceSheetCurrency(TICKER, listingCurrency)
        print("ticker, listing currency, bs currency, ", TICKER, listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

    except Exception as e:
        print(e)

    info = si.get_company_info(TICKER)
    infoText = info.loc['country'].item() + "______________" + info.loc['industry'].item() + \
               '______________' + info.loc['sector'].item() + "______________" + info.loc['longBusinessSummary'].item()

    print('info text is ', infoText)
    infoParagraph.text = str(infoText)

    priceData = si.get_data(TICKER)
    priceData.index.name = 'date'
    divData = si.get_dividends(TICKER)
    divPrice = pd.DataFrame()
    if not divData.empty:
        # divData.groupby(by=lambda a: a.year)['dividend'].sum()
        divPrice = pd.merge(divData.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(),
                            left_index=True, right_index=True)
        # print('divprice1', divPrice)
        divPrice.index.name = 'year'
        divPrice['yield'] = divPrice['dividend'] / divPrice['close'] * 100

        # print('divprice2', divPrice)
        divPriceData.data = ColumnDataSource.from_df(divPrice)

    latestPrice = si.get_live_price(TICKER)
    bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
    bsT = bs.T
    bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']
    bsT['currentRatio'] = (bsT['cash'] + 0.5 * fill0Get(bsT, 'netReceivables') +
                           0.2 * fill0Get(bsT, 'inventory')) / bsT['totalCurrentLiabilities']
    bsT['netBook'] = bsT['totalAssets'] - bsT['totalLiab'] - fill0Get(bsT, 'goodWill') \
                     - fill0Get(bsT, 'intangibleAssets')
    bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
    bsT['priceOnOrAfter'] = bsT.index.map(lambda d: priceData[priceData.index >= d].iloc[0]['adjclose'])
    bsT['priceOnOrAfter'][0] = latestPrice

    shares = si.get_quote_data(TICKER)['sharesOutstanding']

    if TICKER.upper().endswith("HK") and bsCurrency == 'CNY':
        shares = scrapeTotalSharesXueqiu(TICKER)
        print('using xueqiu total shares for china', TICKER, shares)

    bsT['marketCap'] = bsT['priceOnOrAfter'] * shares
    bsT['PB'] = bsT['marketCap'] * exRate / bsT['netBook']
    income = si.get_income_statement(TICKER, yearly=ANNUALLY)
    incomeT = income.T
    bsT['revenue'] = bsT.index.map(
        lambda d: incomeT[incomeT.index == d]['totalRevenue'].item() * indicatorFunction(ANNUALLY))
    bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']
    cf = si.get_cash_flow(TICKER, yearly=ANNUALLY)
    cfT = cf.T
    bsT['CFO'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'].item() * indicatorFunction(ANNUALLY))
    bsT['dep'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['depreciation'].item() * indicatorFunction(ANNUALLY))
    bsT['capex'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['capitalExpenditures'].item() * -1 * indicatorFunction(ANNUALLY))
    bsT['FCF'] = bsT['CFO'] - bsT['dep']

    bsT['CFOB'] = bsT['CFO'] / 1000000000
    bsT['FCFB'] = bsT['FCF'] / 1000000000
    bsT['PFCF'] = bsT['marketCap'] * exRate / bsT['FCF']

    print('fcf', bsT['FCF'])
    print('pfcf', bsT['PFCF'])

    bsT['DepCFO'] = bsT['dep'] / bsT['CFO']
    bsT['CapexCFO'] = bsT['capex'] / bsT['CFO']

    bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.8 +
                           fill0Get(bsT, 'inventory') * 0.5) / (bsT['totalLiab'] + exRate * bsT['marketCap']))
    bsT['FCFAssetRatio'] = bsT['FCF'] / bsT['totalAssets']

    bsT['dateStr'] = pd.to_datetime(bsT.index)
    bsT['dateStr'] = bsT['dateStr'].transform(lambda x: x.strftime('%Y-%m-%d'))
    bsT['cashB'] = bsT['cash'] / 1000000000
    bsT['netBookB'] = bsT['netBook'] / 1000000000

    global_source.data = ColumnDataSource.from_df(bsT)
    stockData.data = ColumnDataSource.from_df(priceData)

    print("=============graph now===============")

    updateGraphs()

    compName1 = info.loc['longBusinessSummary'].item().split(' ')[0] if 'longBusinessSummary' in info.index else ""
    compName2 = info.loc['longBusinessSummary'].item().split(' ')[1] if 'longBusinessSummary' in info.index else ""
    # print(' comp name ', compName1, compName2, 'summary', info.loc['longBusinessSummary'].item().split(' '))
    text_input.title = compName1 + ' ' + compName2 + ' ' \
                       + 'shares:' + str(roundB(shares, 2)) + 'B ' \
                       + listingCurrency + bsCurrency + '______MV:' + str(roundB(bsT['marketCap'][0], 1)) + 'B' \
                       + "____NetB:" + str(roundB(bsT['netBook'][0] / exRate, 1)) + 'B' \
                       + '____PB:' + str(round(bsT['PB'][0], 2)) \
                       + '____CR:' + str(round(bsT['currentRatio'][0], 1)) \
                       + '____DE:' + str(round(bsT['DERatio'][0], 1)) \
                       + '____RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
                       + '____P/FCF:' + str(round(bsT['PFCF'][0], 1)) \
                       + '____DivYld:' + (str(round(divPrice['yield'].mean(), 1)) if 'yield' in divPrice else '') + '%' \
                       + '____lastDivYld:' \
                       + (str(round(divPrice['yield'].iloc[-1], 1)) if 'yield' in divPrice else '') + '%'

    print("=============graph finished===============")


def updateGraphs():
    global FIRST_TIME_GRAPHING

    print(' updating graphs. FIrst time graphing', FIRST_TIME_GRAPHING)
    print('update price graph')
    lastPrice = round(stockData.data['close'][-1], 2) if 'close' in stockData.data else ''
    gPrice.title.text = ' prices ' + TICKER + '____' + str(lastPrice)

    for figu in [gCash, gBook, gCurrentRatio, gRetainedEarnings, gDE, gPB, gFCF, gPFCF, gDepCFO, gCapexCFO,
                 gSA, gNetnet, gFCFA]:
        figu.x_range.factors = list(global_source.data['dateStr'][::-1])

    if FIRST_TIME_GRAPHING:
        gPrice.line(x='date', y='close', source=stockData, color='#D06C8A')
        gDiv.vbar(x='year', top='yield', source=divPriceData, width=0.8)

        # cash
        gCash.vbar(x='dateStr', top='cashB', source=global_source, width=0.5)

        # book
        gBook.vbar(x='dateStr', top='netBookB', source=global_source, width=0.5)

        # current ratio
        gCurrentRatio.vbar(x='dateStr', top='currentRatio', source=global_source, width=0.5)

        # retained earnings/Asset
        gRetainedEarnings.vbar(x='dateStr', top='REAssetsRatio', source=global_source, width=0.5)

        # Debt/Equity
        gDE.vbar(x='dateStr', top='DERatio', source=global_source, width=0.5)

        # P/B
        gPB.vbar(x='dateStr', top='PB', source=global_source, width=0.5)

        # CFO
        gFCF.vbar(x='dateStr', top='FCFB', source=global_source, width=0.5)

        # P/FCF
        gPFCF.vbar(x='dateStr', top='PFCF', source=global_source, width=0.5)

        # Dep/CFO
        gDepCFO.vbar(x='dateStr', top='DepCFO', source=global_source, width=0.5)

        # capex/CFO
        gCapexCFO.vbar(x='dateStr', top='CapexCFO', source=global_source, width=0.5)

        # Sales/Assets
        gSA.vbar(x='dateStr', top='SalesAssetsRatio', source=global_source, width=0.5)

        # netnet ratio
        gNetnet.vbar(x='dateStr', top='netnetRatio', source=global_source, width=0.5)

        # CFO/A ratio
        gFCFA.vbar(x='dateStr', top='FCFAssetRatio', source=global_source, width=0.5)
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


rg = RadioGroup(labels=['Annual', 'Quarterly'], active=1)
rg.on_click(my_radio_handler)

curdoc().add_root(column(row(button, button2), rg, text_input, gPrice, gDiv, grid, infoParagraph))
