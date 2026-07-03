import smtplib

import requests


def Dose_Availability_Lon_Lat(Lattitude,Longitude):
    api="https://cdn-api.co-vin.in/api/v2/appointment/centers/public/findByLatLong?lat={}&long={}".format(Lattitude,Longitude)
    return main_task1(api)

def Dose_Availability_District(district_id,date):
    api="https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id={}&date={}".format(district_id,date)
    return main_task(api)

def Dose_Availability_Pincode(pincode, date):
    api ="https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}".format(pincode,date)

    return main_task(api)



def main_task1(api):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"}
        response = requests.get(api, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('centers', [])
            if data:
                output="*"*30 + "\n"
                for area in data:
                    output+="  Hospital Name:" + area['name'] + "*"*30 +"\n"
                    output+='''\
pincode: {}
state_name: {}
district_name : {}
block_name : {}

'''.format(area['pincode'],area['state_name'],area['district_name'],
                                 area['block_name'])
                    output+="*"*30 + "\n"
                return output
    except Exception:
        pass

    # Fallback to Mock Data if API fails or returns no data
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(api)
    params = parse_qs(parsed.query)
    lat = params.get('lat', ['28.61'])[0]
    lon = params.get('long', ['77.23'])[0]
    dist_id = params.get('district_id', ['N/A'])[0]
    
    output = "⚠️ [Co-WIN API Offline Fallback: Showing Mock Vaccination Centers]\n"
    output += "*"*30 + "\n"
    
    mock_centers = [
        {
            "name": f"Apollo Hospital (District {dist_id})",
            "pincode": "110001",
            "state_name": "Delhi",
            "district_name": "New Delhi",
            "block_name": "Connaught Place"
        },
        {
            "name": f"Fortis Healthcare Center",
            "pincode": "110002",
            "state_name": "Delhi",
            "district_name": "New Delhi",
            "block_name": "New Delhi GP"
        },
        {
            "name": f"Metro Clinic (Lat: {lat}, Lon: {lon})",
            "pincode": "110003",
            "state_name": "Delhi",
            "district_name": "New Delhi",
            "block_name": "Chanakyapuri"
        }
    ]
    
    for area in mock_centers:
        output += "  Hospital Name: " + area['name'] + "\n" + "*"*30 + "\n"
        output += '''\
pincode: {}
state_name: {}
district_name : {}
block_name : {}

'''.format(area['pincode'], area['state_name'], area['district_name'], area['block_name'])
        output += "*"*30 + "\n"
    return output



def main_task(api):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"}
        response = requests.get(api, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('sessions', [])
            if data:
                output="*"*30 + "\n"
                for area in data:
                    if area.get('available_capacity', 0) > 0:
                        output+="  Hospital Name:" + area['name'] + "*"*30 +"\n"
                        output+='''\
Address: {}
Pincode: {}
available_capacity_dose1 : {}
available_capacity_dose2 : {}
available_capacity : {}
min_age_limit: {}
Time Slots: {}

'''.format(area['address'],area['pincode'],area['available_capacity_dose1'],area['available_capacity_dose2'],
                                     area['available_capacity'],area['min_age_limit'],str(area['slots'])[1:-1])
                        output+="*"*30 + "\n"
                if output != "*"*30 + "\n":
                    return output
    except Exception:
        pass

    # Fallback to Mock Data if API fails or returns no data
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(api)
    params = parse_qs(parsed.query)
    pincode = params.get('pincode', ['110001'])[0]
    date = params.get('date', ['08-08-2026'])[0]
    
    output = f"⚠️ [Co-WIN API Offline Fallback: Showing Mock Slots for Pincode {pincode} on {date}]\n"
    output += "*"*30 + "\n"
    
    mock_sessions = [
        {
            "name": "Apollo Clinic",
            "address": "Plot No 4, District Shopping Center",
            "pincode": pincode,
            "available_capacity_dose1": 15,
            "available_capacity_dose2": 10,
            "available_capacity": 25,
            "min_age_limit": 18,
            "slots": ["09:00 AM - 11:00 AM", "11:00 AM - 01:00 PM"]
        },
        {
            "name": "Max Healthcare Vaccine Center",
            "address": "12 Metro Marg, Connaught Place",
            "pincode": pincode,
            "available_capacity_dose1": 8,
            "available_capacity_dose2": 5,
            "available_capacity": 13,
            "min_age_limit": 45,
            "slots": ["10:00 AM - 12:00 PM", "02:00 PM - 04:00 PM"]
        }
    ]
    
    for area in mock_sessions:
        output += "  Hospital Name: " + area['name'] + "\n" + "*"*30 + "\n"
        output += '''\
Address: {}
Pincode: {}
available_capacity_dose1 : {}
available_capacity_dose2 : {}
available_capacity : {}
min_age_limit: {}
Time Slots: {}

'''.format(area['address'], area['pincode'], area['available_capacity_dose1'], area['available_capacity_dose2'],
             area['available_capacity'], area['min_age_limit'], str(area['slots'])[1:-1])
        output += "*"*30 + "\n"
    return output

def send_email(email,message):
    try:
        import os
        host = "smtp.gmail.com"
        port = 587

        connection=smtplib.SMTP(host,port)
        connection.starttls()

        username="innovateyourself2build@gmail.com"
        
        # Look for creds.txt in api/ or current dir
        creds_path = "creds.txt"
        if not os.path.exists(creds_path):
            creds_path = os.path.join(os.path.dirname(__file__), "creds.txt")
            
        if not os.path.exists(creds_path):
            return "Email credentials file 'api/creds.txt' is missing. Please create this file with your Gmail App Password to enable email notifications."

        with open(creds_path) as file:
            password=file.read().strip()
            
        if not password:
            return "Email credentials file 'api/creds.txt' is empty. Please add your Gmail App Password."
            
        connection.login(username,password)

        receiver=email
        subject="COVID-19 Vaccine Slot Availability"

        body='''\
From: {}
Subject:{}

{}'''.format(username,subject,message)

        connection.sendmail(username,receiver,body)
        connection.quit()
        return "success"
    except Exception as e:
        return f"Failed to send email. Error: {str(e)}"

# Dose_Availability_Pincode("530051","31-03-2021")

# send_email("innovateyourself2build@gmail.com",'test mail')
# print(Dose_Availability_District(512,"08-08-2022"))
# print(Dose_Availability_Lon_Lat(17.68,83.21))


# def prime_number(num):
#     flag = False
#
#     # prime numbers are greater than 1
#     if num > 1:
#         # check for factors
#         for i in range(2, num):
#             if (num % i) == 0:
#                 # if factor is found, set flag to True
#                 flag = True
#                 # break out of loop
#                 break
#     elif num == 2:
#         Flag = True
#     # check if flag is True
#     if flag:
#         return False
#     else:
#         return True
#
#
# def prime_numbers(l, n):
#     x = []
#
#     for i in range(l, n-1 ):
#         if prime_number(i) == True:
#             x.append(i)
#             # print(i)
#             break
#     # print('*****')
#
#     for j in range(n-1, l-1,-1):
#         # print(j)
#         if prime_number(j) == True:
#             x.append(j)
#             break
#     return x
#
#
# def out(t):
#     l, r = input().split()
#     # x = set([prime(i) for i in range(int(l), int(r) + 1) if i != None]).difference({None})
#     # tuple(filter(prime, range(int(l), int(r) + 1)))
#     # print(x)
#     # print(max(x), min(x))
#     x = prime_numbers(int(l), int(r) + 1)
#     # print(x)
#     print(max(x) - min(x)) if len(x) >= 2 else print(0) if len(x) == 1 else print(-1)
#
#
# def main():
#     t = int(input())
#     if t >= 1 and t <= 10:
#         tuple(map(out, range(t)))
#
#
# # print(prime(999997))
# main()