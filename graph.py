from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show
from bokeh.models.tools import HoverTool

import yahoo_fin.stock_info as si
import currency_getExchangeRate
from currency_scrapeYahoo import getListingCurrency, getBalanceSheetCurrency

HALF_YEAR_WIDE = 15552000000
ANNUALLY = False


def getBarWidth(annually):
    if annually:
        return 15552000000
    else:
        return 15552000000 / 4


def indicatorFunction(annually):
    if annually:
        return 1
    else:
        return 4


comp = '2698.HK'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
listingCurrency = getListingCurrency(comp)
bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
print("listing currency, bs currency, ", listingCurrency, bsCurrency)
exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

print('exrate', listingCurrency, bsCurrency, exRate)

price = si.get_live_price(comp)

data = si.get_data(comp)
bs = si.get_balance_sheet(comp, yearly=ANNUALLY)
bsT = bs.T
bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']
bsT['currentRatio'] = (bsT['cash'] + 0.5 * bsT['netReceivables'] + 0.2 * bsT['inventory']) \
                      / bsT['totalCurrentLiabilities']
bsT['netBook'] = (bsT['totalAssets'] - bsT['totalLiab']
                  - (bsT['goodWill'] if 'goodWill' in bsT.columns else 0)
                  - (bsT['intangibleAssets'] if 'intangibleAssets' in bsT.columns else 0))
bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
bsT['priceOnOrAfter'] = bsT.index.map(lambda d: data[data.index >= d].iloc[0]['adjclose'])
shares = si.get_quote_data('0743.HK')['sharesOutstanding']
bsT['marketCap'] = bsT['priceOnOrAfter'] * shares * exRate
bsT['PB'] = bsT['marketCap'] / bsT['netBook']

income = si.get_income_statement(comp, yearly=ANNUALLY)
incomeT = income.T
bsT['revenue'] = bsT.index.map(lambda d: incomeT[incomeT.index == d]['totalRevenue'] * indicatorFunction(ANNUALLY))
bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']

cf = si.get_cash_flow(comp, yearly=ANNUALLY)
cfT = cf.T
cfo = cf.loc["totalCashFromOperatingActivities"]
bsT['CFO'] = bsT.index.map(
    lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'] * indicatorFunction(ANNUALLY))
bsT['PCFO'] = bsT['marketCap'] / bsT['CFO']

bsT['netnetRatio'] = ((bsT['cash'] + bsT['netReceivables'] * 0.5 + bsT['inventory'] * 0.2) - bsT['totalLiab']) \
                     / exRate / bsT['marketCap']
source = ColumnDataSource(bsT)
print(source.data)

############ test
# cash
p = figure(title='cash', x_axis_type="datetime")
p.vbar(x='endDate', top='cash', source=source, width=getBarWidth(ANNUALLY))
p.title.text_font_size = '18pt'
p.title.align = 'center'

# current ratio
p1 = figure(title='currentRatio', x_axis_type="datetime")
p1.vbar(x='endDate', top='currentRatio', source=source, width=getBarWidth(ANNUALLY))
p1.title.text_font_size = '18pt'
p1.title.align = 'center'

# retained earnings/Asset
p2 = figure(title='RetEarnings/A', x_axis_type="datetime")
p2.vbar(x='endDate', top='REAssetsRatio', source=source, width=getBarWidth(ANNUALLY))
p2.title.text_font_size = '18pt'
p2.title.align = 'center'

# Debt/Equity
p3 = figure(title='D/E Ratio', x_axis_type="datetime")
p3.vbar(x='endDate', top='DERatio', source=source, width=getBarWidth(ANNUALLY))
p3.title.text_font_size = '18pt'
p3.title.align = 'center'

# P/B
p4 = figure(title='P/B Ratio', x_axis_type="datetime")
p4.vbar(x='endDate', top='PB', source=source, width=getBarWidth(ANNUALLY))
p4.title.text_font_size = '18pt'
p4.title.align = 'center'

# P/CFO
p5 = figure(title='P/CFO Ratio', x_axis_type="datetime")
p5.vbar(x='endDate', top='PCFO', source=source, width=getBarWidth(ANNUALLY))
p5.title.text_font_size = '18pt'
p5.title.align = 'center'

# Sales/Assets
p6 = figure(title='Sales/Assets Ratio', x_axis_type="datetime")
p6.vbar(x='endDate', top='SalesAssetsRatio', source=source, width=getBarWidth(ANNUALLY))
p6.title.text_font_size = '18pt'
p6.title.align = 'center'

# netnet ratio
p7 = figure(title='netnet Ratio', x_axis_type="datetime")
p7.vbar(x='endDate', top='netnetRatio', source=source, width=getBarWidth(ANNUALLY))
p7.title.text_font_size = '18pt'
p7.title.align = 'center'

# show(column(p, p1, p2, p3))


grid = gridplot([[p1, p2], [p3, p4], [p5, p6], [p7, None]], width=500, height=500)

show(grid)
