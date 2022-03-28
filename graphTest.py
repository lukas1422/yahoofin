from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, FactorRange

from helperMethods import getBarWidth

ANNUALLY = False
FIRST_TIME_GRAPHING = True

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


def my_text_input_handler(attr, old, new):
    global TICKER
    TICKER = new
    print('new ticker is ', TICKER)


gCash = figure(title='cash', x_range=FactorRange(factors=list()))
gCash.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("cash", "@cash")], mode='vline'))

for figu in [gCash]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    text_input.title = ''
    print(' cleared source ')


def buttonCallback():
    print('new ticker is ', TICKER)
    print('annual is ', ANNUALLY)

    bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
    bsT = bs.T

    bsT['dateStr'] = pd.to_datetime(bsT.index)
    bsT['dateStr'] = bsT['dateStr'].transform(lambda x: x.strftime('%Y-%m-%d'))
    bsT.set_index('dateStr')

    global_source.data = ColumnDataSource.from_df(bsT)

    print("=============graph now===============")

    # print('global source data', global_source.data)

    print(' global source data datestr', global_source.data['dateStr'][::-1])

    gCash.vbar(x='dateStr', top='cash', source=global_source, width=0.5)
    print('list of potential factors', list(global_source.data['dateStr'][::-1]))
    gCash.x_range.factors = list(global_source.data['dateStr'][::-1])

    if FIRST_TIME_GRAPHING:
        updateGraphs()
    else:
        print(' already graphed ')

    print("=============graph finished===============")


def updateGraphs():
    global FIRST_TIME_GRAPHING

    print(' updating graphs. FIrst time graphing', FIRST_TIME_GRAPHING)
    print('update price graph')
    gCash.vbar(x='dateStr', top='cash', source=global_source, width=0.5)
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

curdoc().add_root(column(row(button, button2), rg, text_input, gCash))
