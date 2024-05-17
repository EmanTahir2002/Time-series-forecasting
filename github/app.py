from flask import Flask, render_template, request, Response
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import warnings
import os

warnings.filterwarnings("ignore")

UPLOAD_FOLDER = 'static/uploads'

''' 
"Coal Electric Power Sector CO2 Emissions"
"Natural Gas Electric Power Sector CO2 Emissions"
"Distillate Fuel, Including Kerosene-Type Jet Fuel, Oil Electric Power Sector CO2 Emissions"
"Petroleum Coke Electric Power Sector CO2 Emissions"
"Residual Fuel Oil Electric Power Sector CO2 Emissions"
"Petroleum Electric Power Sector CO2 Emissions"
"Geothermal Energy Electric Power Sector CO2 Emissions"
"Non-Biomass Waste Electric Power Sector CO2 Emissions"
"Total Energy Electric Power Sector CO2 Emissions"
'''

app = Flask(__name__)
description = ""
actData = None

def TestStationaryPlot(ts):
    rol_mean = ts["Value"].rolling(window = 12, center = False).mean()
    rol_std = ts["Value"].rolling(window = 12, center = False).std()

    plt.plot(ts["Value"], color = 'blue',label = 'Original Data')
    plt.plot(rol_mean, color = 'red', label = 'Rolling Mean')
    plt.plot(rol_std, color ='black', label = 'Rolling Std')
    plt.xticks(fontsize = 15)
    plt.yticks(fontsize = 15)
    
    plt.xlabel('Time in Years', fontsize = 25)
    plt.ylabel('Total Emissions', fontsize = 25)
    plt.legend(loc='best', fontsize = 25)
    plt.title('Rolling Mean & Standard Deviation', fontsize = 25)
    # plt.show(block= True)
    image_path = 'static/plot.png'
    if os.path.exists(image_path):
        os.remove(image_path)
        
    plt.savefig(image_path, bbox_inches='tight')

    plt.close()
    return image_path

def displayHybrid(data, actual_data, name):
    # train_size = int(len(data) * 0.8)
    length = 463
    
    # print("actual date:",actual_data["Date"])
    # print("actual value:",actual_data["Value"])
    # print("data date:",data["Date"])
    # print("pred:",data["predResults"])

    plt.figure(figsize=(10, 6))
    # print("before")
    plt.plot(actual_data["Value"][length:], label='Actual', color='blue')
    # print("after")
    plt.plot(actual_data["Value"][:length], label='Train', color='green')
    # print("later")
    plt.plot(data["predResults"], label='Hybrid Forecast', color='orange')
    # print("now")
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title(f'Model Evaluation for {name}')
    plt.legend()
    # print("saving")
    image_path = 'static/hybrid.png'
    if os.path.exists(image_path):
        os.remove(image_path)
    # print("still saving")
    plt.savefig(image_path, bbox_inches='tight')
    # print("saved")
    return image_path

@app.route("/", methods=["GET", "POST"])
def index():
    
    return render_template("index.html")

@app.route("/preprocessing", methods=["POST"])              # Fetching data from the db and displaying the statics
def preprocessing():
    im = ""
    selectedValue = request.form['selected_value']
    if selectedValue:
        conn = sqlite3.connect('energy_data.db')
        c = conn.cursor()

        c.execute("SELECT YYYYMM, Value FROM energy_data WHERE Description = ?", (selectedValue,))
        result = c.fetchall()
        result = [list(t) for t in result]

        global description 
        description = selectedValue

        df = pd.DataFrame(result, columns=['Date', 'Value'])

        global actData
        actData = df

        imagePath = TestStationaryPlot(df)
        im = []
        im.append(imagePath)
        conn.close()
    return render_template("page2.html", image_path=im)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if request.method == "POST":
        selectedValue = request.form['selected_value']
        if selectedValue:
            conn = sqlite3.connect('energy_data.db')
            c = conn.cursor()
            
            c.execute("SELECT date, predResults FROM predictions WHERE model = ?", (selectedValue,))
            result = c.fetchall()
            result = [list(t) for t in result]

            predDf = pd.DataFrame(result, columns=['Date', 'predResults'])

            c.execute("SELECT rmse, rmsePercent FROM metrics WHERE model = ?", (selectedValue,))
            result = c.fetchall()
            result = [list(t) for t in result]

            metricsDf = pd.DataFrame(result, columns=['rmse', 'rmsePercentage'])
            
            im = []     
            imp = displayHybrid(predDf, actData, description)
            im.append(imp)
            conn.close()
            print(im)
            return render_template("page3.html", rmse=metricsDf['rmse'][0], rmsep=metricsDf['rmsePercentage'][0], image_path=im)
    
    else:
        return render_template("page3.html")
    

if __name__ == "__main__":
    app.run(debug=True)
