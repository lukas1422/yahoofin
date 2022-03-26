from math import pi
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, Paragraph, Label

from helperMethods import fill0Get, getBarWidth, indicatorFunction, roundB
from scrape_sharesOutstanding import scrapeTotalSharesXueqiu

ANNUALLY = False

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, show
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
    TICKER = new
    print('new ticker is ', TICKER)
    # resetCallback()
    # buttonCallback()


infoParagraph = Paragraph(width=1000, height=500, text='Blank')

# price chart
priceChart = figure(title='prices chart', width=1000, x_axis_type="datetime")
priceChart.xaxis.major_label_orientation = pi / 4
priceChart.grid.grid_line_alpha = 0.3
priceChart.add_tools(HoverTool(tooltips=[('date', '@date{%Y-%m-%d}'), ('close', '@close')],
                               formatters={'@date': 'datetime'}, mode='vline'))

# priceChart.background_fill_color = "#f5f5f5"
pDiv = figure(title="divYld", width=1000)
pDiv.add_tools(HoverTool(tooltips=[('year', '@year'), ("yield", "@yield")], mode='vline'))

pCash = figure(title='cash', x_axis_type="datetime")
pCash.title.text = 'cash '
pCash.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cash", "@cash")],
                          formatters={'@endDate': 'datetime'}, mode='vline'))

pBook = figure(title='book', x_axis_type="datetime")
pBook.title.text = 'Book'
pBook.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("book", "@netBook")],
                          formatters={'@endDate': 'datetime'}, mode='vline'))

p1 = figure(title='currentRatio', x_axis_type="datetime")
p2 = figure(title='RetEarnings/A', x_axis_type="datetime")
p3 = figure(title='D/E Ratio', x_axis_type="datetime")
p4 = figure(title='P/B Ratio', x_axis_type="datetime")
p5 = figure(title='P/CFO Ratio', x_axis_type="datetime")
p6 = figure(title='Sales/Assets Ratio', x_axis_type="datetime")
p7 = figure(title='netnet Ratio', x_axis_type="datetime")
p8 = figure(title='CFO/A Ratio', x_axis_type="datetime")
p1.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cr", "@currentRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p2.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("Re/A", "@REAssetsRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p3.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("DERatio", "@DERatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p4.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PB", "@PB")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p5.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PCFO", "@PCFO")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p6.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("S/A Ratio", "@SalesAssetsRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p7.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("netnet", "@netnetRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p8.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("CFO/A", "@CFOAssetRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))

for figu in [priceChart, pCash, pBook, pDiv, p1, p2, p3, p4, p5, p6, p7, p8]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'

grid = gridplot([[pCash, pBook], [p1, p2], [p3, p4], [p5, p6], [p7, p8]], width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()


# global_source = ColumnDataSource(pd.DataFrame())
# stockData = ColumnDataSource(pd.DataFrame())
# divPriceData = ColumnDataSource(pd.DataFrame())

def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    infoParagraph.text = ""
    text_input.title = ''
    updateGraphs()
    print(' cleared source ')


def buttonCallback():
    global TICKER
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

    # print('ticker exrate', TICKER, listingCurrency, bsCurrency, exRate)
    priceData = si.get_data(TICKER)
    priceData.index.name = 'date'
    divData = si.get_dividends(TICKER)
    divPrice = pd.DataFrame()
    if not divData.empty:
        divData.groupby(by=lambda a: a.year)['dividend'].sum()
        divPrice = pd.merge(divData.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(),
                            left_index=True, right_index=True)
        divPrice.index.name = 'year'
        divPrice['yield'] = divPrice['dividend'] / divPrice['close'] * 100
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
    bsT['PCFO'] = bsT['marketCap'] * exRate / bsT['CFO']
    bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.5 +
                           fill0Get(bsT, 'inventory') * 0.2) / (bsT['totalLiab'] + exRate * bsT['marketCap']))
    bsT['CFOAssetRatio'] = bsT['CFO'] / bsT['totalAssets']
    global_source.data = ColumnDataSource.from_df(bsT)
    stockData.data = ColumnDataSource.from_df(priceData)

    print("=============graph now===============")
    updateGraphs()
    compName1 = info.loc['longBusinessSummary'].item().split(' ')[0] if 'longBusinessSummary' in info.index else ""
    compName2 = info.loc['longBusinessSummary'].item().split(' ')[1] if 'longBusinessSummary' in info.index else ""
    # print(' comp name ', compName1, compName2, 'summary', info.loc['longBusinessSummary'].item().split(' '))
    text_input.title = compName1 + ' ' + compName2 + ' ' + \
                       listingCurrency + bsCurrency + '______MV:' + str(roundB(bsT['marketCap'][0], 1)) + 'B' \
                       + "____NetB:" + str(roundB(bsT['netBook'][0] / exRate, 1)) + 'B' \
                       + '____PB:' + str(round(bsT['PB'][0], 2)) \
                       + '____CR:' + str(round(bsT['currentRatio'][0], 1)) \
                       + '____DE:' + str(round(bsT['DERatio'][0], 1)) \
                       + '____RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
                       + '____P/CFO:' + str(round(bsT['PCFO'][0], 1)) \
                       + '____DivYld:' + (str(round(divPrice['yield'].mean(), 1)) if 'yield' in divPrice else '') + '%' \
                       + '____lastDivYld:' \
                       + (str(round(divPrice['yield'].iloc[-1], 1)) if 'yield' in divPrice else '') + '%'

    print("=============graph finished===============")

    # print("get width div graph", 20 / len(divPriceData.data['year']))
    # return 20 / len(divPriceData.data['year'])


def updateGraphs():
    print('update price graph')
    lastPrice = round(stockData.data['close'][-1], 2) if 'close' in stockData.data else ''
    priceChart.title.text = ' prices ' + TICKER + '____' + str(lastPrice)
    priceChart.line(x='date', y='close', source=stockData, color='#D06C8A')

    pDiv.vbar(x='year', top='yield', source=divPriceData, width=getWidthDivGraph())

    # cash
    pCash.vbar(x='endDate', top='cash', source=global_source, width=getBarWidth(ANNUALLY))

    # book
    pBook.vbar(x='endDate', top='netBook', source=global_source, width=getBarWidth(ANNUALLY))


    # current ratio
    p1.vbar(x='endDate', top='currentRatio', source=global_source, width=getBarWidth(ANNUALLY))

    # retained earnings/Asset
    p2.vbar(x='endDate', top='REAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))

    # Debt/Equity
    p3.vbar(x='endDate', top='DERatio', source=global_source, width=getBarWidth(ANNUALLY))

    # P/B
    p4.vbar(x='endDate', top='PB', source=global_source, width=getBarWidth(ANNUALLY))
    # P/CFO
    p5.vbar(x='endDate', top='PCFO', source=global_source, width=getBarWidth(ANNUALLY))

    # Sales/Assets
    p6.vbar(x='endDate', top='SalesAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))

    # netnet ratio
    p7.vbar(x='endDate', top='netnetRatio', source=global_source, width=getBarWidth(ANNUALLY))


    # CFO/A ratio
    p8.vbar(x='endDate', top='CFOAssetRatio', source=global_source, width=getBarWidth(ANNUALLY))




text_input = TextInput(value="0001.HK", title="Label:")
text_input.on_change("value", my_text_input_handler)

button = Button(label="Get Data")
button.on_click(buttonCallback)

button2 = Button(label='Reset')
button2.on_click(resetCallback)


# prelimLabel = Label(width=500, text='abc')


def my_radio_handler(new):
    global ANNUALLY
    ANNUALLY = True if new == 0 else False
    print('ANNUAL IS', ANNUALLY)


rg = RadioGroup(labels=['Annual', 'Quarterly'], active=1)
rg.on_click(my_radio_handler)

curdoc().add_root(column(row(button, button2), rg, text_input, priceChart, pDiv, grid, infoParagraph))
