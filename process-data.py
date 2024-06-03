import pandas as pd


raw_data = pd.read_csv('./data-raw/uscities.csv')
filtered_data = raw_data.loc[raw_data['population'] >= 10000].copy()
filtered_data.loc[:, 'city_state'] = filtered_data['city'] + ', ' + filtered_data['state_name']
processed_data = filtered_data[['city_state', 'lat', 'lng']]

processed_data_path = './data/cities.csv'
processed_data.to_csv(processed_data_path, index=False)