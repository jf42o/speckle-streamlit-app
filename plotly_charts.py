import pandas as pd
import plotly.express as px
import streamlit as st

# Base Chart class
class Chart:
    def __init__(self, df):
        self.df = df

    def is_numeric(self, column):
        return pd.api.types.is_numeric_dtype(self.df[column])

    def get_grouped_data(self, x_axis, y_axis, group_by):
        return self.df.groupby([group_by, x_axis])[y_axis].sum().reset_index()

    def validate(self, x_axis, y_axis):
        pass

    def render(self, x_axis, y_axis, group_by):
        pass

    def apply_speckle_style(self, fig):
        fig.update_traces(marker=dict(color='#1a6498'))
        fig.update_layout(
            font=dict(family="Public Sans", size=14, color="black"),
            plot_bgcolor='#fff',
            paper_bgcolor='#fff',
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

# ScatterChart class
class ScatterChart(Chart):
    def validate(self, x_axis, y_axis):
        if not self.is_numeric(x_axis) or not self.is_numeric(y_axis):
            raise ValueError("Please choose numeric parameters for the X and Y axes.")

    def render(self, x_axis, y_axis, group_by):
        self.validate(x_axis, y_axis)
        grouped_data = self.get_grouped_data(x_axis, y_axis, group_by)
        fig = px.scatter(grouped_data, x=x_axis, y=y_axis, color=group_by)
        return self.apply_speckle_style(fig)

# BarChart class
class BarChart(Chart):
    def validate(self, x_axis, y_axis):
        if not self.is_numeric(y_axis):
            raise ValueError("Please choose a numeric parameter for the Y axis.")

    def render(self, x_axis, y_axis, group_by=None):
        self.validate(x_axis, y_axis)
        if group_by is not None:
            grouped_data = self.get_grouped_data(x_axis, y_axis, group_by)
            fig = px.bar(grouped_data, x=x_axis, y=y_axis, color=group_by)
            return self.apply_speckle_style(fig)
        else:
            fig = px.bar(self.df, x=x_axis, y=y_axis, color=group_by)
            return self.apply_speckle_style(fig)

# LineChart class
class LineChart(Chart):
    def validate(self, x_axis, y_axis):
        if not self.is_numeric(y_axis):
            raise ValueError("Please choose a numeric parameter for the Y axis.")

    def render(self, x_axis, y_axis, group_by):
        self.validate(x_axis, y_axis)
        grouped_data = self.get_grouped_data(x_axis, y_axis, group_by)
        fig = px.line(grouped_data, x=x_axis, y=y_axis, color=group_by)
        return self.apply_speckle_style(fig)

# BoxPlot class
class BoxPlot(Chart):
    def validate(self, x_axis, y_axis):
        if not self.is_numeric(y_axis):
            raise ValueError("Please choose a numeric parameter for the Y axis.")

    def render(self, x_axis, y_axis, group_by):
        self.validate(x_axis, y_axis)
        grouped_data = self.get_grouped_data(x_axis, y_axis, group_by)
        fig = px.box(grouped_data, x=x_axis, y=y_axis, color=group_by)
        return self.apply_speckle_style(fig)

# PieChart class
class PieChart(Chart):
    def validate(self, x_axis):
        if not self.is_numeric(x_axis):
            raise ValueError("Please choose a numeric parameter for the X axis.")
        
    def render(self, x_axis=None, y_axis=None, group_by=None):
        self.validate(x_axis)
        grouped_data = self.df.groupby(group_by)[x_axis].sum().reset_index()
        fig = px.pie(grouped_data, names=group_by, values=x_axis)
        return self.apply_speckle_style(fig)
    
def display_charts(df):
    chart_type = st.selectbox(
    "Choose the chart type:",
    ("Scatter Chart", "Bar Chart", "Pie Chart", "Line Chart", "Box Plot"),
    )
    x_axis = st.selectbox("Choose the X-axis parameter:", df.columns)
    y_axis = st.selectbox("Choose the Y-axis parameter:", df.columns)
    group_by = st.selectbox("Choose the Group By parameter:", df.columns)

    chart_classes = {
        "Scatter Chart": ScatterChart,
        "Bar Chart": BarChart,
        "Pie Chart": PieChart,
        "Line Chart": LineChart,
        "Box Plot": BoxPlot,
    }

    try:
        chart = chart_classes[chart_type](df)
        fig = chart.render(x_axis, y_axis, group_by)
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"An error occurred while creating the chart: {e}")

def get_numeric_columns(df):
                numeric_columns = [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]
                return numeric_columns

def get_non_numeric_columns(df):
    non_numeric_columns = [column for column in df.columns if not pd.api.types.is_numeric_dtype(df[column])]
    return non_numeric_columns

def get_columns_except(df, input_to_filter1, input_to_filter2):
    columns_except_input = [column for column in df.columns if (column != input_to_filter1 and column != input_to_filter2)]
    return columns_except_input

chart_types = ["Bar Chart", "Scatter Chart", "Pie Chart", "Line Chart", "Box Plot"]
chart_classes = {
    "Bar Chart": BarChart,
    "Scatter Chart": ScatterChart,
    "Pie Chart": PieChart,
    "Line Chart": LineChart,
    "Box Plot": BoxPlot,
}