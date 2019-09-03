from esdl.processing import ESDLAsset
import settings
import requests


#TODO: find proper way
def send_alert(msg):
    print(msg)


class EDR_assets:

    def __init__(self):
        self.current_asset = None
        self.EDR_config = settings.edr_config
        pass

    def get_asset_from_EDR(self, edr_asset_id):
        url = self.EDR_config['EDR_host'] + self.EDR_config['EDR_path'] + edr_asset_id + '?format=xml'
        print('EDR url: ', url)

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/xml",
            'User-Agent': "ESDL Mapeditor/0.1"
            # 'Cache-Control': "no-cache",
            # 'Host': ESSIM_config['ESSIM_host'],
            # 'accept-encoding': "gzip, deflate",
            # 'Connection': "keep-alive",
            # 'cache-control': "no-cache"
        }

        try:
            r = requests.get(url, headers=headers)
            # print(r)
            # print(r.content)
            if r.status_code == 200:
                result = r.text
                # print(result)
                self.current_asset = ESDLAsset.load_asset_from_string(result)
                return self.current_asset
            else:
                send_alert('Error getting EDR asset - response ' + str(r.status_code) + ' with reason: ' + str(
                    r.reason))
                print(r)
                print(r.content)
                return 0
        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return 0