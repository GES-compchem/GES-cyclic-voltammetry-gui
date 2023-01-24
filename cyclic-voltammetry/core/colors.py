import plotly

def get_plotly_color(index: int) -> str:
    color_list = plotly.colors.qualitative.Plotly
    return color_list[index % len(color_list)]