import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from io import StringIO, BytesIO
from tempfile import NamedTemporaryFile as tmp
from typing import Dict

from core.bytestream_tools import BytesStreamManager
from echemsuite.cyclicvoltammetry.read_input import CyclicVoltammetry

# Set the wide layout style and remove menus and markings from display
st.set_page_config(layout="wide")

# Initialize the session state
if "experiments" not in st.session_state:
    st.session_state["experiments"] = {}

experiments: Dict[str, CyclicVoltammetry] = st.session_state["experiments"]


st.title("Cyclic voltammetry viewer")

with st.form("File upload form", clear_on_submit=True):

    # Set the name of the experiment to be loaded
    default = "experiment_{}".format(len(experiments))
    experiment_name = st.text_input("Define the experiment name", value=default)

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
        experiments[experiment_name] = cv

if experiments != {}:

    fig = make_subplots(cols=1, rows=1, )

    for name, cv in experiments.items():

        for index in range(cv.settings["n_cycles"]):

            x, y = cv[index]["Vf"], cv[index]["Im"]

            if type(x) == np.float64:
                continue

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
        title_text="Vf (V)",
        showline=True,
        linecolor="black",
        gridwidth=1,
        gridcolor="#DDDDDD",
        title_font={"size": 32},
    )

    fig.update_yaxes(
        title_text="Im (A)",
        showline=True,
        linecolor="black",
        gridwidth=1,
        gridcolor="#DDDDDD",
        title_font={"size": 32},
    )

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        height=800,
        width=None,
        font=dict(size=28),
    )

    st.plotly_chart(fig, use_container_width=True)
