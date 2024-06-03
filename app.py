import matplotlib.pyplot as plt
import numpy as np
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime
from ipyleaflet import Map, Marker 
from shiny import App, Inputs, Outputs, Session, render, ui, reactive
from shinywidgets import output_widget, render_widget


cities_df = pd.read_csv("./data/cities.csv")
def plotter(chosencity, startdate, enddate, temp, temp_threshold, option, begin, end):
        selected_city = cities_df[cities_df["city_state"] == chosencity]
        lat, lon = selected_city.iloc[0]["lat"], selected_city.iloc[0]["lng"]

        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,      
            "longitude": lon,          
            "start_date": startdate,
            "end_date": enddate,   
            "daily": "temperature_2m_min",  
            "temperature_unit": temp 
        }
        responses = openmeteo.weather_api(url, params=params)


        selected_response = responses[0]
        reallat = round(selected_response.Latitude(),4)
        reallong = round(selected_response.Longitude(),4)

        daily = selected_response.Daily()
        daily_temperature_2m_min = daily.Variables(0).ValuesAsNumpy()

        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}
        daily_data["temperature_2m_min"] = daily_temperature_2m_min

        thresholds = range(begin, end+1) 

        days_below = [(daily_data['temperature_2m_min'] < t).sum() for t in thresholds]

        total_days = len(daily_data['temperature_2m_min'])
        proportion_below = [days / total_days for days in days_below]

        table_df = pd.DataFrame({
            "Temp": thresholds,
            "Days Below": days_below,
            "Proportion Below": proportion_below
        })
        table_df = table_df.sort_values(by="Temp", ascending=False).reset_index(drop=True)

        fig, ax = plt.subplots(figsize=(10, 5))

        below_threshold = daily_data["temperature_2m_min"] < temp_threshold
        above_threshold = daily_data["temperature_2m_min"] >= temp_threshold

        ax.scatter(daily_data["date"][below_threshold], daily_data["temperature_2m_min"][below_threshold], alpha=0.5, color='lightgrey', label='Below Threshold')

        ax.scatter(daily_data["date"][above_threshold], daily_data["temperature_2m_min"][above_threshold], color='black', label='Above Threshold')

        ax.axhline(y=temp_threshold, color='black', linestyle='-', label=f'Threshold at {temp_threshold}°F')

        daily_data_df = pd.DataFrame(daily_data)
        if "a" in option:
            rolling_avg = daily_data_df["temperature_2m_min"].rolling(window=7, center=True).mean()
            ax.plot(daily_data_df["date"], rolling_avg, color='red', label='Weekly Rolling Avg')
        if "b" in option:
            monthly_rolling_avg = daily_data_df['temperature_2m_min'].rolling(window=30, min_periods=1, center=True).mean()
            ax.plot(daily_data_df['date'], monthly_rolling_avg, color='blue', label='Monthly Rolling Avg')

        ax.set_xlabel("Date")
        ax.set_ylabel("Daily Minimum Temperature (°F)")
        ax.set_title(f"Daily Minimum Temperature for {selected_city['city_state'].values[0]}")
        ax.grid(True)
        return fig, table_df, reallat, reallong
            

app_ui = ui.page_fillable(
    ui.panel_title("Daily Heat Pump Efficiency Counter"),  
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_selectize(  
                "selectize",  
                "City",  
                {row['city_state']: row['city_state'] for index, row in cities_df.iterrows()}, 
                selected = "Urbana, Illinois" 
            ),  
            ui.output_text("value"),
            ui.input_date_range("daterange", "Dates", start="2022-01-01", end = "2024-01-01", min="2020-01-01", max="2024-01-01"), 
            ui.input_radio_buttons(  
                "radio",  
                "Units",  
                {"fahrenheit": "Fahrenheit", "celsius": "Celsius"}, 
                selected = "fahrenheit"
            ), 
            ui.output_ui("plot_temp"),
            ui.input_checkbox_group(  
                "checkbox_group",  
                "Plot options",  
                {  
                    "a": "Weekly Rolling Average",  
                    "b": "Monthly rolling average",   
                },  
                selected = ""
            ), 
            ui.output_ui("ui_slider"),
            output_widget("map"),
            width = 300
        ), 
        ui.navset_pill(
            ui.nav_panel("Historical", ui.output_plot("my_plot"), ui.output_table("my_table")),
            ui.nav_panel("About", ui.markdown("""
                # About

                This interactive software offers a comprehensive look at past weather trends in different cities. Users can explore minimum daily temperatures across selected date periods, compare these against temperature thresholds, and observe trends through rolling averages. All this is made possible by utilizing data from the Open-Meteo API.
                This software provides an engaging and educational platform for investigation, suited for anyone interested in climate trends or local weather patterns.

                ## Features
                - **Temperature Units**: Choose between Fahrenheit and Celsius for temperature readings.
                - **City Selection**: Select from a list of cities to view weather data.
                - **Date Range**: Specify the period for which you wish to view weather data by clicking on the dates to change them.
                - **Temperature Thresholds**: Compare daily temperatures against specified thresholds in the table by using the "Table Temperatures" slider.
                - **Rolling Averages**: View weekly and monthly rolling averages to identify trends by selecting the checkbox.

                ### Citations
                    Open-Meteo. (n.d.). Historical Weather API. https://open-meteo.com/en/docs/historical-weather-api 
                    United States Cities Database. SimpleMaps. (n.d.). https://simplemaps.com/data/us-cities 
                            """)
                        ),
            id="tab"
        ), 
    ), 
)  

def server(input, output, session):

    @output
    @render.plot
    def my_plot():
        selected_city = input.selectize()
        startdate = input.daterange()[0]
        enddate = input.daterange()[1]
        temp = input.radio()
        thresh = input.slider()
        option = input.checkbox_group()
        begin = input.slider2()[0]
        end = input.slider2()[1]
        fig, table_df, reallat, reallong = plotter(selected_city, startdate, enddate, temp, thresh, option, begin, end)
        return fig

    @output
    @render.table
    def my_table():
        selected_city = input.selectize()
        startdate = input.daterange()[0]
        enddate = input.daterange()[1]
        temp = input.radio()
        thresh = input.slider()
        option = input.checkbox_group()
        begin = input.slider2()[0]
        end = input.slider2()[1]
        fig, table_df, reallat, reallong = plotter(selected_city, startdate, enddate, temp, thresh, option, begin, end)
        return table_df
    
    @render.text
    def value():
        selected_city = input.selectize()
        startdate = input.daterange()[0]
        enddate = input.daterange()[1]
        temp = input.radio()
        thresh = input.slider()
        option = input.checkbox_group()
        begin = input.slider2()[0]
        end = input.slider2()[1]
        fig, table_df, reallat, reallong = plotter(selected_city, startdate, enddate, temp, thresh, option, begin, end)
        return f"{reallat}°N, {reallong}°E"
    
    @render.ui
    @reactive.event(input.radio)
    def ui_slider():
        if input.radio() == "fahrenheit":
            return ui.input_slider("slider2", "Table Temperatures", min=-25, max=60, value=[0,15])
        else:
            return ui.input_slider("slider2", "Table Temperatures", min=-30, max=15, value=[-20,10])
    @render.ui
    @reactive.event(input.radio)
    def plot_temp():
        if input.radio() == "fahrenheit":
            return ui.input_slider("slider", "Plot Temperature", -15, 50, 5)
        else:
            return ui.input_slider("slider", "Plot Temperature", -25, 10, -15)
    @render_widget 
    @reactive.event(input.selectize) 
    def map():
        selected_city = cities_df[cities_df["city_state"] == input.selectize()]
        lat, lon = selected_city.iloc[0]["lat"], selected_city.iloc[0]["lng"]
        map = Map(center=(lat, lon), zoom=10)
        point = Marker(location=(lat, lon), draggable=True)  
        map.add_layer(point) 
        return map
    
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
