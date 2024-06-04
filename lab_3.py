import pandas as pd
from spyre import server

import datetime
import os
import urllib
import matplotlib.pyplot as plt
import pandas as pd
import glob
import seaborn as sns





def download_data(province_id, year1=1981, year2=2024):
    # Checking the existence of the data folder
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    else:
        # Checking the existence of an already downloaded file
        existing_files = [f for f in os.listdir(data_folder) if f.startswith(f'vhi_id__{province_id}__')]
        if existing_files:
            print(f"File '{existing_files[0]}' already exists in the 'data' folder. Nothing to download.")
            return

    # Loading data
    url = f"https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={province_id}&year1={year1}&year2={year2}&type=Mean"
    vhi_url = urllib.request.urlopen(url)

    # Writing to a file
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f'vhi_id__{province_id}__{current_datetime}.csv'
    file_path = os.path.join(data_folder, filename)

    with open(file_path, 'wb') as out:
        out.write(vhi_url.read())

    print(f"VHI is downloaded and saved in '{file_path}'")
    
for i in range(1,28):
  download_data(i)

def create_data_frame(folder_path):

    csv_files = glob.glob(folder_path + "/*.csv")

    headers = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI', 'empty']
    frames = []

    for file in csv_files:
        region_id = int(file.split('__')[1])
        df = pd.read_csv(file, header = 1, names = headers)
        df.at[0, 'Year'] =  df.at[0, 'Year'][9:]
        df=df.drop(df.index[-1])
        df = df.drop(df.loc[df['VHI'] == -1].index)
        df = df.drop('empty', axis=1)
        df.insert(0, 'region_id', region_id, True)
        df['Week'] = df['Week'].astype(int)
        frames.append(df)   
    result = pd.concat(frames).drop_duplicates().reset_index(drop=True)
    result = result.loc[(result.region_id != 12) & (result.region_id != 20)]
    result = result.replace({'region_id':{1:22, 2:24, 3:23, 4:25, 5:3, 6:4, 7:8, 8:19, 9:20, 10:21,
                                          11:9, 13:10, 14:11, 15:12, 16:13, 17:14, 18:15, 19:16, 21:17, 
                                          22:18, 23:6, 24:1, 25:2, 26:6, 27:5}})
    return result

df = create_data_frame('./data')

reg_id_name = {
    1: 'Вінницька',  2: 'Волинська',  3: 'Дніпропетровська',  4: 'Донецька',  5: 'Житомирська',
    6: 'Закарпатська',  7: 'Запорізька',  8: 'Івано-Франківська',  9: 'Київська',  10: 'Кіровоградська',
    11: 'Луганська',  12: 'Львівська',  13: 'Миколаївська',  14: 'Одеська',  15: 'Полтавська',
    16: 'Рівенська',  17: 'Сумська',  18: 'Тернопільська',  19: 'Харківська',  20: 'Херсонська',
    21: 'Хмельницька',  22: 'Черкаська',  23: 'Чернівецька',  24: 'Чернігівська',  25: 'Республіка Крим'
}

class SimpleApp(server.App):
    title = "Lab 3 app"

    inputs = [
        {
            "type": "dropdown",
            "label": "Parameter",
            "options": [{"label": "VCI", "value": "VCI"},
                        {"label": "TCI", "value": "TCI"},
                        {"label": "VHI", "value": "VHI"}],
            "key": "parameter",
            "action_id": "update_data"
        },
        {
            "type": "dropdown",
            "label": "Region",
            "options": [{"label": reg_id_name[region_id], "value": region_id} for region_id in sorted(df['region_id'].unique())],
            "key": "region",
            "action_id": "update_data"
        },
        {
            "type": "text",
            "key": "years_interval",
            "label": "Years Interval",
            "value": "1982-2024"
        },
        {
            "type": "text",
            "key": "weeks_interval",
            "label": "Weeks Interval (e.g., 1-3)",
            "value": "1-3"
        }
    ]

    controls = [{"type": "button", "label": "Update", "id": "update_data"}]

    tabs = ["Table", "Plot"]

    outputs = [{"type": "table", "id": "table", "control_id": "update_data", "tab": "Table", "on_page_load": True},
               {"type": "plot", "id": "plot", "control_id": "update_data", "tab": "Plot", "on_page_load": True},]

    def getData(self, params):
        parameter = params["parameter"]
        region_id = int(params["region"])
        years = params["years_interval"].split('-')
        week_interval = params['weeks_interval'].split('-')


        df2 = df[(df["Year"].between(years[0],years[1])) & 
        (df['Week'].between(int(week_interval[0]), int(week_interval[1]))) &
                 (df['region_id'] == region_id)][["Year","Week", parameter]]
        

        return df2
    
    def getPlot(self, params):
        parameter = params['parameter']
        region = int(params['region'])
        week_interval = params['weeks_interval'].split('-')
        date_range = params['years_interval'].split('-')

        processed_data = self.getData(params)


        pivot_data = processed_data.pivot(index='Year', columns='Week', values=parameter)
        plt.figure(figsize=(25, 20))
        sns.heatmap(pivot_data, cmap="inferno", annot=True)
        plt.title(f'Heatmap {parameter} for region: {reg_id_name[region]}')
        plt.xlabel('Week')
        plt.ylabel('Year')

        plot = plt.gcf()
        return plot
   
    
app = SimpleApp()
app.launch()