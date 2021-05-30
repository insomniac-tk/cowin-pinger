#  APIs are subject to a rate limit of 100 API calls per 5 minutes per IP.
import concurrent.futures
import datetime
import json
import os
import time

import requests
from dotenv import load_dotenv
from playsound import playsound

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

def write_to_file(data_dict, outfile='dump.csv'):
	"""
	pin_code | min_age_limit
	time center_name slots available min age vaccine
	"""
	line=""
	for key,value in data_dict.items():
		line+= f"{value},"
	
	with open(outfile,'a') as out:
		out.write(line)
		out.write("\n")

def play_alert(alert_sound):
	playsound(alert_sound,block=False)

def check_avail(pin,response_dict,outfile='log.txt'):
	curr_time = datetime.datetime.now().strftime("%H:%M:%S")
	if len(response_dict) >= 1:
		for center in response_dict:
			min_age = center['min_age_limit']
			available_doses = center['available_capacity_dose1']
			pincode = center['pincode']
			avail = center['available_capacity_dose1']
			vaccine = center['vaccine']
			center_name = center['name']
			if min_age == 45 and avail > 0:
				play_alert('alert.mp3')
				data_dict = {
				'pincode':pincode,
				'center_name':center_name,
				'avail_dose':available_doses,
				'age':min_age,
				'vaccine':vaccine,
				'curr_time':curr_time
				}
				write_to_file(data_dict)
				return("Pin:{pin}, Time: {curr_time}, # Slots: {avail}")
		return f'[{curr_time}, {pin}] X X X'
	else:
		return f'[{curr_time}, {pin}] X X X'


def ping_cowin(base_url, date, pincode,timeout=300):
	ping_count = 0 
	start = time.time()
	user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Mobile Safari/537.36"
	headers = {'User-Agent':user_agent}
	while time.time() - start < timeout:
		query_string = f"pincode={pincode}&date={date}"
		request_url = base_url + "?" + query_string
		response = requests.get(request_url,headers=headers)
		ping_count+=1
		if response.status_code == 200:
			payload = json.loads(response.content.decode())
			if check_avail(pincode, payload['sessions']):
				print(check_avail(pincode, payload['sessions']),flush=True)
		else:
			print(f'Request failed with status code: {response.status_code}. Time: {time.time()}',flush=True)
		time.sleep(3)
	return(f"{ping_count} ping counts in last 5 minutes for pin {pincode}")
		



if __name__ == "__main__":
	pin_codes = [] # add pincodes here 
	pin_str = ",".join(pin_codes)
	print(f"Looking for sessions in {pin_str}")
	today =  datetime.datetime.now()
	curr_time = datetime.datetime.now().strftime("%H:%M:%S")
	print(f"Start time: {curr_time}")
	date = (today+datetime.timedelta(days=1)).strftime("%d-%m-%y")
	while True:
		with concurrent.futures.ThreadPoolExecutor() as executor:
			results = [executor.submit(ping_cowin,BASE_URL, date, pin) for pin in pin_codes]
			for f in concurrent.futures.as_completed(results):
				print(f.result(),flush=True)
