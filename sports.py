import requests
import re
import json
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta

from controls import Site


class HudlSports:

    def __init__(self):
        self.teamUrl = {
            "Boys Varsity Football": "https://www.hudl.com/team/v2/15811/Boys-Varsity-Football/",  # 1532948
            "Boys Varsity Hockey": "https://www.hudl.com/team/v2/68066/Wayland-Boys-Ice-Hockey/",
            "Boys Varsity Soccer": "https://www.hudl.com/team/v2/48990/Wayland-Warriors/"
        }  # BOOBIES
        self.teamCodes = {
            "Boys Varsity Football": {
                "teamCode": "15811",
                "seasonCode": "1532948"
            }
        }

    def schedule(self, sport):
        s = requests.session()

        SCHEDULE = s.get(self.teamUrl[sport] + "schedule")

        SCHEDULE_HTML = BeautifulSoup(SCHEDULE.text, 'html.parser')

        for HUDL_EMBED in SCHEDULE_HTML.find_all("script"):
            if re.findall("__hudlEmbed", str(HUDL_EMBED)):
                RAW_HUDL = str(HUDL_EMBED.text).replace(";", "").replace("window.__hudlEmbed=", "")
                WAYLAND = json.loads(RAW_HUDL)

                SCHEDULE = WAYLAND["model"]["team"]["allSeasons"][0]["events"]

        return SCHEDULE

    def roster(self, sport):
        s = requests.session()

        ROSTER_GET = s.get(
            f"https://www.hudl.com/team/v2/{self.teamCodes[sport]['teamCode']}/athletes?seasonId={self.teamCodes[sport]['seasonCode']}")

        ROSTER = ROSTER_GET.json()

        for ATHLETE in ROSTER:
            print(ATHLETE["fullName"])
        print(ROSTER_GET.url)


class ArbiterSchedule:

    def __init__(self):
        self.teamCodes = {

            # Football
            "Boys Varsity Football": "4297159",
            "Boys JV Football": "7675963",
            "Boys Freshman Football": "7675959",

            # Baseball
            "Boys Varsity Baseball": "7490652",
            "Boys JV Baseball": "7490653",
            "Boys Freshman Baseball": "7490654",

            # Basketball
            "Boys Varsity Basketball": "4457224",
            "Boys JV Basketball": "4457696",
            "Boys Freshman Basketball": "4467259",
            "Girls Varsity Basketball": "4467345",
            "Girls JV Basketball": "4467346",
            "Girls Freshman Basketball": "4483969",

            # Competitive Cheer
            "Girls Varsity Competitive Cheer": "9428382",

            # Cross Country
            "Boys Varsity Cross Country": "4273867",
            "Girls Varsity Cross Country": "9440231",

            # Field Hockey
            "Girls Varsity Field Hockey": "4213019",
            "Girls JV Field Hockey": "4281624",
            "Girls Freshman Field Hockey": "4273238",

            # Golf
            "Boys Varsity Golf": "4213267",

            # Hockey
            "Boys Varsity Hockey": "6002275",
            "Boys JV Hockey": "7597275",

            # Lacrosse
            "Boys Varsity Lacrosse": "7647476",
            "Boys JV Lacrosse": "7647475",
            "Girls Varsity Lacrosse": "4603477",
            "Girls JV Lacrosse": "4603483",
            "Girls Freshman Lacrosse": "4603475",

            # Sailing
            "Coed Varsity Sailing": "8000979",

            # Soccer
            "Boys Varsity Soccer": "4268555",
            "Boys JV Soccer": "4268734",
            "Boys Freshman Soccer": "4297199",

            "Girls Varsity Soccer": "4268221",
            "Girls JV Soccer": "4268284",
            "Girls Freshman Soccer": "4268322",

            # Softball
            "Girls Varsity Softball": "5500128",
            "Girls JV Softball": "8098054",
            "Girls Freshman Softball": "711633",

            # Swimming
            "Boys Varsity Swimming": "7516775",
            "Coed Varsity Swimming": "7738222",
            "Coed JV Swimming": "7738221",
            "Girls Varsity Swimming": "9092024",

            # Tennis
            "Boys Varsity Tennis": "9292010",

            # Volleyball
            "Boys Varsity Volleyball": "4044307",
            "Boys JV Volleyball": "4057920",
            "Girls Varsity Volleyball": "4044308",
            "Girls JV Volleyball": "4057921",
            "Girls Freshman Volleyball": "4274232",

            # Wrestling
            "Boys Varsity Wrestling": "4300729",
            "Boys JV Wrestling": "7731410"
        }

    def schedule(self, team):
        s = requests.session()

        SCHEDULE_GET = s.get("https://arbiterlive.com/Teams/Schedule/" + self.teamCodes[team])

        SCHEDULE_HTML = BeautifulSoup(SCHEDULE_GET.text, 'html.parser')

        allGameDetails = []
        for GAME in SCHEDULE_HTML.find_all("tr", {"class": "gameRow"}):
            DETAILS = GAME.find_all("td")

            gameDetails = []
            for DETAIL in DETAILS:
                gameDetails.append(
                    str(DETAIL.text).replace("\r\n                            \r\n                            ",
                                             " ").replace("\r\n                            \n", " ").strip())
            allGameDetails.append(gameDetails)

        # Parse collected list details
        SCHEDULE = []
        for GAME in allGameDetails:

            DATE = GAME[0]
            OPPONENT = str(GAME[2]).replace("'", "")
            print(OPPONENT)
            LOCATION = str(GAME[3]).replace("'", "")
            SCORE = GAME[4]
            LEAGUE = GAME[5]

            if not SCORE:
                SCORE = "TBA"

            SCHEDULE.append({
                "OPPONENT": OPPONENT,
                "DATE": DATE,
                "LOCATION": LOCATION,
                "SCORE": SCORE,
                "LEAGUE": LEAGUE,
                "TEAM_DATA": {

                }
            }
            )
        SCHEDULE.reverse()
        return SCHEDULE


class MaxPrepsSchedule:
    def __init__(self):
        self.buildCode = None

    def buildIdCollector(self):

        s = requests.session()

        GET = s.get("https://www.maxpreps.com/high-schools/wayland-warriors-(wayland,ma)/football/home.htm")

        GET_HTML = BeautifulSoup(GET.text, "html.parser")

        JSON_RAW = GET_HTML.find("script", {"id": "__NEXT_DATA__"}).text
        DATA = json.loads(JSON_RAW)
        self.buildCode = DATA["buildId"]
        return DATA["buildId"]

    def allSportsCollector(self):
        self.buildIdCollector()

        s = requests.session()
        INDEX = s.get(
            f"https://www.maxpreps.com/team/_next/data/{self.buildCode}/index.json?apptype=0&schoolid=ebfdb5dc-f288-4971-86b9-21810fe847d3&ssid=97e3f828-856d-419e-b94f-7f41319fe3d3&allSeasonId=22e2b335-334e-4d4d-9f67-a0f716bb1ccd")

        allSportsData = INDEX.json()["pageProps"]["teamContext"]["teamSeasonPickerData"]

        allSports = {}
        for sportData in allSportsData:
            if sportData["year"] == Site().schoolYear:
                sportName = sportData["gender"] + " " + sportData["level"] + " " + sportData["sport"]
                allSports[sportName] = {
                    "year": sportData["year"],
                    "season": sportData["season"],
                    "data": {
                        "allSeasonId": sportData["allSeasonId"],
                        "sportSeasonId": sportData["sportSeasonId"]
                    }
                }
        return allSports

    def schedule(self, sport):

        s = requests.session()
        sportData = self.allSportsCollector()[sport]

        PARAMS = {
            "apptype": "0",
            "schoolid": "ebfdb5dc-f288-4971-86b9-21810fe847d3",
            "ssid": sportData["data"]["sportSeasonId"],
            "allSeasonId": sportData["data"]["allSeasonId"]
        }

        GET = s.get("https://www.maxpreps.com/team/_next/data/FGOV5So79VV6BBdcrK0JV/schedule.json", params=PARAMS)
        DATA = GET.json()["pageProps"]

        SCHEDULE_DATA = DATA["linkedDataJson"]["event"]

        ALL_GAME_DETAILS = []
        for GAME in SCHEDULE_DATA:

            TITLE = GAME["name"]
            LOCATION = GAME["location"]["name"]
            DATE = GAME["startDate"]

            if LOCATION != "Wayland":
                OPPONENT = GAME["homeTeam"]["name"]
                OPPONENT_URL = GAME["homeTeam"]["url"]
            else:
                OPPONENT = GAME["awayTeam"]["name"]
                OPPONENT_URL = GAME["awayTeam"]["url"]

            ALL_GAME_DETAILS.append(
                {
                    "title": TITLE,
                    "location": LOCATION,
                    "date": DATE,
                    "opponent": OPPONENT,
                    "opponent_url": OPPONENT_URL
                }
            )
        # Put in order from closest to oldest
        ALL_GAME_DETAILS.reverse()
        return ALL_GAME_DETAILS

    def roster(self, sport):

        s = requests.session()
        allSportsCollector = self.allSportsCollector()
        if sport not in allSportsCollector.keys():
            return {}

        sportData = allSportsCollector[sport]

        PARAMS = {
            "apptype": "0",
            "schoolid": "ebfdb5dc-f288-4971-86b9-21810fe847d3",
            "ssid": sportData["data"]["sportSeasonId"],
            "allSeasonId": sportData["data"]["allSeasonId"]
        }

        GET = s.get(f"https://www.maxpreps.com/team/_next/data/{self.buildCode}/roster.json", params=PARAMS)

        DATA = GET.json()["pageProps"]
        return DATA


class SportCalendarExport:

    @staticmethod
    def create_sport_calendar(sport):
        cal = Calendar()
        (sport_name, schedule_string) = sport.split("$")
        schedule = json.loads(schedule_string.replace("'", '"'), strict=False)

        for game in schedule:
            opponent = game["OPPONENT"]
            date_format = '%a %b %d %I:%M %p, %Y'
            year = "2022"

            if re.findall("TBA", game["DATE"]):
                date_format = '%a %b %d TBA, %Y'
            location = game["LOCATION"]
            date = datetime.strptime(game["DATE"] + f", {year}", date_format)

            if date.month < 7:
                year = "2023"
                date = datetime.strptime(game["DATE"] + f", {year}", date_format)

            event = Event()
            event.add("summary", f"{sport_name}: Wayland V. {opponent}")
            event.add("location", location)
            event.add("dtstart", date)
            event.add("dtend", date + timedelta(hours=2))
            cal.add_component(event)

        with open(f"SportCalendars/{sport_name}.ics", "wb") as f:
            f.write(cal.to_ical())
            return sport_name

