import plotly
import numpy as np
import streamlit as st

def get_plotly_color(index: int) -> str:
    color_list = plotly.colors.qualitative.Plotly
    return color_list[index % len(color_list)]

def get_trace_color(experiment_name: str, track_id: int):
    color_id = 0
    for _name, _experiment in st.session_state["experiments"].items():

        if _name == experiment_name:
            color_id += track_id
            break

        else:
            cycles = [
                df
                for df in _experiment.data
                if type(df["Vf"]) != np.float64
            ]
            color_id += len(cycles)


def force_update_once():
    if "forced update executed" not in st.session_state:
        st.session_state["forced update executed"] = False
        st.experimental_rerun()
    if not st.session_state["forced update executed"]:
        st.session_state["forced update executed"] = True
        return
    st.session_state["forced update executed"] = False
    st.experimental_rerun()