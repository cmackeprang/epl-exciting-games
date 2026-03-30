#!/usr/bin/env python3
"""
EPL Exciting Game Finder - Dash Mantine UI
A web interface for finding exciting Premier League matches.
"""

import asyncio
from datetime import datetime
from dash import Dash, html, Input, Output, State, callback, dcc
import dash_mantine_components as dmc
from exciting_games import ExcitingGameFinder


# Initialize the Dash app with Mantine
app = Dash(__name__)
app.title = "EPL Exciting Game Finder"

# Expose the Flask server for production deployment (gunicorn)
server = app.server

# Define the layout
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "dark"},
    children=[
        dmc.Container(
            size="xl",
            px="md",
            children=[
                # Header
                dmc.Space(h=30),
                html.H1(
                    "⚽ EPL Exciting Game Finder",
                    style={"textAlign": "center", "marginBottom": "10px"}
                ),
                html.P(
                    "Discover exciting Premier League matches without spoiling the results",
                    style={"textAlign": "center", "marginBottom": "30px", "fontSize": "1.2rem", "opacity": "0.7"}
                ),
                
                # Input Card
                dmc.Card(
                    children=[
                        dmc.CardSection(
                            html.H3("Search Parameters", style={"margin": "0"}),
                            withBorder=True,
                            inheritPadding=True,
                            py="xs"
                        ),
                        dmc.Space(h=20),
                        dmc.NumberInput(
                            id="days-input",
                            label="How many days back should I check?",
                            description="Enter a number between 1 and 90 days",
                            value=7,
                            min=1,
                            max=90,
                            step=1,
                            style={"width": "100%"},
                        ),
                        dmc.Space(h=20),
                        dmc.Switch(
                            id="debug-switch",
                            label="Debug Mode (Show xG and scores)",
                            checked=False,
                            size="md",
                        ),
                        dmc.Space(h=20),
                        dmc.Button(
                            "Find Exciting Matches",
                            id="search-button",
                            fullWidth=True,
                            size="lg",
                            variant="gradient",
                            gradient={"from": "teal", "to": "lime", "deg": 105},
                        ),
                    ],
                    withBorder=True,
                    shadow="sm",
                    radius="md",
                    style={"marginBottom": "30px"}
                ),
                
                # Loading overlay
                dmc.LoadingOverlay(
                    id="loading-overlay",
                    visible=False,
                ),
                
                # Results container
                html.Div(id="results-container"),
                
                # Store for async results
                dcc.Store(id="analysis-store"),
                
                dmc.Space(h=50),
            ]
        )
    ]
)


def create_match_card(game: dict, index: int, debug: bool) -> dmc.Card:
    """Create a card component for a single match."""
    # Format date
    try:
        match_date = datetime.strptime(game['date'], '%Y-%m-%d %H:%M:%S')
        date_str = match_date.strftime('%A, %B %d, %Y')
    except:
        date_str = game['date']
    
    # Create reasons badges
    reason_badges = [
        dmc.Badge(
            reason,
            color="teal",
            variant="light",
            size="md",
            style={"marginRight": "5px", "marginBottom": "5px"}
        )
        for reason in game['reasons']
    ]
    
    # Create debug info if enabled
    debug_content = []
    if debug:
        debug_content = [
            dmc.Space(h=15),
            dmc.Divider(label="Debug Information", labelPosition="center"),
            dmc.Space(h=10),
            html.P("Why it's exciting:", style={"fontWeight": "500", "fontSize": "0.9rem", "opacity": "0.7", "margin": "5px 0"}),
            html.Div(reason_badges, style={"marginBottom": "10px"}),
            html.Div([
                html.P(f"Score: {game['home_goals']}-{game['away_goals']}", style={"margin": "5px 0", "fontWeight": "500"}),
                html.P(f"xG: {game['home_xg']:.2f} - {game['away_xg']:.2f}", style={"margin": "5px 0", "opacity": "0.7"}),
                dmc.Badge(
                    f"Excitement: {game['excitement_score']}",
                    color="grape",
                    variant="filled"
                )
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "flexWrap": "wrap", "gap": "10px"})
        ]
    
    return dmc.Card(
        children=[
            html.Div([
                dmc.Badge(
                    f"#{index}",
                    color="blue",
                    variant="filled",
                    size="lg"
                ),
                html.Span(date_str, style={"fontSize": "0.9rem", "opacity": "0.7"})
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
            dmc.Space(h=10),
            html.H3(
                f"{game['home_team']} vs {game['away_team']}",
                style={"margin": "10px 0"}
            ),
            *debug_content
        ],
        withBorder=True,
        shadow="md",
        radius="md",
        style={"marginBottom": "20px"},
        p="lg"
    )


@callback(
    Output("analysis-store", "data"),
    Output("loading-overlay", "visible", allow_duplicate=True),
    Input("search-button", "n_clicks"),
    State("days-input", "value"),
    State("debug-switch", "checked"),
    prevent_initial_call=True
)
def run_analysis(n_clicks, days_back, debug_mode):
    """Run the analysis when button is clicked."""
    if n_clicks is None:
        return None, False
    
    # Show loading
    # Run the analysis
    finder = ExcitingGameFinder(days_back=days_back, debug=debug_mode)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        exciting_games = loop.run_until_complete(finder.find_exciting_games())
    finally:
        loop.close()
    
    return {"games": exciting_games, "debug": debug_mode}, False


@callback(
    Output("results-container", "children"),
    Output("loading-overlay", "visible"),
    Input("analysis-store", "data"),
)
def display_results(data):
    """Display the analysis results."""
    if data is None or not data.get("games"):
        return html.Div(), False
    
    games = data["games"]
    debug = data.get("debug", False)
    
    if not games:
        return dmc.Alert(
            title="No Matches Found",
            color="yellow",
            children=[
                html.P("No particularly exciting matches found in this time window."),
                html.P("Try increasing the number of days or waiting for more games.", style={"marginTop": "10px"})
            ],
        ), False
    
    # Create header
    results_header = dmc.Card(
        children=[
            html.H2(
                f"🏆 Found {len(games)} Exciting Match{'es' if len(games) != 1 else ''}",
                style={"textAlign": "center", "color": "teal", "margin": "0"}
            ),
            html.P(
                "Ranked by excitement score - highest first",
                style={"textAlign": "center", "opacity": "0.7", "fontSize": "0.9rem", "marginTop": "10px", "marginBottom": "0"}
            )
        ],
        withBorder=True,
        shadow="sm",
        radius="md",
        style={"marginBottom": "25px", "background": "linear-gradient(135deg, rgba(0,128,128,0.1) 0%, rgba(0,255,0,0.1) 100%)"},
        p="lg"
    )
    
    # Create match cards
    match_cards = [
        create_match_card(game, idx + 1, debug)
        for idx, game in enumerate(games)
    ]
    
    # Footer note
    footer_note = dmc.Alert(
        children=[
            html.P(
                "💡 Note: Scores and final results are hidden to preserve the excitement!",
                style={"fontWeight": "500", "margin": "5px 0"}
            ),
            html.P(
                "Watch the replays to see how these thrilling matches unfolded.",
                style={"margin": "5px 0"}
            )
        ],
        title="Spoiler-Free Viewing",
        color="blue",
        variant="light",
    ) if not debug else None
    
    return html.Div([results_header] + match_cards + ([footer_note] if footer_note else [])), False


if __name__ == "__main__":
    import os
    
    # Use environment variables for production (Render, etc.)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("ENVIRONMENT", "development") == "development"
    
    print("="*70)
    print("Starting EPL Exciting Game Finder Dashboard...")
    print("="*70)
    print(f"\n🌐 Opening dashboard on {host}:{port}")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    app.run(debug=debug, host=host, port=port)
