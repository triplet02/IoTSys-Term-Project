import http.client
import urllib.parse

key = '9PTV37GXQ7O3XIIT'


def update(fields, values):
    if len(fields) != len(values):
        return -1
    
    payload = dict()
    for field, value in zip(fields, values):
        payload['field{}'.format(field)]=value
    
    payload['api_key']=key
    
    params = urllib.parse.urlencode(payload)
    headers = {'Content-typZZe':'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
    conn = http.client.HTTPConnection('api.thingspeak.com:80')
    
    try:
        conn.request('POST', '/update', params, headers)
        response = conn.getresponse()
        print(response.status, response.reason)
        conn.close()
    except:
        print("Connection Failed.")
    
    