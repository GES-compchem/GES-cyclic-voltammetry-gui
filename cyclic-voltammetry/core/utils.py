import plotly
import streamlit as st

def get_plotly_color(index: int) -> str:
    color_list = plotly.colors.qualitative.Plotly
    return color_list[index % len(color_list)]

def force_update_once():
    if "forced update executed" not in st.session_state:
        st.session_state["forced update executed"] = False
        st.experimental_rerun()
    if not st.session_state["forced update executed"]:
        st.session_state["forced update executed"] = True
        return
    st.session_state["forced update executed"] = False
    st.experimental_rerun()