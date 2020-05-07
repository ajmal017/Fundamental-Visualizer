#!/usr/bin/env python
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_daq import ToggleSwitch
from dash.dependencies import Input, Output, State
from webscraper import req_handle
from data_processing import data_processing
import plotly.graph_objs as go
import pandas as pd
import datetime
# TODO: Add ratio yield switch
# TODO: Add enterprise value
# add data table

class Storage:
    def __init__(self):
        self.previous_request = ["MSFT"]

    def update(self, symbol, metric, mc_ev):
        request = [symbol,metric, mc_ev]
        print("Request: ", request)
        if request[0] != self.previous_request[0] or self.previous_request == []:
            print("Requesting data...")
            self.df_daily, self.df_yearly, self.df_est, self.currency = req_handle(request[0])
            self.previous_request = request
            print("Data received.")
        print("Processing data...")
        processing_request = [self.df_daily, self.df_yearly,
                              self.df_est, *request, self.currency]
        trace_base, trace_ratio, pe, pe_norm, grw, grw_exp = data_processing(
            *processing_request)
        print("Data processed.")
        return trace_base, trace_ratio, pe, pe_norm, grw, grw_exp

df_ticker=pd.read_csv('spx.csv',usecols=[1,2]) 
df_ticker["label"] = df_ticker["label"] + " (" + df_ticker["value"] + ")"
dict_data = df_ticker.to_dict('records')

init_fig = {'data': [], 'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis={
    'showticklabels': False, 'ticks': '', 'showgrid': False, 'zeroline': False}, yaxis={'showticklabels': False, 'ticks': '', 'showgrid': False, 'zeroline': False})}
strg = Storage()
PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"
app = dash.Dash('FunViz', external_stylesheets=[dbc.themes.DARKLY]) 
app.title = "FunViz"

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <script data-ad-client="ca-pub-4596163412984698" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


app.layout = html.Div([
    dbc.Row([
            dbc.Label('      '),
            ], style={'background-color': 'rgb(50,50,50)'}),
    dbc.Row([
        dbc.Col([html.Img(src=PLOTLY_LOGO, height="90px")], width="auto"),
        dbc.Col([html.H2("FunViz"), html.Div(html.Label(
            "FunViz 2.0 (beta)"), style={'font-size': 13})], width="auto"),
        dbc.Col([
            html.Label('Metric: '),
            html.Div([dcc.Dropdown(
                id='metric-input',
                options=[
                    {'label': u'EPS', 'value': 'EPS'},
                    {'label': u'FCF', 'value': 'FCF','disabled': True},
                    {'label': u'OCF', 'value': 'OCF','disabled': True},
                ],
                value='EPS'
            )], style={'color': 'black', 'width': '120px', 'height': '40px'}),
        ], width="auto"),
        dbc.Col([
            html.Label('Stock: '),
            html.Div([dcc.Dropdown(id="ticker-input", options=[*dict_data
                    #{'label': u'Apple (AAPL)', 'value': 'AAPL'},
                ],
                value='AAPL'
                )], style={'color': 'black', 'width': '240px', 'height': '40px'}),
        ], width="auto"),
        dbc.Col([
            dbc.Tooltip(
                "If enabled, expected growth rate "
                "is used for multiple calculation, otherwise historical growth rate is used.",
                target="mc_ev-switch",
            ),
            html.Div([
                ToggleSwitch(id='mc_ev-switch',
                              vertical=True, value=False, label='EV', labelPosition="top"), #color='rgb(55, 90, 127);'
                              dbc.Label('Market Cap.'),
            ], id='bool-switch-output')
        ], width="auto"),
        dbc.Col([
            dbc.Button("Update", id="update-input", size="lg"),
        ], width="auto"),
        dbc.Col([
            dbc.Nav([
                dbc.NavItem(dbc.NavLink(
                    "FunViz 1.0", active=True, href="www.tobigs.de", external_link=True)),
            ], pills=True),
        ], width="auto"),
        dbc.Col([
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Sponsor", active=True,
                                        href="http://paypal.me/tobigsIO")),
            ], pills=True),
        ], width="auto"),
    ], justify="between", align="center", style={'background-color': 'rgb(50,50,50)'}
    ),
    dbc.Row([
        dbc.Label('      '),
    ], style={'background-color': 'rgb(50,50,50)'}),
    dbc.Row([
            dbc.Label('      '),
            ]),
    dbc.Row([
        dbc.Col([
            dbc.Label('Multiple'),
            html.Div(dbc.Input(id='pe', type="text"), style={'width': '100px'})
        ], width="auto"),

        dbc.Col([
            dbc.Label('Normal Multiple'),
            html.Div(dbc.Input(id='pe_norm', type="text"),
                     style={'width': '100px'})
        ], width="auto"),

        dbc.Col([
            dbc.Label('Growth Rate'),
            html.Div(dbc.Input(id='grw', type="text"),
                     style={'width': '100px'})
        ], width="auto"),

        dbc.Col([
            dbc.Label('exp. Growth Rate'),
            html.Div(dbc.Input(id='grw_exp', type="text"),
                     style={'width': '100px'}),
        ], width="auto"),
    ], justify="center", align="center"),
    dbc.Row([
            dbc.Label('      '),
            ]),
    dbc.Row([dbc.Alert(
        "Couldn't find any stocks matching your request or symbol is not supported. Use finance.yahoo.com to check symbol.",
        id="alert",
        dismissable=True,
        fade=True,
        color="warning",
        is_open=False,
    )], justify="center"),
    dcc.Graph(id='graph-base', figure=init_fig),
    dcc.Graph(id='graph-ratio', figure=init_fig),
])


@app.callback([
    Output('graph-base', 'figure'),
    Output('graph-ratio', 'figure'),
    Output('pe', 'value'),
    Output('pe_norm', 'value'),
    Output('grw', 'value'),
    Output('grw_exp', 'value'),
    Output('alert', 'is_open')],
    [Input('update-input', 'n_clicks')],
    [State('ticker-input', 'value'),
     State('metric-input', 'value'),
     State('mc_ev-switch', 'value')]
)
def update_graph_output(n_clicks, symbol, metric, mc_ev):
    print(symbol, metric, mc_ev)
    try:
        figure, figure_ratio, pe, pe_norm, grw, grw_exp = strg.update(
            symbol, metric, mc_ev)
        print("Success.")
        return figure, figure_ratio, str(pe), str(pe_norm), str(grw), str(grw_exp), False
    except Exception as ex:
        print("Main App Failure:", ex)
        return init_fig, init_fig, None, None, None, None, True

'''
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
'''


if __name__ == '__main__':
    app.run_server(debug=False)
