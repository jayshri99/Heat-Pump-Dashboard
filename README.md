# Heat Pump Dashboard

The goal of this project is to create an interactive dashboard that helps determine the efficacy of installing a heat pump depending on the weather in a particular location in the United States.

In short, heat pumps are a reverse air conditioner that can be used to replace a traditional gas-powered furnace through the magic of refrigerant. However, compared to gas-powered furnaces, their efficacy is potentially more dependent on temperature. In particular, heat pumps may struggle at extremely low temperatures. As a result, many potential users are discouraged from electing to install a heat pump over a traditional furnace.

Heat pump manufacturers publish performance specifications, importantly including the coefficient of performance. This information, together with local weather information, can help consumers make informed decisions.

## Application Features

1. User Input
  - City and state (autocompleted).
  - Date range (default: 2022-01-01 to 2024-01-01).
  - Temperature units (Fahrenheit/Celsius).
  - Temperature slider for plotting.
  - Weekly and monthly rolling averages.
  - Temperature range slider for table data.

2. Reactive Elements
  - Historical data plot and table.
  - Interactive map with location pin.
  - Coordinates display for the weather station.

### Setup Instructions
1. **Environment Preparation**: Ensure that Python is installed on your system. 
2. **Clone the Repository**: Clone the project repository from GitHub or another version control system.
   ```bash
   git clone <repository-url>
   ```
3. **Install Dependencies**: Navigate to the cloned directory and run the following command to install the necessary Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Application**: Start the web server. 
   ```bash
   python app.py
   ```
