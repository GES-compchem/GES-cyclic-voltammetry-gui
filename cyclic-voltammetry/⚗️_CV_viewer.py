import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from io import StringIO, BytesIO
from tempfile import NamedTemporaryFile as tmp
from typing import Dict, List

from core.bytestream_tools import BytesStreamManager
from core.data_structures import CVExperiment, Trace, PlotSettings
from core.utils import get_trace_color, force_update_once
from echemsuite.cyclicvoltammetry.read_input import CyclicVoltammetry


# Set the wide layout style and remove menus and markings from display
st.set_page_config(layout="wide")

# Initialize the session state
if "experiments" not in st.session_state:
    st.session_state["experiments"] = {}
    st.session_state["plot_data"] = {}
    st.session_state["plot_settings"] = {}

experiments: Dict[str, CVExperiment] = st.session_state["experiments"]
plotdata: Dict[str, List[Trace]] = st.session_state["plot_data"]
plotsettings: Dict[str, PlotSettings] = st.session_state["plot_settings"]


st.title("Cyclic voltammetry viewer")

with st.form("File upload form", clear_on_submit=True):

    col1, col2, col3 = st.columns(3)

    # Set the name of the experiment to be loaded
    with col1:
        default = "experiment_{}".format(len(experiments))
        experiment_name = st.text_input("Define the experiment name", value=default)

    # Set the area of the electrode
    with col2:
        area = st.number_input(
            "Set the area of the electrode in cm²", min_value=1e-6, value=1.0
        )

    # Set the potential shift
    with col3:
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
        experiments[experiment_name] = CVExperiment(cv, area, vref, loaded.name)


if experiments != {}:

    with st.expander("📋 Experiment information", expanded=False):

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("#### Experiment name")

        with col2:
            st.write("#### Filename")

        with col3:
            st.write("#### Number of cycles")

        for name, experiment in experiments.items():

            with col1:
                st.write(name)

            with col2:
                st.write(experiment.filename)

            with col3:
                cycles = [df for df in experiment.data if type(df["Vf"]) != np.float64]
                st.write(len(cycles))

    col1, col2 = st.columns([3, 1])

    with col1:
        name = st.text_input("Select the name of the plot", value="")

    if name in plotdata.keys():
        st.warning(f"The plot `{name}` already exists, select another name")

    with col2:
        st.write("")
        st.write("")
        apply = st.button(
            "Create",
            disabled=True if name in plotdata.keys() or name == "" else False,
        )

    if apply:
        plotdata[name] = []
        plotsettings[name] = PlotSettings()

        for _name, _experiment in experiments.items():

            cycles = [df for df in _experiment.data if type(df["Vf"]) != np.float64]

            for tid, cycle in enumerate(cycles):

                voltage = cycle["Vf"]
                current = cycle["Im"]

                newtrace = Trace(
                    f"{_name} / Cycle {tid}",
                    voltage,
                    current,
                    get_trace_color(_name, tid),
                    "solid",
                    _name,
                    tid,
                )

                plotdata[name].append(newtrace)

        st.experimental_rerun()

if plotdata != {}:

    tabs = st.tabs([name for name in plotdata.keys()])

    for index, (tab, pname) in enumerate(zip(tabs, plotdata.keys())):

        with tab:

            st.markdown(f"## {pname}")

            with st.expander("Trace selector"):

                col1, col2 = st.columns([1, 3])

                with col1:
                    mode = st.radio(
                        "Select operation mode:",
                        ["Add/remove traces", "Edit single trace"],
                        key=f"mode_{index}",
                    )

                    clearall = st.button("🧹 Remove all", key=f"remove_all_{index}")

                if clearall:
                    plotdata[pname] = []
                    st.experimental_rerun()

                with col2:

                    label_list = [trace.name for trace in plotdata[pname]]

                    if mode == "Add/remove traces":

                        experiment_name = st.selectbox(
                            "Select experiment:",
                            [name for name in experiments.keys()],
                            key=f"experiment_name_{index}",
                        )

                        experiment = experiments[experiment_name]
                        cycles = [
                            df for df in experiment.data if type(df["Vf"]) != np.float64
                        ]

                        last_selection = [
                            trace.original_number
                            for trace in plotdata[pname]
                            if trace.original_experiment == experiment_name
                        ]

                        trace_ids = st.multiselect(
                            "Select the cycles to show:",
                            [i for i, _ in enumerate(cycles)],
                            default=last_selection,
                            key=f"trace_ids_selector_{index}",
                        )

                        removed = [idx for idx in last_selection if idx not in trace_ids]
                        for r in removed:
                            for idx, trace in enumerate(plotdata[pname]):
                                if (
                                    trace.original_experiment == experiment_name
                                    and trace.original_number == r
                                ):
                                    del plotdata[pname][idx]
                                    break

                        added = [idx for idx in trace_ids if idx not in last_selection]
                        for added_trace in added:

                            voltage = cycles[added_trace]["Vf"]
                            current = cycles[added_trace]["Im"]

                            newtrace = Trace(
                                f"{experiment_name} / Cycle {added_trace}",
                                voltage,
                                current,
                                get_trace_color(experiment_name, added_trace),
                                "solid",
                                experiment_name,
                                added_trace,
                            )

                            plotdata[pname].append(newtrace)

                    elif mode == "Edit single trace":

                        if len(label_list) == 0:
                            st.info(
                                "Please add at least one trace to the plot to edit a trace"
                            )

                        else:
                            tname = st.selectbox(
                                "Select the trace to edit:",
                                label_list,
                                key=f"trace_to_edit_selestor_{index}",
                            )
                            trace_index = label_list.index(tname)

                            label = st.text_input(
                                "Select the new name of the trace:",
                                value=tname,
                                key=f"modify_trace_name_{index}",
                            )

                            if label in label_list and label != tname:
                                st.warning(
                                    f"WARNING: The label `{label}` is already in use"
                                )

                            linestyle = st.selectbox(
                                "Select the line style:",
                                [
                                    "solid",
                                    "dot",
                                    "dash",
                                    "longdash",
                                    "dashdot",
                                    "longdashdot",
                                ],
                                key=f"modify_linestyle_{index}",
                            )

                            color = st.color_picker(
                                "Select the color of the trace:",
                                value=plotdata[pname][trace_index].color,
                                key=f"modify_color_{index}",
                            )

                            apply = st.button(
                                "Apply",
                                disabled=True
                                if label == "" or (label in label_list and label != tname)
                                else False,
                                key=f"modify_apply_{index}",
                            )

                            if apply:
                                old = plotdata[pname][trace_index]
                                newtrace = Trace(
                                    label,
                                    old.voltage,
                                    old.current,
                                    color,
                                    linestyle,
                                    old.original_experiment,
                                    old.original_number,
                                )
                                plotdata[pname][trace_index] = newtrace
                                st.experimental_rerun()

            settings = plotsettings[pname]

            col1, col2 = st.columns([3, 1])

            with col2:

                st.write("### Scale values")

                settings.normalize_by_area = st.checkbox(
                    "Apply normalization by area",
                    value=settings.normalize_by_area,
                    key=f"scale_by_area_{index}",
                )

                settings.shift_with_vref = st.checkbox(
                    "Apply shift to the potential",
                    value=settings.shift_with_vref,
                    key=f"shift_vref_{index}",
                )

                st.write("### Graph options")

                settings.show_markers = st.checkbox(
                    "Add markers to data-point",
                    value=settings.show_markers,
                    key=f"marker_selector_{index}",
                )

                settings.set_user_defined_scale = st.checkbox(
                    "Set user defined plot range",
                    value=settings.set_user_defined_scale,
                    key=f"range_scale_selector_{index}",
                )

                settings.vmin = float(
                    st.number_input(
                        "Set minimum value of the voltage scale (V)",
                        value=settings.vmin,
                        max_value=settings.vmax,
                        disabled=not settings.set_user_defined_scale,
                        step=1e-9,
                        key=f"vmin_selector_{index}",
                    )
                )

                settings.vmax = float(
                    st.number_input(
                        "Set maximum value of the voltage scale (V)",
                        value=settings.vmax,
                        min_value=settings.vmin,
                        disabled=not settings.set_user_defined_scale,
                        step=1e-9,
                        key=f"vmax_selector_{index}",
                    )
                )

                settings.imin = float(
                    st.number_input(
                        "Set minimum value of the current scale (mA)",
                        value=settings.imin,
                        max_value=settings.imax,
                        disabled=not settings.set_user_defined_scale,
                        step=1e-9,
                        key=f"imin_selector_{index}",
                    )
                )

                settings.imax = float(
                    st.number_input(
                        "Set maximum value of the current scale (mA)",
                        value=settings.imax,
                        min_value=settings.imin,
                        disabled=not settings.set_user_defined_scale,
                        step=1e-9,
                        key=f"imax_selector_{index}",
                    )
                )

            with col1:

                fig = make_subplots(cols=1, rows=1)

                for trace in plotdata[pname]:

                    voltage, current = trace.voltage, trace.current

                    vref = experiments[trace.original_experiment].vref
                    area = experiments[trace.original_experiment].area

                    x = [V - vref for V in voltage] if settings.shift_with_vref else voltage
                    y = (
                        [I / area for I in current]
                        if settings.normalize_by_area
                        else current
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=x,
                            y=y,
                            name=trace.name,
                            line=dict(color=trace.color, dash=trace.linestyle),
                            mode="lines+markers" if settings.show_markers else "lines",
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
                    range=[settings.vmin, settings.vmax]
                    if settings.set_user_defined_scale
                    else None,
                    zeroline=False,
                    mirror=True,
                    automargin=True,
                )

                fig.update_yaxes(
                    showline=True,
                    linecolor="black",
                    gridwidth=1,
                    gridcolor="#DDDDDD",
                    title_font={"size": 32},
                    range=[settings.imin / 1000, settings.imax / 1000]
                    if settings.set_user_defined_scale
                    else None,
                    zeroline=False,
                    mirror=True,
                    automargin=True,
                )

                fig.update_layout(
                    xaxis_title="V vs S.H.E." if settings.shift_with_vref else "V vs Ref.",
                    yaxis_title="I (A/cm²)" if settings.normalize_by_area else "I (A)",
                    plot_bgcolor="#FFFFFF",
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bordercolor="Black",
                        borderwidth=1,
                        font=dict(size=18),
                    ),
                    height=800,
                    width=1100,
                    font=dict(size=28),
                    margin=dict(l=120, r=50, t=50, b=120),
                )

                st.plotly_chart(fig, use_container_width=True, theme=None)

            with col2:

                st.markdown("### Download")

                format = st.selectbox(
                    "Select the format of the file",
                    ["png", "jpeg", "svg", "pdf"],
                    key=f"download_format_{index}",
                )

                st.download_button(
                    "📥 Download plot",
                    data=fig.to_image(format=format),
                    file_name=f"{pname}.{format}",
                    key=f"download_button_{index}",
                )

force_update_once()
