# myapp.py
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup

from helperMethods import fill0Get, getBarWidth, indicatorFunction

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


def my_text_input_handler(attr, old, new):
    global TICKER
    TICKER = new
    print('new ticker is ', TICKER)


# def initialize():
p = figure(title='cash', x_axis_type="datetime")
p1 = figure(title='currentRatio', x_axis_type="datetime")
p2 = figure(title='RetEarnings/A', x_axis_type="datetime")
p3 = figure(title='D/E Ratio', x_axis_type="datetime")
p4 = figure(title='P/B Ratio', x_axis_type="datetime")
p5 = figure(title='P/CFO Ratio', x_axis_type="datetime")
p6 = figure(title='Sales/Assets Ratio', x_axis_type="datetime")
p7 = figure(title='netnet Ratio', x_axis_type="datetime")
p8 = figure(title='CFO/A Ratio', x_axis_type="datetime")
grid = gridplot([[p, None], [p1, p2], [p3, p4], [p5, p6], [p7, p8]], width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
global_source = ColumnDataSource(pd.DataFrame())


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    updateGraphs()
    print(' cleared source ')


def buttonCallback():
    global TICKER
    print(" button pressed ")
    print(' new ticker is ', TICKER)

    print('clearing graphs')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    updateGraphs()
    print('clearing graphs done')

    try:
        listingCurrency = getListingCurrency(TICKER)
        bsCurrency = getBalanceSheetCurrency(TICKER, listingCurrency)
        print("ticker, listing currency, bs currency, ", TICKER, listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

    except Exception as e:
        print(e)

    print('ticker exrate', TICKER, listingCurrency, bsCurrency, exRate)
    price = si.get_live_price(TICKER)
    print(' ticker price ', TICKER, price)
    data = si.get_data(TICKER)

    bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
    bsT = bs.T
    bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']
    bsT['currentRatio'] = (bsT['cash'] + 0.5 * fill0Get(bsT, 'netReceivables') +
                           0.2 * fill0Get(bsT, 'inventory')) / bsT['totalCurrentLiabilities']
    bsT['netBook'] = bsT['totalAssets'] - bsT['totalLiab'] - fill0Get(bsT, 'goodWill') \
                     - fill0Get(bsT, 'intangibleAssets')
    bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
    bsT['priceOnOrAfter'] = bsT.index.map(lambda d: data[data.index >= d].iloc[0]['adjclose'])
    shares = si.get_quote_data(TICKER)['sharesOutstanding']
    bsT['marketCap'] = bsT['priceOnOrAfter'] * shares * exRate
    bsT['PB'] = bsT['marketCap'] / bsT['netBook']
    income = si.get_income_statement(TICKER, yearly=ANNUALLY)
    incomeT = income.T
    bsT['revenue'] = bsT.index.map(lambda d: incomeT[incomeT.index == d]['totalRevenue'] * indicatorFunction(ANNUALLY))
    bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']
    cf = si.get_cash_flow(TICKER, yearly=ANNUALLY)
    cfT = cf.T
    bsT['CFO'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'] * indicatorFunction(ANNUALLY))
    bsT['PCFO'] = bsT['marketCap'] / bsT['CFO']
    bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.5 +
                           fill0Get(bsT, 'inventory') * 0.2) - bsT['totalLiab']) \
                         / exRate / bsT['marketCap']
    bsT['CFOAssetRatio'] = bsT['CFO'] / bsT['totalAssets']
    print('ticker', 'new source complete:index cols', bsT.index, bsT.columns)
    global_source.data = ColumnDataSource.from_df(bsT)
    print("=============graph now===============")
    updateGraphs()
    print("=============graph finished===============")


def updateGraphs():
    p.vbar(x='endDate', top='cash', source=global_source, width=getBarWidth(ANNUALLY))
    p.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cash", "@cash")],
                          formatters={'@endDate': 'datetime'}, mode='vline'))
    p.title.text_font_size = '18pt'
    p.title.align = 'center'

    # current ratio
    p1.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cr", "@currentRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p1.vbar(x='endDate', top='currentRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p1.title.text_font_size = '18pt'
    p1.title.align = 'center'

    # retained earnings/Asset
    p2.vbar(x='endDate', top='REAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p2.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("Re/A", "@REAssetsRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p2.title.text_font_size = '18pt'
    p2.title.align = 'center'

    # Debt/Equity
    p3.vbar(x='endDate', top='DERatio', source=global_source, width=getBarWidth(ANNUALLY))
    p3.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("DERatio", "@DERatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p3.title.text_font_size = '18pt'
    p3.title.align = 'center'

    # P/B
    p4.vbar(x='endDate', top='PB', source=global_source, width=getBarWidth(ANNUALLY))
    p4.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PB", "@PB")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p4.title.text_font_size = '18pt'
    p4.title.align = 'center'

    # P/CFO
    p5.vbar(x='endDate', top='PCFO', source=global_source, width=getBarWidth(ANNUALLY))
    p5.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PCFO", "@PCFO")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p5.title.text_font_size = '18pt'
    p5.title.align = 'center'

    # Sales/Assets
    p6.vbar(x='endDate', top='SalesAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p6.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("S/A Ratio", "@SalesAssetsRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p6.title.text_font_size = '18pt'
    p6.title.align = 'center'

    # netnet ratio
    p7.vbar(x='endDate', top='netnetRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p7.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("netnet", "@netnetRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p7.title.text_font_size = '18pt'
    p7.title.align = 'center'

    # CFO/A ratio
    p8.vbar(x='endDate', top='CFOAssetRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p8.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("CFO/A", "@CFOAssetRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p8.title.text_font_size = '18pt'
    p8.title.align = 'center'


text_input = TextInput(value="0001.HK", title="Label:")
text_input.on_change("value", my_text_input_handler)

# add a button widget and configure with the call back
button = Button(label="Get Data")
button.on_click(buttonCallback)

button2 = Button(label='Reset')
button2.on_click(resetCallback)


def my_radio_handler(new):
    global ANNUALLY
    ANNUALLY = True if new == 0 else False
    print('ANNUAL IS', ANNUALLY)

rg = RadioGroup(labels=['Annual', 'Quarterly'], active=0)
rg.on_click(my_radio_handler)

# put the button and plot in a layout and add to the document
curdoc().add_root(column(row(button, button2), rg, text_input, grid))
