import requests
import json
import logging
import urllib.parse
import datetime
import humanfriendly
import os
import sys
import matplotlib.pyplot as plt

# config
client_password = ''
client_username = ''
output_html = "index.html"
output_graph = "graph.png"

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

def call_mva_api(token, path):
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': f'Bearer {token}'
	}
	data = json.loads(requests.get(f'https://public.api.vodafone.hu/mva-api{path}', headers=headers).text)
	print(f'### {path} :')
	print(json.dumps(data, indent=4, ensure_ascii=False))
	print(f'###\n\n')
	if data.get("fault") != None:
		print(f"found fault, exitting")
		sys.exit(-1)
	return data

def write_html(text):
	#print(text)
	f = open(output_html, "w", encoding="utf-8")
	f.write(text)
	f.close()

def get_api_key():
			
	def get_jwt():
		payload = f'client_id={jwtClientId}&client_secret={jwtClientSecret}&scope=other openid&grant_type=password&keep_signed_in=true&password={client_password}&username={client_username}'

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

def get_color(num1, num2):
    # Find the smaller number
    smaller_num = min(num1, num2)

    # Calculate the percentage
    percentage = (smaller_num / max(num1, num2)) * 100

    # Calculate the color components
    red = int(255 - (percentage * 2.55))
    green = int(percentage * 2.55)
    blue = 0

    # Generate HTML color code based on the color components
    color_code = '#{:02x}{:02x}{:02x}'.format(red, green, blue)

    return color_code

def remaining_time(target_date_str):
    # Convert the target date string to a datetime object
    target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')

    # Get the current date and time
    current_date = datetime.datetime.now()

    # Calculate the time difference
    time_difference = target_date - current_date

    # Calculate days, hours, minutes, and seconds
    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the result as a string
    remaining_time_str = f"{days} days, {hours:02}:{minutes:02}:{seconds:02}"

    return remaining_time_str

def log(availalbe, plan):
	today = datetime.datetime.today()
	current_month = today.strftime("%Y-%m")
	filename = f"{current_month}.json"

	# Define the data structure for each entry
	new_entry = {
		"timestamp": datetime.datetime.now().isoformat(),
		"available": availalbe // (1000*1000),
		"plan": plan // (1000*1000)
	}
		# Try to open and read the existing data (or handle if it doesn't exist)
	try:
		with open(filename, "r") as file:
			data = json.load(file)
	except (IOError, json.JSONDecodeError):
		data = []  # Initialize an empty list if file doesn't exist

	# Add the new entry to the existing data
	data.append(new_entry)

	# Save the updated data to the file
	try:
		with open(filename, "w") as file:
			json.dump(data, file, indent=4)
		print("Data saved successfully!")
	except IOError as e:
		print(f"Error saving data: {e}")
	return data

def create_graph(data):
	timestamps = [datetime.datetime.strptime(d["timestamp"], "%Y-%m-%dT%H:%M:%S.%f") for d in data]
	current_month = datetime.datetime.today().month

	# Get the maximum plan value
	max_plan = max(d["plan"] for d in data)

	# Extract available values
	available = [d["available"] for d in data]

	# Filter data for current month
	filtered_timestamps = [t for t in timestamps if t.month == current_month]
	filtered_available = [a for a, t in zip(available, timestamps) if t.month == current_month]
	
	# convert to GB
	for i, val in enumerate(filtered_available):
		filtered_available[i] = val / 1000 
	max_plan = max_plan / 1000

	# Create the plot
	plt.figure(figsize=(10, 6))
	plt.plot(filtered_timestamps, filtered_available)
	plt.xlabel("Time")
	plt.ylabel("Available data (GB)")
	plt.grid(True)

	# Rotate x-axis labels for better readability
	plt.xticks(rotation=45)

	# Set y-axis limit to max plan value
	plt.ylim(0, max_plan)

	# Show the plot
	plt.tight_layout()
	plt.savefig(output_graph)

def main():
	# make sure we are outputting in the correct folder
	os.chdir(os.path.dirname(__file__))
	
	api_key = get_api_key()
	data = call_mva_api(api_key, '/productAPI/v2/myPlan')
	available_raw = data["allowanceInfo"]["allowances"][0]["usageValue"]
	plan_raw = data["allowanceInfo"]["allowances"][0]["usageDescription"]
	available = humanfriendly.parse_size(available_raw.replace(",", "."))
	plan = humanfriendly.parse_size(plan_raw.replace("/", "").replace(",", "."))
	color = get_color(available, plan)
	renew_at = data["tariffInfo"]["tariffBillClosure"]

	monthly_data = log(available, plan)
	create_graph(monthly_data)

	available_str = humanfriendly.format_size(available)
	now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	renew_str = remaining_time(renew_at)
	plan_str = humanfriendly.format_size(plan)

	html_content = f'''
			<meta charset="UTF-8">
			<center>
			<br><br>
			<h1>Available: <span style="color: {color}">{available_str}</span> / {plan_str}</h1>
			<br><br>
			<h3>Updated: {now_str}
			<br>Renew in: {renew_str}
			<br><br>
			<img src="graph.png">
			'''
	write_html(html_content)

if __name__ == "__main__":
	main()
