import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import math

# --- CONSTANTS ---
# NEC Table 310.15(B)(16) (Copper)
NEC_TABLE_COPPER = {
    '14': {'60': 15, '75': 20, '90': 25},
    '12': {'60': 20, '75': 25, '90': 30},
    '10': {'60': 30, '75': 35, '90': 40},
    '8':  {'60': 40, '75': 50, '90': 55},
    '6':  {'60': 55, '75': 65, '90': 75},
    '4':  {'60': 70, '75': 85, '90': 95},
    '3':  {'60': 85, '75': 100, '90': 115},
    '2':  {'60': 95, '75': 115, '90': 130},
    '1':  {'60': 110, '75': 130, '90': 145},
    '1/0': {'60': 125, '75': 150, '90': 170},
    '2/0': {'60': 145, '75': 175, '90': 195},
    '3/0': {'60': 165, '75': 200, '90': 225},
    '4/0': {'60': 195, '75': 230, '90': 260},
    '250': {'60': 215, '75': 255, '90': 290},
    '300': {'60': 240, '75': 285, '90': 320},
    '350': {'60': 260, '75': 310, '90': 350},
    '400': {'60': 280, '75': 335, '90': 380},
    '500': {'60': 320, '75': 380, '90': 430},
    '600': {'60': 350, '75': 420, '90': 475},
    '700': {'60': 385, '75': 460, '90': 520},
    '750': {'60': 400, '75': 475, '90': 535},
    '800': {'60': 410, '75': 490, '90': 555},
    '900': {'60': 435, '75': 520, '90': 585},
    '1000': {'60': 455, '75': 545, '90': 615},
}

# NEC Chapter 9 Table 5 (XHHW-2) - Approximate Diameters
NEC_DIAMETERS_XHHW2 = {
    '14': 0.133, '12': 0.152, '10': 0.176, '8': 0.236,
    '6': 0.274,  '4': 0.322,  '3': 0.350,  '2': 0.382, '1': 0.442,
    '1/0': 0.482, '2/0': 0.528, '3/0': 0.580, '4/0': 0.637,
    '250': 0.711, '300': 0.766, '350': 0.817, '400': 0.864,
    '500': 0.949, '600': 1.051, '700': 1.121, '750': 1.156,
    '800': 1.191, '900': 1.251, '1000': 1.317
}

WIRE_SIZES = list(NEC_TABLE_COPPER.keys())
TEMP_RATINGS = ['60', '75', '90']

# --- APP INIT ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
server=app.server
app.title = "Electrical Load & Wireway Sizing"

# --- HELPER COMPONENTS ---
def make_card(title, content, color="light"):
    return dbc.Card([
        dbc.CardHeader(html.H5(title, className="m-0"), className="bg-light"),
        dbc.CardBody(content)
    ], className="mb-4 shadow-sm border-0")

def make_input_group(label, id_name, value, unit=None, note=None):
    return html.Div([
        dbc.Label(label, html_for=id_name, className="fw-bold text-muted small text-uppercase mb-1"),
        dbc.InputGroup([
            dbc.Input(id=id_name, type="number", value=value, step=0.001),
            dbc.InputGroupText(unit) if unit else None
        ], size="sm"),
        html.Small(note, className="text-muted mt-1 d-block") if note else None
    ], className="mb-3")

# --- LAYOUT ---
app.layout = dbc.Container([
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Electrical Load & Wireway Sizing", className="display-6 fw-bold text-primary"),
            html.P("Automated NEC Calculations for HD5AC System", className="lead text-muted"),
        ], width=12, md=8),
        dbc.Col([
            dbc.Button("Print / Export", id="btn-print", color="outline-secondary", className="float-end")
        ], width=12, md=4, className="d-flex align-items-center justify-content-md-end")
    ], className="py-4 border-bottom mb-4"),

    # Status Banners
    dbc.Row([
        dbc.Col(id="ampacity-status-col", width=12, md=6),
        dbc.Col(id="fill-status-col", width=12, md=6),
    ], className="mb-4"),

    # Main Grid
    dbc.Row([
        # Left Column: Inputs
        dbc.Col([
            # System Parameters Card
            make_card("System Parameters", [
                dbc.Row([
                    dbc.Col(make_input_group("HD5AC FLA", "input-fla", 2886.8, "A", "Baseline requirement"), md=6),
                    dbc.Col(make_input_group("OCPD Trip Setting", "input-ocpd", 3000, "A", "Must be > FLA"), md=6),
                    dbc.Col(make_input_group("Parallel Conductors (Per Phase)", "input-parallel", 6, "qty"), md=6),
                    dbc.Col(make_input_group("Number of Wireways", "input-wireways", 2, "qty"), md=6),
                    dbc.Col(make_input_group("Ambient Temp Correction", "input-temp-correction", 0.96, "factor", "NEC Table 310.15(B)(2)(A)"), md=12),
                ])
            ]),

            # Cable Configuration Card
            make_card("Cable Configuration", [
                
                # Phase Section
                html.Div([
                    html.Div("Phase Conductors", className="fw-bold text-primary mb-2 text-uppercase small"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Size (AWG/kcmil)", className="small fw-bold text-muted"),
                            dbc.Select(id="select-phase-size", options=[{'label': s, 'value': s} for s in WIRE_SIZES], value='750', size="sm")
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Temp Rating", className="small fw-bold text-muted"),
                            dbc.Select(id="select-temp-rating", options=[{'label': f"{t}°C", 'value': t} for t in TEMP_RATINGS], value='90', size="sm")
                        ], md=4),
                        dbc.Col(make_input_group("Base Ampacity", "input-cable-ampacity", 535, "A"), md=4),
                    ]),
                    html.Div(id="phase-diam-container", children=[
                        # Hidden calculation/display for phase diameter, logic handles it in callback
                         dbc.Label("Phase Diameter (Auto)", className="small fw-bold text-muted mt-2"),
                         dbc.InputGroup([
                             dbc.Input(id="input-phase-diam", type="number", value=1.156, step=0.001),
                             dbc.InputGroupText("in")
                         ], size="sm")
                    ])
                ], className="p-3 bg-light rounded mb-3 border"),

                # Ground Section
                html.Div([
                    html.Div("Ground Conductors", className="fw-bold text-primary mb-2 text-uppercase small"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Size (AWG/kcmil)", className="small fw-bold text-muted"),
                            dbc.Select(id="select-ground-size", options=[{'label': s, 'value': s} for s in WIRE_SIZES], value='500', size="sm")
                        ], md=6),
                         dbc.Col([
                             dbc.Label("Ground Diameter", className="small fw-bold text-muted"),
                             dbc.InputGroup([
                                 dbc.Input(id="input-ground-diam", type="number", value=0.949, step=0.001),
                                 dbc.InputGroupText("in")
                             ], size="sm")
                         ], md=6),
                    ]),
                    make_input_group("Ground Qty (Per Raceway)", "input-ground-qty", 1, "qty")
                ], className="p-3 bg-light rounded border"),
            ])
        ], lg=8),

        # Right Column: Results
        dbc.Col([
            # Ampacity Results
            dbc.Card([
                dbc.CardHeader("Calculated Ampacity", className="fw-bold"),
                dbc.CardBody([
                    html.Div("Total Capacity", className="small text-muted text-uppercase fw-bold text-center"),
                    html.H2(id="result-ampacity-display", className="display-4 fw-bold text-center my-3"),
                    html.Div(id="result-ampacity-calc-text", className="small text-muted text-center")
                ])
            ], className="mb-4 shadow-sm border-0", id="card-ampacity-result"),

            # Wireway Results
            dbc.Card([
                dbc.CardHeader("Wireway Sizing", className="fw-bold"),
                dbc.CardBody([
                    make_input_group("Wireway Internal Area", "input-wireway-area", 56.27, "in²"),
                    
                    html.Div([
                        dbc.Row([
                            dbc.Col("Phase Area:", className="text-muted"),
                            dbc.Col(id="display-phase-area", className="fw-bold text-end")
                        ], className="mb-1"),
                        dbc.Row([
                            dbc.Col("Ground Area:", className="text-muted"),
                            dbc.Col(id="display-ground-area", className="fw-bold text-end")
                        ], className="mb-1"),
                        html.Hr(className="my-2"),
                        dbc.Row([
                            dbc.Col("Total Fill Area:", className="fw-bold text-dark"),
                            dbc.Col(id="display-total-fill", className="fw-bold text-end")
                        ]),
                    ], className="bg-light p-3 rounded small mb-3 border"),

                    html.Div("Current Fill Percentage", className="small text-muted text-uppercase fw-bold text-center"),
                    html.H2(id="result-fill-display", className="display-4 fw-bold text-center my-2"),
                    html.Div("Limit: 20%", className="text-center small text-muted")

                ])
            ], className="shadow-sm border-0", id="card-fill-result")

        ], lg=4)
    ]),

    html.Footer("This tool assumes standard NEC conditions. Verify with official codes.", className="text-center text-muted small py-4")

], fluid=True, className="bg-light min-vh-100")


# --- CALLBACKS ---

# 1. Update Phase Ampacity & Diameter based on Dropdowns
@app.callback(
    [Output("input-cable-ampacity", "value"),
     Output("input-phase-diam", "value")],
    [Input("select-phase-size", "value"),
     Input("select-temp-rating", "value")],
    [State("input-cable-ampacity", "value"),
     State("input-phase-diam", "value")]
)
def update_phase_specs(size, temp, current_amp, current_diam):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_amp, current_diam
    
    # Defaults
    new_amp = current_amp
    new_diam = current_diam

    # Lookup Ampacity
    if size in NEC_TABLE_COPPER and temp in NEC_TABLE_COPPER[size]:
        new_amp = NEC_TABLE_COPPER[size][temp]
    
    # Lookup Diameter
    if size in NEC_DIAMETERS_XHHW2:
        new_diam = NEC_DIAMETERS_XHHW2[size]
        
    return new_amp, new_diam

# 2. Update Ground Diameter based on Dropdown
@app.callback(
    Output("input-ground-diam", "value"),
    Input("select-ground-size", "value"),
    State("input-ground-diam", "value")
)
def update_ground_specs(size, current_diam):
    if size in NEC_DIAMETERS_XHHW2:
        return NEC_DIAMETERS_XHHW2[size]
    return current_diam

# 3. Main Calculation & UI Updates
@app.callback(
    [
        # Results
        Output("result-ampacity-display", "children"),
        Output("result-ampacity-display", "className"),
        Output("result-ampacity-calc-text", "children"),
        Output("card-ampacity-result", "className"), # For border color
        
        Output("display-phase-area", "children"),
        Output("display-ground-area", "children"),
        Output("display-total-fill", "children"),
        Output("result-fill-display", "children"),
        Output("result-fill-display", "className"),
        Output("card-fill-result", "className"), # For border color

        # Status Banners
        Output("ampacity-status-col", "children"),
        Output("fill-status-col", "children"),
    ],
    [
        Input("input-fla", "value"),
        Input("input-ocpd", "value"),
        Input("input-parallel", "value"),
        Input("input-wireways", "value"),
        Input("input-temp-correction", "value"),
        Input("input-cable-ampacity", "value"),
        Input("input-phase-diam", "value"),
        Input("input-ground-diam", "value"),
        Input("input-ground-qty", "value"),
        Input("input-wireway-area", "value"),
    ]
)
def calculate_all(fla, ocpd, parallel, num_wireways, temp_corr, 
                  base_ampacity, phase_diam, ground_diam, ground_qty, wireway_area):
    
    # Safety checks for None/Zero
    if not all([fla, ocpd, parallel, num_wireways, base_ampacity, phase_diam, ground_diam, wireway_area]):
        return ["---"] * 11

    # --- Calculations ---
    
    # 1. Ampacity
    calculated_ampacity = base_ampacity * parallel * temp_corr
    is_ampacity_safe = calculated_ampacity > ocpd
    
    # 2. Fill
    conductors_in_raceway = (parallel / num_wireways) * 3
    phase_area = math.pi * ((phase_diam/2)**2)
    ground_area = math.pi * ((ground_diam/2)**2)
    
    total_phase_area = conductors_in_raceway * phase_area
    total_ground_area = ground_qty * ground_area
    total_fill_area = total_phase_area + total_ground_area
    
    fill_percentage = (total_fill_area / wireway_area) * 100
    is_fill_safe = fill_percentage <= 20

    # --- UI Formatting ---

    # Ampacity Styles
    amp_color_class = "text-success" if is_ampacity_safe else "text-danger"
    amp_card_class = f"mb-4 shadow-sm border-top-0 border-end-0 border-bottom-0 border-start-4 {'border-success' if is_ampacity_safe else 'border-danger'}"
    amp_calc_text = f"Base ({base_ampacity}A) × Parallel ({parallel}) × Corr ({temp_corr})"
    
    # Fill Styles
    fill_color_class = "text-success" if is_fill_safe else "text-danger"
    fill_card_class = f"shadow-sm border-top-0 border-end-0 border-bottom-0 border-start-4 {'border-success' if is_fill_safe else 'border-danger'}"

    # Status Banners
    amp_banner = dbc.Alert(
        [html.H5("Ampacity Check: PASS" if is_ampacity_safe else "Ampacity Check: FAIL", className="alert-heading"),
         html.P(f"Calculated ({calculated_ampacity:.1f} A) > OCPD ({ocpd} A)")],
        color="success" if is_ampacity_safe else "danger"
    )

    fill_banner = dbc.Alert(
        [html.H5("Wireway Fill: PASS" if is_fill_safe else "Wireway Fill: FAIL", className="alert-heading"),
         html.P(f"Fill ({fill_percentage:.1f}%) is {'within' if is_fill_safe else 'exceeds'} 20% limit")],
        color="success" if is_fill_safe else "danger"
    )

    return (
        f"{calculated_ampacity:.1f} A",
        f"display-4 fw-bold text-center my-3 {amp_color_class}",
        amp_calc_text,
        amp_card_class,
        
        f"{total_phase_area:.2f} in²",
        f"{total_ground_area:.2f} in²",
        f"{total_fill_area:.2f} in²",
        f"{fill_percentage:.1f}%",
        f"display-4 fw-bold text-center my-2 {fill_color_class}",
        fill_card_class,

        amp_banner,
        fill_banner
    )

# 4. Clientside Callback for Print
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.print();
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("btn-print", "id"),  # Dummy output to satisfy callback requirement
    Input("btn-print", "n_clicks"),
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True)