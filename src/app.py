from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from PIL import Image
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go



app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP], 
            meta_tags=[{'name': 'viewport',
                        'content': 'width=device-width, initial-scale=1.0'}])

app.title = "Himanshu Deshpande"

server = app.server



app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.P("PS - Handcrafted this website from scratch—no templates, just caffeine and code.😎🛠️ I'd love to hear what you think, so feel free to drop me a note.", 
                       style={"textAlign": "center", 'font-size': '12px','font-style': 'italic'})
                , xs=12, sm=12, md=12, lg=12, xl=12, align="center"),
    ], justify="center"),

    html.Br(),

], fluid=True)


if __name__ == "__main__":
    app.run(debug=True)