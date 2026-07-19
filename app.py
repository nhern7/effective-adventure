from flask import Flask, request, jsonify
import openmeteo_requests

app = Flask(__name__)

@app.route('/')
def hello():
	openmeteo = openmeteo_requests.Client()
	url = "https://api.open-meteo.com/v1/forecast"

	params = {
		"latitude": 52.52,
		"longitude": 13.41,
		"hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
		"current": ["temperature_2m", "relative_humidity_2m"],
	}
	responses = openmeteo.weather_api(url, params=params)

	response = responses[0]
	# print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
	# print(f"Elevation: {response.Elevation()} m asl")
	# print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

	current = response.Current()
	current_temperature_2m = current.Variables(0).Value()
	current_relative_humidity_2m = current.Variables(1).Value()

	# print(f"Current time: {current.Time()}")
	# print(f"Current temperature_2m: {current_temperature_2m}")
	# print(f"Current relative_humidity_2m: {current_relative_humidity_2m}")

	return f"Hello World!\nCurrent time: {current.Time()}\nCurrent temperature: {current_temperature_2m}"

@app.route('/cache-me')
def cache():
	return "nginx will cache this response"

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
