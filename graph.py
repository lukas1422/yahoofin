from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show
from bokeh.models.tools import HoverTool

import yahoo_fin.stock_info as si

bs = si.get_balance_sheet('AAPL')
# dates = bs.columns
bsT= bs.T

source = ColumnDataSource(bsT)
print(source.data)

############ test
fig = figure(x_axis_type="datetime")
fig.line(x='endDate',y='totalLiab', source=source)
# p.circle(x='', y='y_values', source=source)
show(fig)