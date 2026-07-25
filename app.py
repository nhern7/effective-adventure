from flask import Flask, request, jsonify, render_template
from datetime import datetime
import openmeteo_requests
import sqlite3
import os
import pandas as pd
app = Flask(__name__)
DB_PATH = os.getenv("DATABASE_PATH","./database/locations.db")

def dbSetup():
	con = sqlite3.connect(DB_PATH)
	initialize = "CREATE TABLE Locations(id, name, latitude, longitude)"
	con.execute(initialize)
	con.close()

def addLocation(name, latitude, longitude):
	con = sqlite3.connect(DB_PATH)
	cur = con.cursor()
	res = con.execute("SELECT 1 FROM Locations WHERE name = ?", (name,))
	if res.fetchone() is not None:
		print("Location already exists")
	else:
		cur.execute("INSERT INTO Locations (name, latitude, longitude) VALUES (?, ?, ?) ",(name, latitude, longitude))
		con.commit()
	con.close()
@app.route('/')
def hello():
	con = sqlite3.connect(DB_PATH)
	cursor = con.execute("SELECT * FROM Locations")
	locs = cursor.fetchall()
	con.close()
	return render_template("index.html", locations=locs, date=datetime.now().strftime('%Y-%m-%d'))
@app.route('/cache-me')
def cache():
	return f"nginx will cache this response"

@app.route('/info')
def info():

	resp = {
		'connecting_ip': request.headers['X-Real-IP'],
		'proxy_ip': request.headers['X-Forwarded-For'],
		'host': request.headers['Host'],
		'user-agent': request.headers['User-Agent']
	}

	return jsonify(resp)

@app.route('/flask-health-check')
def flask_health_check():
	return "success"

@app.route('/reset-data')
def reset_data():
	con = sqlite3.connect(DB_PATH)
	con.execute("DELETE FROM Locations")
	con.commit()
	con.close()


	return "Data reset successfully! <br> <a href='/'><button>Back</button></a>"

@app.route('/get-temp')
def get_temp_route():
	lat = request.args.get('lat')
	long = request.args.get('long')
	return _getTemp(float(lat), float(long))

def _getTemp(lat, long):
	openmeteo = openmeteo_requests.Client()
	url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": lat,
		"longitude": long,
		"hourly": ["temperature_2m", "precipitation"],
		"temperature_unit": "fahrenheit"
	}
	response_raw = openmeteo.weather_api(url, params=params)
	response = response_raw[0]
	if response is not None:
		hourly = response.Hourly()
		hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
		
		hourly_range = pd.date_range(
			start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
			end=pd.to_datetime(hourly.Time(), unit="s", utc=True).normalize() + pd.Timedelta(days=1),
			freq=pd.Timedelta(seconds=hourly.Interval()),
			inclusive="left"
		)
		
		hourly_data = {
			"Hour (24 hour)": hourly_range.strftime('%H:00'),
			"Temperature (degrees F)": hourly_temperature_2m[:len(hourly_range)].astype(int),
			"Precipitation (inches)": hourly.Variables(1).ValuesAsNumpy()[:len(hourly_range)].astype(int)
		}
		
		hourly_dataframe = pd.DataFrame(data=hourly_data)
		return hourly_dataframe.to_html(classes='table table-striped', index=False)
	else:
		return "Error in getTemp()"