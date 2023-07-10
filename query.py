import requests
import jwt
import json
import logging
import urllib.parse


# config
client_password = ''
client_username = ''

# extracted from the apk
jwtUrl = "https://auth.vodafone.hu/oxauth/restv1/token"
jwtBearerToken = 'MjI5YjMxZDAtNzVkZi00MWUwLTllZjQtNDc0MGY2MWM2MDBkOld5UUo5UU9TMXlJclR5Q242bnRTeW5CYw=='
jwtClientId = '229b31d0-75df-41e0-9ef4-4740f61c600d'
jwtClientSecret = 'WyQJ9QOS1yIrTyCn6ntSynBc'
bearerUrl = 'https://public.api.vodafone.hu/oauth2/token'
bearerClientId = '8mBeBG93vTOWHwcYk9TIWmEXey2QPczD' 

def setupDebugPrints():
	try:
		import http.client as http_client
	except ImportError:
		# Python 2
		import httplib as http_client
	http_client.HTTPConnection.debuglevel = 1

	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

def getJwt():
	payload = f'client_id={jwtClientId}&client_secret={jwtClientSecret}&scope=other openid&grant_type=password&keep_signed_in=true&password={client_password}&username={client_username}'

	headers = {
		'Authorization': f'Basic {jwtBearerToken}',
		'Content-Type': 'application/x-www-form-urlencoded',
	}

	json_data = json.loads(requests.post(jwtUrl, headers=headers, data=payload).text)
	return json_data["access_token"]

def getBearer(jwtToken):
	grant_type = urllib.parse.quote_plus('urn:ietf:params:oauth:grant-type:jwt-bearer')
	payload = f'client_id={bearerClientId}&assertion={jwtToken}&grant_type={grant_type}'

	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
	}

	json_data = json.loads(requests.post(bearerUrl, headers=headers, data=payload).text)
	return json_data["access_token"]

def callMvaApi(token, path):

	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': f'Bearer {token}'

	}
	data = json.loads(requests.get(f'https://public.api.vodafone.hu/mva-api{path}', headers=headers).text)
	print(f'### {path} :')
	print(json.dumps(data, indent=4))
	print(f'###\n\n')

def main():
	global masterToken
	#setupDebugPrints()

	if masterToken is None:
		
		jwt = getJwt()
		print(f'got jwt: {jwt} \n')
		
		masterToken = getBearer(jwt)
		print(f'got bearer: {masterToken}\n')
	else:
		print(f'reusing hardcoded token: {masterToken}')
	
	callMvaApi(masterToken, '/customerAPI/v1/personalInformation')
	callMvaApi(masterToken, '/customerAPI/v1/billingAccount')
	callMvaApi(masterToken, '/productAPI/v2/myPlan')
	callMvaApi(masterToken, '/productAPI/v2/devices')
	callMvaApi(masterToken, '/productAPI/v2/currentSpend')
	callMvaApi(masterToken, '/productAPI/v2/discountInfo')
	callMvaApi(masterToken, '/productAPI/v2/extraService')


#masterToken = ""
masterToken = None

main()
