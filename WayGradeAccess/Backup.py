from controls import UserTools, Utils
import requests
import json

API_KEY = ""
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256:TLS13-AES-256-GCM-SHA384:ECDHE:!COMPLEMENTOFDEFAULT"


def update():
    USER_DATA_GET = requests.get(f"https://www.waygrade.com/api/user_data?api_key={API_KEY}")
    STATISTICS_GET = requests.get(f"https://www.waygrade.com/api/statistics?api_key={API_KEY}")
    print("Writing to file...")
    USER_DATA = json.loads(str(USER_DATA_GET.text).replace("'", '"'))
    STATISTICS = json.loads(str(STATISTICS_GET.text).replace("'", '"'))

    Utils.writer(USER_DATA, "../databases/user_info.json")
    Utils.writer(STATISTICS, "../databases/statistics.json")
    print("Done!")


if __name__ == '__main__':
    update()
