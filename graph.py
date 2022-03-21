comp = 'PDD'
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


def getBarWidth(annually):
    return 15552000000 if annually else 15552000000 / 4


def indicatorFunction(annually):
    return 1 if annually else 4


def fill0Get(df, item):
    return df[item].fillna(0) if item in df.columns else 0


try:
    exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
    listingCurrency = getListingCurrency(comp)
    bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
    print("listing currency, bs currency, ", listingCurrency, bsCurrency)
    exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)
except Exception as e:
    print(e)
    listingCurrency = 'HKD'
    bsCurrency = 'HKD'
    exRate = 1

print('exrate', listingCurrency, bsCurrency, exRate)

price = si.get_live_price(comp)

data = si.get_data(comp)
bs = si.get_balance_sheet(comp, yearly=ANNUALLY)
bsT = bs.T
bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']

print('retained earnings:')
print(bsT[['retainedEarnings', 'totalAssets']])

bsT['currentRatio'] = (bsT['cash']
                       + 0.5 * fill0Get(bsT, 'netReceivables') +
                       0.2 * fill0Get(bsT, 'inventory')) / bsT['totalCurrentLiabilities']

# print('cash rec inven currLiab', bsT[['cash', 'netReceivables', 'inventory', 'totalCurrentLiabilities']])

bsT['netBook'] = bsT['totalAssets'] - bsT['totalLiab'] - fill0Get(bsT, 'goodWill') \
                 - fill0Get(bsT, 'intangibleAssets')

bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
# print('net book is', bsT[['totalAssets', 'totalLiab', 'goodWill', 'intangibleAssets']])

bsT['priceOnOrAfter'] = bsT.index.map(lambda d: data[data.index >= d].iloc[0]['adjclose'])
shares = si.get_quote_data(comp)['sharesOutstanding']
bsT['marketCap'] = bsT['priceOnOrAfter'] * shares * exRate

# print('price, shares, exrate', bsT['priceOnOrAfter'], shares, exRate)

bsT['PB'] = bsT['marketCap'] / bsT['netBook']

# print('pb', bsT['marketCap'], bsT['netBook'])

income = si.get_income_statement(comp, yearly=ANNUALLY)
incomeT = income.T
bsT['revenue'] = bsT.index.map(lambda d: incomeT[incomeT.index == d]['totalRevenue'] * indicatorFunction(ANNUALLY))
# print('revenue', bsT['revenue'])
bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']

cf = si.get_cash_flow(comp, yearly=ANNUALLY)
cfT = cf.T
cfo = cf.loc["totalCashFromOperatingActivities"]
bsT['CFO'] = bsT.index.map(
    lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'] * indicatorFunction(ANNUALLY))
bsT['PCFO'] = bsT['marketCap'] / bsT['CFO']

bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.5 +
                       fill0Get(bsT, 'inventory') * 0.2) - bsT['totalLiab']) \
                     / exRate / bsT['marketCap']

# print('netnet', bsT[['cash', 'netReceivables', 'inventory', 'totalLiab', 'marketCap']])

bsT['CFOAssetRatio'] = bsT['CFO'] / bsT['totalAssets']

source = ColumnDataSource(bsT)

# cash
p = figure(title='cash', x_axis_type="datetime")
p.vbar(x='endDate', top='cash', source=source, width=getBarWidth(ANNUALLY))
p.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cash", "@cash")],
                      formatters={'@endDate': 'datetime'}, mode='vline'))
# p.hover.formatters = {'@endDate': 'datetime'}
# hover_tool.formatters = { "@endDate": "datetime"}
p.title.text_font_size = '18pt'
p.title.align = 'center'

# current ratio
p1 = figure(title='currentRatio', x_axis_type="datetime")
p1.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cr", "@currentRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p1.vbar(x='endDate', top='currentRatio', source=source, width=getBarWidth(ANNUALLY))
p1.title.text_font_size = '18pt'
p1.title.align = 'center'

# retained earnings/Asset
p2 = figure(title='RetEarnings/A', x_axis_type="datetime")
p2.vbar(x='endDate', top='REAssetsRatio', source=source, width=getBarWidth(ANNUALLY))

p2.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("Re/A", "@REAssetsRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))

p2.title.text_font_size = '18pt'
p2.title.align = 'center'

# Debt/Equity
p3 = figure(title='D/E Ratio', x_axis_type="datetime")
p3.vbar(x='endDate', top='DERatio', source=source, width=getBarWidth(ANNUALLY))
p3.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("DERatio", "@DERatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p3.title.text_font_size = '18pt'
p3.title.align = 'center'

# P/B
p4 = figure(title='P/B Ratio', x_axis_type="datetime")
p4.vbar(x='endDate', top='PB', source=source, width=getBarWidth(ANNUALLY))
p4.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PB", "@PB")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p4.title.text_font_size = '18pt'
p4.title.align = 'center'

# P/CFO
p5 = figure(title='P/CFO Ratio', x_axis_type="datetime")
p5.vbar(x='endDate', top='PCFO', source=source, width=getBarWidth(ANNUALLY))
p5.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PCFO", "@PCFO")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p5.title.text_font_size = '18pt'
p5.title.align = 'center'

# Sales/Assets
p6 = figure(title='Sales/Assets Ratio', x_axis_type="datetime")
p6.vbar(x='endDate', top='SalesAssetsRatio', source=source, width=getBarWidth(ANNUALLY))
p6.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("S/A Ratio", "@SalesAssetsRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p6.title.text_font_size = '18pt'
p6.title.align = 'center'

# netnet ratio
p7 = figure(title='netnet Ratio', x_axis_type="datetime")
p7.vbar(x='endDate', top='netnetRatio', source=source, width=getBarWidth(ANNUALLY))
p7.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("netnet", "@netnetRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p7.title.text_font_size = '18pt'
p7.title.align = 'center'

# CFO/A ratio
p8 = figure(title='CFO/A Ratio', x_axis_type="datetime")
p8.vbar(x='endDate', top='CFOAssetRatio', source=source, width=getBarWidth(ANNUALLY))
p8.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("CFO/A", "@CFOAssetRatio")],
                       formatters={'@endDate': 'datetime'}, mode='vline'))
p8.title.text_font_size = '18pt'
p8.title.align = 'center'

grid = gridplot([[p, None], [p1, p2], [p3, p4], [p5, p6], [p7, p8]], width=500, height=500)

show(grid)
