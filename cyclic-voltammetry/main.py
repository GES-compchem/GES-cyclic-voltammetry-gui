import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from io import StringIO, BytesIO
from tempfile import NamedTemporaryFile as tmp
from typing import Dict, Tuple

from core.bytestream_tools import BytesStreamManager
from echemsuite.cyclicvoltammetry.read_input import CyclicVoltammetry


# Set the wide layout style and remove menus and markings from display
st.set_page_config(layout="wide")

# Initialize the session state
if "experiments" not in st.session_state:
    st.session_state["experiments"] = {}

experiments: Dict[str, Tuple[CyclicVoltammetry, float, float]] = st.session_state[
    "experiments"
]


st.title("Cyclic voltammetry viewer")

with st.form("File upload form", clear_on_submit=True):

    col1, col2, col3 = st.columns(3)

    with col1:
        # Set the name of the experiment to be loaded
        default = "experiment_{}".format(len(experiments))
        experiment_name = st.text_input("Define the experiment name", value=default)

    with col2:
        # Set the area of the electrode
        area = st.number_input(
            "Set the area of the electrode in cm²", min_value=1e-6, value=1.0
        )

    with col3:
        # Set the potential shift
        vref = st.number_input(
            "Set the potential of the reference electrode (from S.H.E.)", value=0.0
        )

    # Show the file uploader box
    loaded = st.file_uploader(
        "Select the cycling voltammetry datafiles",
        accept_multiple_files=False,
        type=[".dta"],
    )

    # Display warning if name is not available
    if experiment_name in experiments.keys():
        st.warning("The selected experiment name is already in use")

    # Show the submit button
    submitted = st.form_submit_button(
        "Submit",
        disabled=True if experiment_name in experiments.keys() else False,
    )


if loaded and submitted and experiment_name != "":

    manager = BytesStreamManager(loaded.name, BytesIO(loaded.getvalue()))

    with tmp(mode="w+", suffix=".dta") as file:

        # Write a temporary file
        file.write(StringIO(manager.bytestream.getvalue().decode("utf-8")).read())

        # Read the temporary file and load the experiment in the session state
        cv = CyclicVoltammetry(file.name)
        experiments[experiment_name] = (cv, area, vref)

if experiments != {}:

    col1, col2 = st.columns(2)

    with col1:
        apply_area = st.checkbox("Apply normalization by area", value=False)

    with col2:
        apply_shift = st.checkbox("Apply shift to the potential", value=False)

    fig = make_subplots(cols=1, rows=1)

    for name, (cv, area, vref) in experiments.items():

        for index in range(cv.settings["n_cycles"]):

            voltage, current = cv[index]["Vf"], cv[index]["Im"]

            if type(voltage) == np.float64:
                continue

            x = [V - vref for V in voltage] if apply_shift else voltage
            y = [I / area for I in current] if apply_area else current

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    name=f"{name} {index}",
                ),
                row=1,
                col=1,
            )

    fig.update_xaxes(
        showline=True,
        linecolor="black",
        gridwidth=1,
        gridcolor="#DDDDDD",
        title_font={"size": 32},
    )

    fig.update_yaxes(
        showline=True,
        linecolor="black",
        gridwidth=1,
        gridcolor="#DDDDDD",
        title_font={"size": 32},
    )

    fig.update_layout(
        xaxis_title = "V vs S.H.E." if apply_shift else "V vs Ref.",
        yaxis_title = "I (A/cm²)" if apply_area else "I (A)",
        plot_bgcolor="#FFFFFF",
        height=800,
        width=None,
        font=dict(size=28),
    )

    st.plotly_chart(fig, use_container_width=True)
