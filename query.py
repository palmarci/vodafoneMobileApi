import requests
import json
import logging
import urllib.parse
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import humanfriendly
import shutil
import copy

# config
CLIENT_USERNAME = ''
CLIENT_PASSWORD = ''
HTML_FILE = "index.html"
GRAPH_FILE = "graph.png"
LOG_FILE = "data2.json"
FILTER_DAYS = 40
RENEW_DELAY_HOURS = 48
RENEW_DATE_FORMAT = "%Y-%m-%d"

# extracted from the apk - dont touch
jwtUrl = "https://auth.vodafone.hu/oxauth/restv1/token"
jwtBearerToken = 'MjI5YjMxZDAtNzVkZi00MWUwLTllZjQtNDc0MGY2MWM2MDBkOld5UUo5UU9TMXlJclR5Q242bnRTeW5CYw=='
jwtClientId = '229b31d0-75df-41e0-9ef4-4740f61c600d'
jwtClientSecret = 'WyQJ9QOS1yIrTyCn6ntSynBc'
bearerUrl = 'https://public.api.vodafone.hu/oauth2/token'
bearerClientId = '8mBeBG93vTOWHwcYk9TIWmEXey2QPczD' 

# set up logging
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

def format_size(megabytes_value, threshold_mb=1000):
	if megabytes_value >= threshold_mb:
		gigabytes_value = megabytes_value / 1000
		return f"{gigabytes_value:.2f} GB"
	else:
		return f"{megabytes_value} MB"

def get_current_date():
	return datetime.now()

def parse_date(date_str, format):
	date_object = datetime.strptime(date_str, format)
	return date_object

def call_mva_api(token, path):
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': f'Bearer {token}'
	}
	data = json.loads(requests.get(f'https://public.api.vodafone.hu/mva-api{path}', headers=headers).text)
	print(f'### {path} :')
	print(json.dumps(data, indent=4, ensure_ascii=False))

	if "code" in data and data["code"] == 503:
		print("service is down, exitting...")
		sys.exit(-1)

	print(f'###\n\n')
	if data.get("fault") is not None:
		print(f"found fault, exiting")
		sys.exit(-1)
	return data

def get_api_key():
	def get_jwt():
		payload = f'client_id={jwtClientId}&client_secret={jwtClientSecret}&scope=other openid&grant_type=password&keep_signed_in=true&password={CLIENT_PASSWORD}&username={CLIENT_USERNAME}'
		headers = {
			'Authorization': f'Basic {jwtBearerToken}',
			'Content-Type': 'application/x-www-form-urlencoded',
		}
		json_data = json.loads(requests.post(jwtUrl, headers=headers, data=payload).text)
		return json_data["access_token"]

	def get_bearer(jwtToken):
		grant_type = urllib.parse.quote_plus('urn:ietf:params:oauth:grant-type:jwt-bearer')
		payload = f'client_id={bearerClientId}&assertion={jwtToken}&grant_type={grant_type}'
		headers = {
			'Content-Type': 'application/x-www-form-urlencoded',
		}
		json_data = json.loads(requests.post(bearerUrl, headers=headers, data=payload).text)
		return json_data["access_token"]

	jwt = get_jwt()
	print(f'got jwt: {jwt}')
	bearer_token = get_bearer(jwt)
	print(f'got bearer: {bearer_token}')
	return bearer_token

def get_gradient_color(num1, num2):
	smaller_num = min(num1, num2)
	percentage = (smaller_num / max(num1, num2)) * 100
	red = int(255 - (percentage * 2.55))
	green = int(percentage * 2.55)
	blue = 0
	color_code = '#{:02x}{:02x}{:02x}'.format(red, green, blue)
	return color_code

def read_log(log_file):
	# Read old logs
	try:
		with open(log_file, "r") as file:
			data = json.load(file)
	except (IOError, json.JSONDecodeError):
		print(f"Error reading old data from file {log_file}")
		backup_path = f"{log_file}_bak_{str(int(get_current_date().timestamp))}"
		shutil.copyfile(log_file, backup_path)
		print(f"created safety backup at {backup_path}")
		data = []

	cutoff_date = (get_current_date() - timedelta(days=FILTER_DAYS))
	filtered_data = []
	for log_entry in data:
		parsed_date = datetime.fromtimestamp(log_entry["timestamp"])
		if parsed_date > cutoff_date:
			log_entry["timestamp"] = parsed_date
			filtered_data.append(log_entry)
	return filtered_data

def write_log(log_file, data):
	data_bak = copy.deepcopy(data)
	try:
		with open(log_file, "w") as file:
			for d in data_bak:
				d["timestamp"] = int(d["timestamp"].timestamp())
			print(f"writing data with {len(data_bak)} entries")
			json.dump(data_bak, file, indent=4)
		print("Data saved successfully!")
		return
	except IOError as e:
		print(f"Error saving data: {e}")
		sys.exit(-1)

def create_graph(file, data):
	timestamps = [d["timestamp"] for d in data]
	plan_max = max(d["plan"] for d in data)
	available = [d["available"] for d in data]
	plt.figure(figsize=(10, 6))
	plt.plot(timestamps, available, linewidth=5.0, color="black")
	plt.xlabel("Time")
	plt.ylabel("Available data (GB)")
	plt.grid(True)
	plt.xticks(rotation=45)
	plt.ylim(0, plan_max)
	plt.tight_layout()
	plt.savefig(file)

def write_html(text):
	f = open(HTML_FILE, "w", encoding="utf-8")
	f.write(text)
	f.close()

def main():
	os.chdir(os.path.dirname(__file__))
	api_key = get_api_key()
	data = call_mva_api(api_key, '/productAPI/v2/myPlan')

	plan = data["allowanceInfo"]["allowances"][0]["usageDescription"]
	plan = humanfriendly.parse_size(plan.replace("/", "")) // 1000 // 1000 # convert to MB

	percentage = data["allowanceInfo"]["allowances"][0]["usageProportion"]
	available = round(plan * percentage) 
	
	renew = data["tariffInfo"]["tariffBillClosure"]
	renew = parse_date(renew, RENEW_DATE_FORMAT)
	renew += timedelta(hours=RENEW_DELAY_HOURS) # fuck vodafone tbh

	color = get_gradient_color(available, plan)
	log_data = read_log(LOG_FILE)
	log_data.append({
		"timestamp": get_current_date(),
		"available": available,
		"plan": plan
	})
	write_log(LOG_FILE, log_data)
	create_graph(GRAPH_FILE, log_data)

	html_content = f'''
		<script src="script.js"></script>
		<meta charset="UTF-8">
		<center>
		<br><br>
		<h1>Available: <span style="color: {color}">{format_size(available)}</span> / {format_size(plan)}</h1>
		<br><br>
		<h3>Updated: <span id="updated">{int(get_current_date().timestamp())}</span></h3>
		<h3>Renew: <span id="renew">{int(renew.timestamp())}</span></h3>
		<br><br>
		<img src="{GRAPH_FILE}">
		</center>
		'''
	write_html(html_content)

if __name__ == "__main__":
	main()
