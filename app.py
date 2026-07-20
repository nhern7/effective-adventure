from flask import Flask, request, jsonify
import openmeteo_requests
import sqlite3
import os
app = Flask(__name__)
db_path = os.getenv(
	"DATABASE_PATH")  # not giving a default bc its expected we'll always be running this in docker and not locally


def dbSetup():
	con = sqlite3.connect(db_path)
	cur = con.cursor()

	initialize = "CREATE TABLE IF NOT EXISTS Locations (" \
		"id INTEGER PRIMARY KEY," \
		"name TEXT" \
		"latitude REAL" \
		"longitude REAL" \
		")"
	con.execute(initialize)

dbSetup()

def addLocation(name, latitude, longitude):
	con = sqlite3.connect(db_path)
	cur = con.cursor()
	res = con.execute("SELECT 1 FROM Locations WHERE name = ?", (name,))
	if res is not None:
		print("Location already exists")
	else:
		cur.execute("INSERT INTO Locations (name, latitude, longitude) "
				"VALUES (?, ?, ?) ",
				(name, latitude, longitude)
					)
		con.commit()


def displayResults(res):
	# res looks like....
	return jsonify([dict(row) for row in res])

@app.route('/')
def hello():
	openmeteo = openmeteo_requests.Client()
	url = "https://api.open-meteo.com/v1/forecast"

	con = sqlite3.connect(db_path)
	cur = con.cursor()
	res = con.execute("SELECT * FROM Locations")
	if res is not None:
		return displayResults(res)
	else:
		print("Error getting locations")
		#TODO skip to search bar

	params = {
		"latitude": 52.52,
		"longitude": 13.41,
		"hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
		"current": ["temperature_2m", "relative_humidity_2m"],
	}
	response_raw = openmeteo.weather_api(url, params=params)
	response = response_raw[0]

	current = response.Current()
	current_temperature_2m = current.Variables(0).Value()

	return f"Current time: {current.Time()}\nCurrent temperature: {current_temperature_2m}"

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
