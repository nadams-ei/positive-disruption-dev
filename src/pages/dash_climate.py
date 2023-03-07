import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/Climate", title="Climate", name="Climate")

df = pd.read_csv(
    "~/positive-disruption/podi/data/output/climate/climate_output.csv"
)

layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Dataset", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "climate_output",
                                "climate_output_co2e",
                            ],
                            "climate_output",
                            id="dataset",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Model", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.model.unique().tolist(),
                            df.model.unique().tolist(),
                            id="model",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Scenario", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.scenario.unique().tolist(),
                            df.scenario.unique().tolist()[1],
                            id="scenario",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.region.unique().tolist(),
                            df.region.unique().tolist(),
                            id="region",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Variable", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.variable.unique().tolist(),
                            df.variable.unique().tolist()[0],
                            id="variable",
                            multi=False,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Gas", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.gas.unique().tolist() + ["CO2e"],
                            df.gas.unique().tolist() + ["CO2e"],
                            id="gas",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log"],
                            "Linear",
                            id="yaxis_type",
                            inline=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Group by", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "model",
                                "scenario",
                                "region",
                                "variable",
                                "gas",
                                "unit",
                            ],
                            "gas",
                            id="groupby",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Chart Type", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            {"none": "line", "tonexty": "area"},
                            "none",
                            id="chart_type",
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        dcc.Graph(id="graphic-climate"),
    ]
)


@callback(
    Output("graphic-climate", "figure"),
    Input("dataset", "value"),
    Input("model", "value"),
    Input("scenario", "value"),
    Input("region", "value"),
    Input("variable", "value"),
    Input("gas", "value"),
    Input("yaxis_type", "value"),
    Input("groupby", "value"),
    Input("chart_type", "value"),
)
def update_graph(
    dataset,
    model,
    scenario,
    region,
    variable,
    gas,
    yaxis_type,
    groupby,
    chart_type,
):
    stack_type = {"none": None, "tonexty": "1"}

    df = pd.read_csv(
        "~/positive-disruption/podi/data/output/climate/" + dataset + ".csv"
    )

    yaxis_unit = {
        "Concentration": "PPM",
        "Radiative forcing": "W/m2",
        "Temperature change": "C",
    }

    fig = go.Figure()

    filtered_df = (
        (
            pd.DataFrame(df)
            .set_index(
                [
                    "model",
                    "scenario",
                    "region",
                    "variable",
                    "gas",
                    "unit",
                ]
            )
            .loc[
                model,
                scenario,
                region,
                variable,
                gas,
            ]
            .groupby([groupby])
            .sum()
        )
    ).T.fillna(0)

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df,
        id_vars="year",
        var_name=[groupby],
        value_name=yaxis_unit[variable],
    )

    for sub in filtered_df[groupby].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(width=2, dash="dash"),
                x=filtered_df["year"].unique().astype(int),
                y=filtered_df[filtered_df[groupby] == sub][
                    yaxis_unit[variable]
                ].values,
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
                legendgroup=sub,
            )
        )
        fig.add_trace(
            go.Scatter(
                name=sub + ", Historical",
                line=dict(width=2, color="black"),
                x=filtered_df["year"]
                .unique()
                .astype(int)[filtered_df["year"].unique().astype(int) <= 2022],
                y=filtered_df[filtered_df[groupby] == sub][
                    yaxis_unit[variable]
                ].values,
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=False,
                legendgroup=sub,
            )
        )

    fig.update_layout(
        title={
            "text": str(variable) + ", by " + str(groupby),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": str(groupby) + ", " + str(yaxis_unit[variable])},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    yaxis_title = {
        "PPM": "Concentration, ",
        "C": "Temperature Anomaly, ",
        "W/m2": "Radiative Forcing, ",
    }

    fig.update_yaxes(
        title=yaxis_title[yaxis_unit[variable]] + str(yaxis_unit[variable]),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return fig