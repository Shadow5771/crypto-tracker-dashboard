import pandas as pd
from datetime import datetime
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import os

# ----------------- Initialize App ----------------- #
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

DATA_FILE = "data/crypto_snapshot.csv"
HISTORY_FILE = "data/crypto_history.csv"
ALERT_FILE = "logs/alerts.csv"

# ----------------- Load Data Safely ----------------- #
def load_snapshot():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    df = pd.read_csv(DATA_FILE)
    for col in ["current_price","price_change_24h","market_cap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.head(60)

def load_history(coin_id):
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(HISTORY_FILE, dtype=str, error_bad_lines=False)
    except Exception:
        return pd.DataFrame()
    expected_cols = ["id","symbol","name","current_price","market_cap","total_volume","price_change_24h","scrape_time"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
    df = df[df["id"] == coin_id]
    if df.empty:
        return df
    df["scrape_time"] = pd.to_datetime(df["scrape_time"], errors="coerce")
    df["current_price"] = pd.to_numeric(df["current_price"], errors="coerce").fillna(0)
    df = df.dropna(subset=["scrape_time"])
    return df.sort_values("scrape_time")

def load_alerts():
    if not os.path.exists(ALERT_FILE):
        return pd.DataFrame()
    try:
        return pd.read_csv(ALERT_FILE, dtype=str, error_bad_lines=False)
    except Exception:
        return pd.DataFrame()

# ----------------- Themes ----------------- #
LIGHT = {"CARD_BG":"#ffffff","TEXT":"#111111","ACCENT":"#3b82f6","GRID":"rgba(0,0,0,0.05)"}
DARK  = {"CARD_BG":"#1a1a1a","TEXT":"#eeeeee","ACCENT":"#00f2ff","GRID":"rgba(255,255,255,0.05)"}

# ----------------- Layout ----------------- #
app.layout = dbc.Container([
    html.H2("🚀 Crypto Tracker", className="text-center my-3"),
    dbc.Row([dbc.Col(dbc.Switch(id="theme-toggle", label="Toggle Theme (Light / Dark)", value=False), width=3)]),
    dbc.Row([dbc.Col(dcc.Dropdown(id="coin-dropdown", placeholder="Select Coin", options=[], className="mb-2"), width=4)]),
    dbc.Row([dbc.Col(html.Div(id="coin-info"), width=4),
             dbc.Col(dcc.Graph(id="price-chart"), width=8)], className="g-3"),
    html.Hr(),
    html.H4("📊 Market Overview (Top 60 Coins)", className="mt-3"),
    dcc.Graph(id="market-table", style={"overflowX":"auto","height":"650px"}),
    html.Hr(),
    html.H4("🚨 Recent Alerts", className="mt-3"),
    dcc.Graph(id="alert-table", style={"overflowX":"auto","height":"250px"}),
    # Auto-refresh
    dcc.Interval(id="interval-component", interval=30*1000, n_intervals=0)
], fluid=True, style={"maxWidth":"1400px"})

# ----------------- Callbacks ----------------- #

# Load dropdown options
@app.callback(Output("coin-dropdown","options"), Input("theme-toggle","value"))
def update_dropdown(theme_toggle):
    df = load_snapshot()
    return [{"label": f"{row['name']} ({row['symbol']})", "value": row["id"]} for _, row in df.iterrows()]

# Coin info + price chart
@app.callback(Output("coin-info","children"), Output("price-chart","figure"),
              Input("coin-dropdown","value"), Input("theme-toggle","value"),
              Input("interval-component","n_intervals"))
def update_coin(coin_id, theme_toggle, n):
    theme = LIGHT if theme_toggle else DARK
    df = load_snapshot()
    if coin_id is None or df.empty:
        return "Select a coin", go.Figure()
    row = df[df["id"]==coin_id].iloc[0]
    history = load_history(coin_id)

    # --- Coin Info Card ---
    info_card = dbc.Card(dbc.CardBody([
        html.H4(f"{row['name']} ({row['symbol']})", style={"color":theme["ACCENT"]}),
        html.H2(f"${row['current_price']:,.2f}", style={"color":theme["TEXT"]}),
        html.H5(f"24h Change: {row['price_change_24h']:.2f}%", 
                style={"color":"#22c55e" if row['price_change_24h']>0 else "#ef4444"})
    ]), style={"background":theme["CARD_BG"], "color":theme["TEXT"]})

    # --- Price Chart ---
    fig = go.Figure()
    if not history.empty:
        fig.add_trace(go.Scatter(
            x=history["scrape_time"],
            y=history["current_price"],
            mode="lines+markers",
            line=dict(width=2,color=theme["ACCENT"]),
            marker=dict(size=4)
        ))
    else:
        fig.add_trace(go.Scatter(
            x=[datetime.utcnow()],
            y=[row['current_price']],
            mode="markers",
            marker=dict(size=6,color=theme["ACCENT"])
        ))

    fig.update_layout(
        height=350, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor=theme["CARD_BG"], paper_bgcolor=theme["CARD_BG"],
        font=dict(color=theme["TEXT"]),
        xaxis=dict(gridcolor=theme["GRID"]),
        yaxis=dict(gridcolor=theme["GRID"], title="Price (USD)")
    )

    return info_card, fig

# Market table with mini sparklines
@app.callback(Output("market-table","figure"), Input("theme-toggle","value"), Input("interval-component","n_intervals"))
def update_market_table(theme_toggle, n):
    theme = LIGHT if theme_toggle else DARK
    df = load_snapshot()
    if df.empty: return go.Figure()

    spark_data = []
    for idx, row in df.iterrows():
        hist = load_history(row['id'])
        if hist.empty:
            spark_data.append([row['current_price']]*7)
        else:
            spark_data.append(hist["current_price"].tail(7).tolist())

    table = go.Figure(data=[go.Table(
        header=dict(values=["Name","Symbol","Price ($)","24h %","Market Cap","Trend"],
                    fill_color=theme["ACCENT"], font=dict(color="black", size=12), align="left"),
        cells=dict(values=[df["name"], df["symbol"],
                           df["current_price"].map(lambda x:f"${x:,.2f}"),
                           df["price_change_24h"].map(lambda x:f"{x:.2f}%"),
                           df["market_cap"].map(lambda x:f"${x:,.0f}"),
                           spark_data],
                   fill_color=theme["CARD_BG"], font=dict(color=theme["TEXT"], size=11), align="left")
    )])
    table.update_layout(height=650, margin=dict(l=5,r=5,t=5,b=5))
    return table

# Alerts table (fallback to top movers if no alerts)
@app.callback(
    Output("alert-table","figure"),
    Input("theme-toggle","value"),
    Input("interval-component","n_intervals")
)
def update_alerts(theme_toggle, n):
    theme = LIGHT if theme_toggle else DARK

    # Try to load real alerts
    try:
        df_alerts = pd.read_csv(ALERT_FILE, dtype=str, error_bad_lines=False)
    except Exception:
        df_alerts = pd.DataFrame()

    if df_alerts.empty:
        # Fallback: top 5 movers by absolute 24h change
        df = load_snapshot()
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False,
                               font=dict(size=16, color=theme["TEXT"]))
            fig.update_layout(plot_bgcolor=theme["CARD_BG"], paper_bgcolor=theme["CARD_BG"])
            return fig

        df_alerts = df.copy()
        df_alerts["price_change_24h"] = df_alerts["price_change_24h"].astype(float).fillna(0)
        df_alerts = df_alerts.reindex(df_alerts["price_change_24h"].abs().sort_values(ascending=False).index)
        df_alerts = df_alerts.head(5)
        df_alerts["price_change_pct"] = df_alerts["price_change_24h"]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df_alerts.columns), fill_color=theme["ACCENT"], font=dict(color="black", size=12), align="left"
        ),
        cells=dict(
            values=[df_alerts[col].fillna("") for col in df_alerts.columns],
            fill_color=theme["CARD_BG"], font=dict(color=theme["TEXT"], size=11), align="left"
        )
    )])
    fig.update_layout(height=250, margin=dict(l=5,r=5,t=5,b=5))
    return fig

# ----------------- Run App ----------------- #
if __name__=="__main__":
    app.run(debug=True)