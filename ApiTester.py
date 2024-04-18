##ALL OF THIS FILE IS FOR DEBUGGING AND TESTING THE API.

import requests

username = input("Enter Username: ")
password = input("Enter Password: ")

url = 'http://localhost:5000/get/account'
data = {}
response = requests.post(url, json=data)
print (response)
auth_token = response.headers.get('Authorization')

auth_token = f'Bearer {auth_token}'

headers = {'Authorization': auth_token}

url2 = 'http://localhost:5000/requires-token'


response = requests.get(url2, headers=headers)


if response.ok:
    data = response.json()
    print('Success:', data)
else:
    print('Failed:', response.status_code)
