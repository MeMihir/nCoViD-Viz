import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import numpy as np
import pandas as pd
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.express as px
import cufflinks as cf


def non_cumulative(l):
    for i in range (len(l)-1, 0, -1):
        l[i] -= l[i-1]
    return l

def sort_by_country(country):
    temp_df = df[df['Country/Region'] == country]
    temp_df = temp_df.drop('Province/State', axis=1).drop('SNo', axis=1)
    temp_df = temp_df.groupby(['Country/Region', 'ObservationDate'], as_index=False).aggregate(['sum'], )
    temp_df.columns = df.columns[4:]
    temp_df= temp_df[temp_df['Confirmed'] != 0]
    temp_df['ConfirmedPerDay'] = non_cumulative(temp_df['Confirmed'].copy())
    temp_df['DeathsPerDay'] = non_cumulative(temp_df['Deaths'].copy())
    temp_df['RecoveredPerDay'] = non_cumulative(temp_df['Recovered'].copy())
    temp_df['Country'] = [country]*temp_df.shape[0]
    return temp_df



# df = pd.read_csv('./covid_19_data.csv')
df = pd.read_csv('./covid_19_data/covid_19_data.csv')
df['Active'] = df['Confirmed'] - df['Deaths'] - df['Recovered']
df['ObservationDate'] = pd.to_datetime(df['ObservationDate'])

df_country = sort_by_country(df['Country/Region'].value_counts().index[0])

for i in range(1, len(df['Country/Region'].value_counts())):
    temp = sort_by_country(df['Country/Region'].value_counts().index[i])
    df_country = pd.concat([df_country, temp])

df_country['Date'] = list(map(lambda x: x[1] ,df_country.index.values))
df_country = df_country.sort_index()

df['ConfirmedPerDay'] = non_cumulative(df['Confirmed'].copy())
df['DeathsPerDay'] = non_cumulative(df['Deaths'].copy())
df['RecoveredPerDay'] = non_cumulative(df['Recovered'].copy())

map_df = df_country.copy()
map_df['DateStr'] = map_df['Date'].apply(lambda x: str(x).split(' ')[0])
map_df.sort_values(by='Date', inplace=True)


app = dash.Dash(__name__)

mapOptions = [{'label': 'Confirmed', 'value': 'Confirmed'}, {'label': 'Deaths', 'value': 'Deaths'}, {'label': 'Active', 'value': 'Active'}, {'label': 'Recovered', 'value': 'Recovered'}]
countries = [{'label': country, 'value': country} for country in df_country['Country'].unique()]

app.layout = html.Div([
    html.H1('Data Visualization CSE3020', className="app--title"),
    html.H3('These are a few visualizations of the widespread pandemic COVID19. Presented by - Ananya Ganesh [18BCE0139], Mihir Pavuskar [18BCE0159], Aashraya Singhal [18BCE0171]', className = "app--subt"),
    html.H1('COVID19 Visualization Timeline'),
    html.Div([
        html.H3('Select Type of Display : '),
        dcc.Dropdown( 
            id='mapsDispType',
            options=mapOptions,
            value='Confirmed',
            multi=False,
            className="dropdown"
        ),
        dcc.Graph(id="map-graph")
    ]),
    html.Div([
        html.H1('Improvement'),
        html.H3('The following graph is a logarithmic plot of the timeline of COVID19. You can double-click on the countries on the right to view their inidividual timeline'),
        dcc.Graph(
            id = 'logPlot',            
            figure = px.line(df_country, x='Confirmed', y='ConfirmedPerDay', color='Country', log_x=True, log_y=True)
        )
    ]),
    html.Div([
        html.Div([
            html.H3('Select Country : '),
            dcc.Dropdown(
                id='countrySpreadPlot',
                options=countries,
                value="India",
                multi=False
            )
        ]),
        dcc.Graph(id="spreadPlot"),
        dcc.Graph(id="spreadPlotDaily")
    ]),
    html.Div([
        html.Div([
        html.H3('Select Type of Display : '),
        dcc.Dropdown( 
            id='barDispType',
            options=mapOptions,
            value='Confirmed',
            multi=False
        )
    ]),
        html.Div([
            dcc.Dropdown(
            id='barDispSum',
            options=[{'label': 'PerDay', 'value':'PerDay'}, {'label' : 'Cumulative', 'value': ''}],
            value='',
            multi=False
        )
        ]),
        dcc.Graph(id="barPlot")
    ])
])

@app.callback(Output("map-graph", "figure"), [Input('mapsDispType', "value")])
def make_map(disp_map):
    return px.choropleth(map_df, locations="Country", 
                    locationmode='country names', color=disp_map, 
                    hover_name="Country", 
                    animation_frame='DateStr',
                    # color_continuous_scale="peach", 
                    title=f'Countries with {disp_map} Cases')

@app.callback(Output("spreadPlot", "figure"), [Input('countrySpreadPlot', 'value')])
def make_spread_plot(country):
    spread_data = df_country[df_country['Country']==country]
    spread_data.set_index('Date', inplace=True)
    # fig = 
    return spread_data[['Confirmed', 'Deaths', 'Recovered']].iplot(kind='spread', asFigure=True)

@app.callback(Output("spreadPlotDaily", "figure"), [Input('countrySpreadPlot', 'value')])
def make_daily_spread_plot(country):
    spread_data = df_country[df_country['Country']==country]
    spread_data.set_index('Date', inplace=True)
    return spread_data[['ConfirmedPerDay', 'DeathsPerDay', 'RecoveredPerDay']].iplot(kind='spread', asFigure=True)

@app.callback(Output("barPlot", "figure"), [Input('barDispType', 'value'), Input('barDispSum', 'value')])
def make_bar_plot(dispType, dispSum):
    print(dispSum, dispType)
    return px.bar(df_country, x='Date', y=f'{dispType}{dispSum}', color='Country')

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8051', debug=True)