import requests
from io import BytesIO
import json

if __name__ == "__main__":
    url = 'http://localhost:9080/store/validate/long'
    print('Starting request')
    s = BytesIO()
    r = requests.get(url, stream=True)
    prevchunk = None
    for chunk in r.iter_content():
        if chunk:
            s.write(chunk)
            s.flush()
            if prevchunk is b'\n' and chunk is b'\n':
                # print(s.getvalue())
                j = json.loads(s.getvalue())
                print('{} is at {}%'.format(j['message'], j['percentage'] ))
                s = BytesIO()
            prevchunk = chunk
        
    r.close()