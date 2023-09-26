import cryptography.fernet
import requests
from bs4 import BeautifulSoup
import re
import bcrypt
from datetime import datetime, timedelta, time
import time as log_time
import logging
import json
import secrets
from cryptography.fernet import Fernet
import uuid
import time
import pickle

from discord_webhook import DiscordEmbed, DiscordWebhook
from WayGradeAccess.GoogleAPI.Google import Create_Service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from string import ascii_letters
from random import choice, randint
import smtplib
from email.message import EmailMessage
from flask_mail import Mail, Message
import numpy

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256:TLS13-AES-256-GCM-SHA384:ECDHE:!COMPLEMENTOFDEFAULT"


class Utils:

    @staticmethod
    def utc2est():
        current = datetime.now().strftime("%m/%d/%y %H:%M:%S ")
        return str(current)

    @staticmethod
    def date_formatting(date):
        print(datetime.strptime(date + ", 2021", '%a %b %d %I:%M %p, %Y'))

    @staticmethod
    def logger(message):
        ts = int(log_time.time())
        logging.basicConfig(filename=f"logs/site log %s.log" % ts,
                            format='%(message)s', level=logging.INFO)

        logging.info(str(Utils.utc2est()) + message)

        print(Utils.utc2est() + message)

    @staticmethod
    def writer(data, filename):
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def percent_to_letterGrade(percentage):

        if percentage >= 93:
            return "A"
        elif percentage >= 89.5:
            return "A-"
        elif percentage >= 79.5:
            grade = "B"
        elif percentage >= 69.5:
            grade = "C"
        elif percentage >= 59.5:
            grade = "D"
        else:
            return "F"

        ones_place = percentage % 10
        if 0 <= ones_place <= 2.5 or ones_place == 9.5:
            grade += "-"
        elif 2.5 <= ones_place < 6.5:
            pass
        elif 6.5 <= ones_place < 9.5 and grade != "A":
            grade += "+"

        return grade

    @staticmethod
    def get_letter_day():
        letter_days = ["A", "B", "C", "D", "E", "F", "G", "H"]
        preset_day = "2022-02-11"
        today = datetime.now().strftime("%Y-%m-%d")
        holidays = [
            "2022-02-19",
            "2022-02-20",
            "2022-02-21",
            "2022-02-22",
            "2022-02-23",
            "2022-02-24",
            "2022-02-25",
            "2022-02-26",
            "2022-02-27",
            "2022-04-15",
            "2022-04-16",
            "2022-04-17",
            "2022-04-18",
            "2022-04-19",
            "2022-04-20",
            "2022-04-21",
            "2022-04-22",
            "2022-04-23",
            "2022-04-24",
            "2022-05-30"
        ]
        count = numpy.busday_count(preset_day, today, holidays=[])
        letter_day = letter_days[count % len(letter_days)]
        return letter_day



    @staticmethod
    def gpa_calculator(class_details):

        if not class_details:
            print("NO CLASS DETAILS FOR GPA CALCULATOR!")
            return {"Weighted": "", "Unweighted": ""}

        LETTER_GPA = {
            "COLLEGE": {
                "A": 4.0,
                "A-": 3.7,
                "B+": 3.3,
                "B": 3.0,
                "B-": 2.7,
                "C+": 2.3,
                "C": 2.0,
                "C-": 1.7,
                "D+": 1.3,
                "D": 1.0,
                "D-": 0.7,
                "F": 0.0
            },
            "HONORS": {
                "A": 4.5,
                "A-": 4.2,
                "B+": 3.8,
                "B": 3.5,
                "B-": 3.2,
                "C+": 2.8,
                "C": 2.5,
                "C-": 2.2,
                "D+": 1.8,
                "D": 1.5,
                "D-": 1.2,
                "F": 0.5
            },
            "AP": {
                "A": 5.0,
                "A-": 4.7,
                "B+": 4.3,
                "B": 4.0,
                "B-": 3.7,
                "C+": 3.3,
                "C": 3.0,
                "C-": 2.7,
                "D+": 2.3,
                "D": 2.0,
                "D-": 1.7,
                "F": 1.0
            }
        }

        classes = class_details["CLASSES"]
        classCount = len(classes)
        unweightedTotal = 0
        weightedTotal = 0

        for _class in classes:
            className = _class["CLASS_NAME"]
            classGrade = _class["LETTER_GRADE"]
            if classGrade == "TBA":
                classCount -= 1
                continue

            AP = re.findall("AP", className)
            AP2 = re.findall("advanced placement", className.lower())
            HONORS = re.findall("honors", className.lower()) or re.findall(" H ", className) or re.findall("Hnrs", className)
            COLLEGE = re.findall("college", className.lower())

            # Unweighted GPA Calc
            unweightedTotal += LETTER_GPA["COLLEGE"][classGrade]

            # Weighted GPA Calc
            if COLLEGE:
                weightedTotal += LETTER_GPA["COLLEGE"][classGrade]
            elif HONORS:
                print(f"Found honors for {className}")
                weightedTotal += LETTER_GPA["HONORS"][classGrade]
            elif AP or AP2:
                weightedTotal += LETTER_GPA["AP"][classGrade]
            else:
                weightedTotal += LETTER_GPA["COLLEGE"][classGrade]
        if not classCount:
            weightedGPA = 0
            unweightedGPA = 0
        else:
            weightedGPA = round(weightedTotal / classCount, 2)
            unweightedGPA = round(unweightedTotal / classCount, 2)

        return {"Weighted": weightedGPA,
                "Unweighted": unweightedGPA}

    @staticmethod
    def settings():
        with open("databases/settings.json", "r") as settings_raw:
            settings = json.load(settings_raw)

            return settings["settings"]

    @staticmethod
    def captcha():
        s = requests.session()

        capMonsterApiKey = ""
        createTaskUrl = "https://api.capmonster.cloud/createTask"
        createTaskPayload = {
            "clientKey": capMonsterApiKey,
            "task":
                {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": "https://student.naviance.com/waylandhs",
                    "websiteKey": "6LfAN84UAAAAABfGTP7s2vIfa9lpQWoXg28LcQGV"
                }
        }
        createTask = s.post(createTaskUrl, json=createTaskPayload)
        taskId = createTask.json()["taskId"]

        getGRecapUrl = "https://api.capmonster.cloud/getTaskResult"
        getGRecapPayload = {
            "clientKey": capMonsterApiKey,
            "taskId": taskId
        }
        while True:
            time.sleep(1)
            getGRecap = s.post(getGRecapUrl, json=getGRecapPayload)
            captchaStatus = getGRecap.json()["status"]
            if captchaStatus == "processing":
                continue
            break
        print("Got response token!")
        token = getGRecap.json()["solution"]["gRecaptchaResponse"]
        return token


class UserTools:

    @staticmethod
    def all_user_data():
        with open("databases/user_info.json", "r") as user_info_raw:
            user_info = json.load(user_info_raw)
        return user_info

    @staticmethod
    def class_count(classes):
        totalClasses = 0
        for _class in classes:
            if not _class["DROPPED"]:
                totalClasses += 1
        return totalClasses

    @staticmethod
    def statistics():
        with open("databases/statistics.json", "r") as statisticsRaw:
            statistics = json.load(statisticsRaw)
            return statistics

    @staticmethod
    def log_user(user_dict):
        user_db = UserTools.all_user_data()
        email = user_dict["email"]

        # Log user info
        user_db["users"][email] = user_dict
        Utils.writer(data=user_db, filename="databases/user_info.json")
        print("LOGGED USER!")
        return True

    @staticmethod
    def request_handling(request_type, **kwargs):

        # Duplicate info check
        if request_type == "confirmation":
            code = kwargs.get("code")
            if not code:
                return {"message": "Please enter a confirmation code."}
        if request_type == "signup":
            email = kwargs.get("email")
            username = kwargs.get("username")
            password = kwargs.get("password")
            if not email or not username or not password:
                return {"message": "Mandatory fields missing."}

            if not re.findall("@student.waylandps.org", email):
                return {
                    "message": "Invalid email address. Please enter a valid WHS Student email (student.waylandps.org)."}

            for user in UserTools.all_user_data()["users"].values():
                if user["username"] == username:
                    return {"message": "Username already in use."}
                elif user["email"] == email:
                    return {"message": "Email already in use."}

            return 200
        if request_type == "login":

            password = kwargs.get("password")
            email = kwargs.get("email")
            if not email or not password:
                return {"message": "Mandatory fields missing."}

            if not Authentication.user_auth(email, password):
                return {"message": "Credentials are incorrect."}
            return 200
        else:
            assert "CLOSED DOWN DUE TO INTRUDER."

    @staticmethod
    def eschool_login(username, password, quarter):
        if not username or not password:
            return {"message": "Mandatory fields missing."}

        VERIFICATION_TOKEN = None
        s = requests.session()

        LOGIN_PAGE = {
            "URL": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
            }
        }
        print("Getting page...")
        try:
            LOGIN_PAGE_GET = s.get(LOGIN_PAGE["URL"], headers=LOGIN_PAGE["HEADERS"])
        except Exception as exc:
            print("EXCEPTION OCCURRED: " + str(exc))
            raise exc
        LOGIN_PAGE_HTML = BeautifulSoup(LOGIN_PAGE_GET.text, "html.parser")
        for INPUT in LOGIN_PAGE_HTML.find_all("input", {"name": "__RequestVerificationToken"}):
            VERIFICATION_TOKEN = INPUT["value"]

        if not VERIFICATION_TOKEN:
            assert "NoVerificationTokenError"
        print("Logging in...")
        LOGIN = {
            "URL": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
                "Referer": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
                "Origin": "https://esp41pehac.eschoolplus.powerschool.com",
                "Upgrade-Insecure-Requests": "1"
            },
            "DATA": {
                "__RequestVerificationToken": VERIFICATION_TOKEN,
                "SCKTY00328510CustomEnabled": False,
                "SCKTY00436568CustomEnabled": False,
                "Database": "480",
                "VerificationOption": "UsernamePassword",
                "LogOnDetails.UserName": username,
                "tempUN": "",
                "tempPW": "",
                "LogOnDetails.Password": password
            }
        }
        LOGIN_POST = s.post(LOGIN["URL"], data=LOGIN["DATA"], headers=LOGIN["HEADERS"])
        invalid_credentials = re.findall("invalid username or password", LOGIN_POST.text)
        request_error = re.findall("An error occurred while processing your request", LOGIN_POST.text)

        # ESCHOOL ERROR HANDLING
        if invalid_credentials:
            return {"message": "Credentials are incorrect."}
        if request_error:
            return {"message": "An error occurred while logging in."}

        # PARSE GRADE HTML

        CLASSWORK = {
            "URL": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/Content/Student/Assignments.aspx",
            "HEADERS": {
                "Referer": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/Content/Student/Assignments.aspx",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
            },
            "DATA": {
                "__EVENTTARGET": "ctl00$plnMain$btnRefreshView",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": "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",
                "__VIEWSTATEGENERATOR": "B0093F3C",
                "__EVENTVALIDATION": "EcNFn+gz2/mkzyg7BBlc5TrO6XOXtHMpjuY+SWcqyiqOVSvBLaHoT95MTaVLGlh0KhLNF5nd3NSiN2JEHAFHme+J0KQxGPC9xBsYAI6w9+V1cySab4OwXfZ+iWAG6ZYz32cG81Sc42D0nKsxexkniORBbeMUBx6JdhoVP2p9Ou/BgVX5rkF2hyDwDc5y69eZEXfch12o45gosS3B3dcrAZt9DrHh8RjUyuRkHNqJBpxaVyNcq3bH8D6UsKO0IV5NXPAFdAZd5Ht39zmO1JPhDTuULp+qm8w/mEUkMEP7z2DD04CKNXmmR9PhLk81hr+wpq4Uz7G4PvEMav1Dx2R9GGXwSNwBRSIZI0xqcZz/jTKEUI3JIyhzSbi1S0QTC0qs+TOGWYZIYZLYuDvxpLsC/8AodEcB0uSet5FDcnnbILApAIbH89vaswFoeuD+KKqxSg1p0ErArYjI1Z7Nhmp3TFmNwRb/JFTyq5aWgOT0yBTzFXdwopSUMzpHB416bVoNT881Ilzzlf0BY/7gLZRBoHQTKEv0myGeeMh6Ys7ahLceGWRZ9ra/kY9nYdJsvrRPX3Wx6I0d7J96Cx+gZ9IPRanbdc4rqWh0hz1uKSbnezNQcgrhOryeqRXVNgnJNu/GW8s6w9zcu5f+qT/IMQ6a+mEPcyxe36xaoi1KatoD975+/mXDVuOQVGKnqiQdygXEfeUZstTjlZnOcSt1I0R5uNLB2N6IaZseO2CccMFXeN85ymqqIY7oeaaZSb9k629AXraHFt5JgVpLoX6zJyf1E02Ny02V2EQI3bORRa3AiWtiBACaezjiMwQ7S2obBJ78D3MtAqEbt9Dege7wkghmvdxc8P49B7iO2+/7gyODnJWJH6IX4ehdTyC6QCnWuq0IStrHAmHDbJu90JXUFCJHKGvbNa/t4bWuqohmR8ESwexIrh1mx2lzZ+Owoir13ooN1reg+SH0Jx2peiI6utyX/upZCMytQF42LMyX+GzBN5OMPARyoaUFXJvMYt8KsdNwEP4HT9pjaEUzn+TXdDxkVBt1qlfUPAaV4ZARUKCd11ZAJv0LrL+JW5gkQ39+n33IhX3cHKjKSrt+auOoYT8croM9TdTGWATea5EL2pxclwQ4zNer6BbS8Cq+X+uZ94UnCkF8at9zjUXrjvYJl/wMvXHvkTnWv9wtcz8DEaGboTC/v6i9jGRlOmE7l/QbLg9+bJ2MOEIX3KpjLDo9upAXA0R0KFf8AzJEabiRtydxWGJ7GcGCL/nzdVH4utou12K4qtTSjvqQuCm41GHTs8U0+sQ+nubbX5Dgy4DKddbtyorNC3aeNw58xcjnt1iy7mOtJ/dxlIElhO2OWMCRTiirbXtrn55lclg/iZcqr/lUu7u7FROvSrySOfWmvOHReG7eYGYFDCIY/SH9KNhfTmEdMzcE2LtmQ1vExM+5q50i6rjKKt49WPhfXZYXiA1nTKOL",
                "ctl00$plnMain$ddlReportCardRuns": quarter,  # {QUARTER}-2022
                "ctl00$plnMain$ddlClasses": "ALL",
                "ctl00$plnMain$ddlCompetencies": "ALL",
                "ctl00$plnMain$ddlOrderBy": "Class"
            }
        }
        CLASSWORK_GET = s.post(CLASSWORK["URL"], data=CLASSWORK["DATA"], headers=CLASSWORK["HEADERS"])
        CLASSWORK_HTML = BeautifulSoup(CLASSWORK_GET.text, "html.parser")

        # CLASSES
        CLASS_LIST = {
            "CLASSES": []
        }
        for CLASS in CLASSWORK_HTML.find_all("a", {"class": "sg-header-heading"}):
            CLASS_NAME = str(CLASS.text).strip().replace("\r\n", "")
            CLASS_LIST["CLASSES"].append(
                {
                    "CLASS_NAME": CLASS_NAME,
                    "DROPPED": False,
                    "AVERAGE_GRADE": "",
                    "LETTER_GRADE": "",
                    "CLASSWORK": []
                }
            )

        # GRADES
        class_num = 0
        for DIV in CLASSWORK_HTML.find_all("div", {"class": "AssignmentClass"}):
            # Check if class is dropped
            if DIV.find_all("span", {"class": "sg-header-sub-heading DroppedCourse"}):
                CLASS_LIST["CLASSES"][class_num]["DROPPED"] = True
                CLASS_LIST["CLASSES"][class_num]["CLASS_NAME"] += " (DROPPED)"

            for ASSIGNMENT_NAME_TAG in DIV.find_all("a"):
                ASSIGNMENT_NAME = str(ASSIGNMENT_NAME_TAG.text).replace('\r\n', "").strip()
                CLASS_LIST["CLASSES"][class_num]["CLASSWORK"].append(
                    {
                        "ASSIGNMENT NAME": ASSIGNMENT_NAME,
                        "Assignment ID": str(uuid.uuid4()),
                        "GRADE": ""
                    }
                )
            del CLASS_LIST["CLASSES"][class_num]["CLASSWORK"][0]
            SPAN = False
            for SPAN in CLASSWORK_HTML.find_all("span",
                                                {"id": f"plnMain_rptAssigmnetsByCourse_lblOverallAverage_{class_num}"}):
                CLASS_LIST["CLASSES"][class_num]["AVERAGE_GRADE"] = SPAN.text
                CLASS_LIST["CLASSES"][class_num]["LETTER_GRADE"] = Utils.percent_to_letterGrade(float(SPAN.text))
            if not SPAN:
                CLASS_LIST["CLASSES"][class_num]["AVERAGE_GRADE"] = "TBA"
                CLASS_LIST["CLASSES"][class_num]["LETTER_GRADE"] = "TBA"

            assign_num = 0
            GRADE_LIST = []
            for ASSIGNMENT_GRADE_TAG in DIV.find_all("td", {"class": "sg-view-quick"}):
                ASSIGNMENT_GRADE = ASSIGNMENT_GRADE_TAG.text
                GRADE_LIST.append(ASSIGNMENT_GRADE)
                if len(GRADE_LIST) == 4:
                    if GRADE_LIST[3] == "Percentage":
                        del GRADE_LIST[0:4]
                        continue
                    PercentageGrade = GRADE_LIST[3]
                    if not re.findall("%", PercentageGrade):
                        LetterGrade = "TBA"
                    else:
                        PercentageGrade = str(GRADE_LIST[3]).replace("%", "")
                        LetterGrade = Utils.percent_to_letterGrade(float(PercentageGrade))

                    weighted_score = GRADE_LIST[1]
                    weighted_total_score = GRADE_LIST[2]

                    GRADE_DICT = {
                        "Weight": GRADE_LIST[0],
                        "Weighted Score": str(GRADE_LIST[1]),
                        "Weighted Total Points": str(GRADE_LIST[2]),
                        "Percentage": GRADE_LIST[3],
                        "Letter Grade": LetterGrade,
                    }
                    CLASS_LIST["CLASSES"][class_num]["CLASSWORK"][assign_num]["GRADE"] = GRADE_DICT
                    GRADE_LIST = []
                    assign_num += 1
                else:
                    continue

            # ASSIGN_DUE_LIST = []
            # for ASSIGNMENT_DATE_TAG in DIV.find_all("tr", {"class": "sg-asp-table-data-row"}):
            #     DATE_TAG = ASSIGNMENT_DATE_TAG.find("td")
            #     print(ASSIGNMENT_DATE_TAG)
            # date_num = 0
            # for DATE in DATE_TAG:
            #     print(DATE)
            #     if date_num == 2:
            #         break
            #     ASSIGN_DUE_LIST.append(DATE.text)
            #     date_num += 1

            class_num += 1

        return {"message": 200, "payload": CLASS_LIST}

    @staticmethod
    def eschool_schedule(username, password):
        if not username or not password:
            return {"message": "Mandatory fields missing."}

        VERIFICATION_TOKEN = None
        s = requests.session()

        LOGIN_PAGE = {
            "URL": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
            }
        }
        print("Getting page...")
        try:
            LOGIN_PAGE_GET = s.get(LOGIN_PAGE["URL"], headers=LOGIN_PAGE["HEADERS"])
        except Exception as exc:
            print("EXCEPTION OCCURRED: " + str(exc))
            raise exc
        LOGIN_PAGE_HTML = BeautifulSoup(LOGIN_PAGE_GET.text, "html.parser")
        for INPUT in LOGIN_PAGE_HTML.find_all("input", {"name": "__RequestVerificationToken"}):
            VERIFICATION_TOKEN = INPUT["value"]

        if not VERIFICATION_TOKEN:
            assert "NoVerificationTokenError"
        print("Logging in...")
        LOGIN = {
            "URL": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
                "Referer": "https://esp41pehac.eschoolplus.powerschool.com/HomeAccess/SessionReset?sitecode=wyllive",
                "Origin": "https://esp41pehac.eschoolplus.powerschool.com",
                "Upgrade-Insecure-Requests": "1"
            },
            "DATA": {
                "__RequestVerificationToken": VERIFICATION_TOKEN,
                "SCKTY00328510CustomEnabled": False,
                "SCKTY00436568CustomEnabled": False,
                "Database": "480",
                "VerificationOption": "UsernamePassword",
                "LogOnDetails.UserName": username,
                "tempUN": "",
                "tempPW": "",
                "LogOnDetails.Password": password
            }
        }
        LOGIN_POST = s.post(LOGIN["URL"], data=LOGIN["DATA"], headers=LOGIN["HEADERS"])
        invalid_credentials = re.findall("invalid username or password", LOGIN_POST.text)
        request_error = re.findall("An error occurred while processing your request", LOGIN_POST.text)
        print(LOGIN_POST.url)

        # ESCHOOL ERROR HANDLING
        if invalid_credentials:
            return {"message": "Credentials are incorrect."}
        if request_error:
            return {"message": "An error occurred while logging in."}

        SCHEDULE_DETAILS = []
        scheduleGET = s.get("https://esp41pehac.eschoolplus.powerschool.com//HomeAccess/Content/Student/Classes.aspx",
                            headers=LOGIN_PAGE["HEADERS"])
        scheduleHTML = BeautifulSoup(scheduleGET.text, "html.parser")
        print(scheduleGET.url)
        scheduleTABLE = scheduleHTML.find("table", {"id": "plnMain_dgSchedule"})
        for CLASS in scheduleTABLE.find_all("tr", {"class": "sg-asp-table-data-row"}):
            scheduleDETAILS = CLASS.find_all("td")
            scheduleDict = {
                "ID": str(scheduleDETAILS[0].text).strip(),
                "NAME": str(scheduleDETAILS[1].text).strip(),
                "PERIOD": str(scheduleDETAILS[2].text).strip(),
                "TEACHER": str(scheduleDETAILS[3].text).strip(),
                "LOCATION": str(scheduleDETAILS[4].text).strip(),
                "LETTER_DAY": [letter_day.strip() for letter_day in str(scheduleDETAILS[5].text).strip().split(",")],  #
                "QUARTERS": [quarter.strip() for quarter in str(scheduleDETAILS[6].text).strip().split(",")],
                "STATUS": str(scheduleDETAILS[8].text).strip()
            }
            SCHEDULE_DETAILS.append(scheduleDict)
        print(SCHEDULE_DETAILS)
        LETTER_SCHEDULE = {
            "Q1": {
                "A": ["1", "2", "ADV", "3", "5", "6", "7"],
                "B": ["4", "1", "ADV", "2", "8", "5", "6"],
                "C": ["3", "4", "ADV", "1", "7", "8", "5"],
                "D": ["2", "3", "ADV", "4", "6", "7", "8"],
                "E": ["1", "2", "ADV", "3", "5", "6", "7"],
                "F": ["4", "1", "ADV", "2", "8", "5", "6"],
                "G": ["3", "4", "ADV", "1", "7", "8", "5"],
                "H": ["2", "3", "ADV", "4", "6", "7", "8"]
            },
            "Q2": {
                "A": ["1", "2", "ADV", "3", "5", "6", "7"],
                "B": ["4", "1", "ADV", "2", "8", "5", "6"],
                "C": ["3", "4", "ADV", "1", "7", "8", "5"],
                "D": ["2", "3", "ADV", "4", "6", "7", "8"],
                "E": ["1", "2", "ADV", "3", "5", "6", "7"],
                "F": ["4", "1", "ADV", "2", "8", "5", "6"],
                "G": ["3", "4", "ADV", "1", "7", "8", "5"],
                "H": ["2", "3", "ADV", "4", "6", "7", "8"]
            },
            "Q3": {
                "A": ["1", "2", "ADV", "3", "5", "6", "7"],
                "B": ["4", "1", "ADV", "2", "8", "5", "6"],
                "C": ["3", "4", "ADV", "1", "7", "8", "5"],
                "D": ["2", "3", "ADV", "4", "6", "7", "8"],
                "E": ["1", "2", "ADV", "3", "5", "6", "7"],
                "F": ["4", "1", "ADV", "2", "8", "5", "6"],
                "G": ["3", "4", "ADV", "1", "7", "8", "5"],
                "H": ["2", "3", "ADV", "4", "6", "7", "8"]
            },
            "Q4": {
                "A": ["1", "2", "ADV", "3", "5", "6", "7"],
                "B": ["4", "1", "ADV", "2", "8", "5", "6"],
                "C": ["3", "4", "ADV", "1", "7", "8", "5"],
                "D": ["2", "3", "ADV", "4", "6", "7", "8"],
                "E": ["1", "2", "ADV", "3", "5", "6", "7"],
                "F": ["4", "1", "ADV", "2", "8", "5", "6"],
                "G": ["3", "4", "ADV", "1", "7", "8", "5"],
                "H": ["2", "3", "ADV", "4", "6", "7", "8"]
            }
        }
        for _class in SCHEDULE_DETAILS:
            for quarter in _class["QUARTERS"]:
                for letter_day in _class["LETTER_DAY"]:

                    for period in LETTER_SCHEDULE[quarter][letter_day]:
                        if period == _class["PERIOD"]:
                            location = LETTER_SCHEDULE[quarter][letter_day].index(period)
                            LETTER_SCHEDULE[quarter][letter_day][location] = _class["NAME"]

        return LETTER_SCHEDULE

    @staticmethod
    def naviance_login(username, password):
        session = requests.session()

        print("Getting login captcha...")
        reCaptchaV3 = Utils.captcha()

        LOGIN = {
            "URL": "https://blue-ridge-api.naviance.com/security/login",
            "HEADERS": {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "origin": "https://student.naviance.com"
            },
            "DATA": {
                "username": username,
                "password": password,
                "highSchoolAlias": "waylandhs",
                "highSchoolId": "19374USPU",
                "asGuest": False,
                "captchaToken": reCaptchaV3
            }
        }
        print("Logging into naviance...")
        LOGIN_POST = session.post(LOGIN["URL"], json=LOGIN["DATA"], headers=LOGIN["HEADERS"])
        response = LOGIN_POST.json()

        return response

    @staticmethod
    def naviance_collection(**kwargs):
        s = requests.session()
        email = kwargs.get("email")

        jwt = kwargs.get("jwt")
        if not jwt:
            username = kwargs.get("username")
            password = kwargs.get("password")

            naviance_login_response = UserTools.naviance_login(username, password)
            try:
                error = naviance_login_response["message"]
                if error:
                    return {"message": naviance_login_response["message"]["error"]}
            except TypeError:
                pass

            jwt = naviance_login_response

            # Set JWT into user_data
            with open("databases/user_info.json", "r") as f:
                users = json.load(f)

                print("Saving token to email:", email)
                users["users"][email]["naviance"]["NavianceSessionToken"] = jwt
                Utils.writer(users, "databases/user_info.json")

        # Colleges I'm Thinking About
        THINKING = "https://blue-ridge-api.naviance.com/college/colleges-im-thinking-about?limit=9999"

        THINKING_GET = s.get(THINKING, headers=UserTools.naviance_headers(jwt))
        THINKING_DATA = THINKING_GET.json()["data"]

        for college in THINKING_DATA:
            print(college["college"]["name"])
        return {"message": 200, "payload": {}}

    @staticmethod
    def naviance_headers(jwt):
        return {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "authorization": jwt
        }

    @staticmethod
    def assignment_details(class_details):

        classes = class_details["CLASSES"]

        for _class in classes:
            class_name = _class["CLASS_NAME"]
            # print("Compiling for:", class_name)
            # print("------------------------")
            assignments = _class["CLASSWORK"]
            assignments.reverse()

            for assignment_main in range(len(assignments)):
                assignment = assignments[assignment_main]
                # print("----------------------------")
                # print(assignment["ASSIGNMENT NAME"])
                total_class_points = 0
                class_points = 0

                for assignment_sub in range(assignment_main + 1):

                    assignment_total_points = assignments[assignment_sub]["GRADE"]["Weighted Total Points"]
                    assignment_points = assignments[assignment_sub]["GRADE"]["Weighted Score"]
                    assignment_letter_grade = assignments[assignment_sub]["GRADE"]["Letter Grade"]

                    if assignment_letter_grade == "TBA" or assignment_points == "N/A" or assignment_total_points == "N/A" or assignment_points == "\xa0":
                        continue
                    # print("Adding:", assignment_points, "for assignment:", assignments[assignment_sub]["ASSIGNMENT NAME"])
                    total_class_points += float(assignment_total_points)
                    class_points += float(assignment_points)
                assignment["GRADE"]["TOTAL EARNED AT TIME"] = str(class_points)
                assignment["GRADE"]["TOTAL CLASS POINTS AT TIME"] = str(total_class_points)
                # print("Completed compiling...")

            assignments.reverse()
            for assignment in assignments:
                # print("Starting Grade Delta Calculating...")
                # print("----------------------------")
                # print("----------------------------")

                # print(assignment["ASSIGNMENT NAME"])
                assignment_total_points = assignment["GRADE"]["Weighted Total Points"]
                assignment_points = assignment["GRADE"]["Weighted Score"]
                assignment_letter_grade = assignment["GRADE"]["Letter Grade"]

                if assignment_letter_grade == "TBA" or assignment_points == "N/A" or assignment_total_points == "N/A" or assignment_points == "\xa0":
                    delta = "TBA"
                else:
                    delta = UserTools.percent_difference(float(assignment["GRADE"]["TOTAL CLASS POINTS AT TIME"]),
                                                         float(assignment["GRADE"]["TOTAL EARNED AT TIME"]),
                                                         float(assignment_total_points), float(assignment_points))
                    assignment["GRADE"]["Weighted Total Points"] = round(float(assignment_total_points), 2)
                    assignment["GRADE"]["Weighted Score"] = round(float(assignment_points), 2)

                assignment["GRADE"]["GRADE_DELTA"] = delta

        # Utils.writer(class_details, "classdetailstest.json")
        return class_details

    @staticmethod
    def username_to_email(username):
        with open("databases/user_info.json") as users_raw:
            users = json.load(users_raw)

            for user in users["users"].values():
                if user["username"] == username:
                    return user["email"]
            return False

    @staticmethod
    def percent_difference(total_points, current_points, assignment_max_points, student_gained_points):

        GRADE_PERCENTAGE = (current_points / total_points) * 100
        # print("percentage: " + str(GRADE_PERCENTAGE))

        total_points_before = total_points - assignment_max_points
        current_points_before = current_points - student_gained_points

        # print("CURRENT POINTS (BEFORE):", current_points_before)
        # print("TOTAL POINTS (BEFORE):", total_points_before)
        if current_points_before == 0 and total_points_before == 0:
            return {
                "PERCENT DELTA": 0,
                "BEFORE": {
                    "LETTER": "A",
                    "PERCENT": 100
                },
                "AFTER": {
                    "LETTER": Utils.percent_to_letterGrade(GRADE_PERCENTAGE),
                    "PERCENT": round(GRADE_PERCENTAGE)
                }
            }

        GRADE_PERCENTAGE_BEFORE = (current_points_before / total_points_before) * 100
        # print("percentage before: " + str(GRADE_PERCENTAGE_BEFORE))

        PERCENT_DIFFERENCE = GRADE_PERCENTAGE - GRADE_PERCENTAGE_BEFORE
        # print("percent difference: " + str(PERCENT_DIFFERENCE))
        return {
            "PERCENT DELTA": round(PERCENT_DIFFERENCE, 3),
            "BEFORE": {
                "LETTER": Utils.percent_to_letterGrade(GRADE_PERCENTAGE_BEFORE),
                "PERCENT": round(GRADE_PERCENTAGE_BEFORE, 2)
            },
            "AFTER": {
                "LETTER": Utils.percent_to_letterGrade(GRADE_PERCENTAGE),
                "PERCENT": round(GRADE_PERCENTAGE, 2)
            }
        }

    @staticmethod
    def grad_year_to_grade(grad_year):
        site_info = Site()
        graduations = None
        try:
            if site_info.startSchoolYear == str(datetime.now().year):
                graduations = {
                    f"{datetime.now().year + 1}": "Senior",
                    f"{datetime.now().year + 2}": "Junior",
                    f"{datetime.now().year + 3}": "Sophomore",
                    f"{datetime.now().year + 4}": "Freshman",
                }
            elif site_info.endSchoolYear == str(datetime.now().year):
                graduations = {
                    f"{datetime.now().year}": "Senior",
                    f"{datetime.now().year + 1}": "Junior",
                    f"{datetime.now().year + 2}": "Sophomore",
                    f"{datetime.now().year + 3}": "Freshman",
                }
        except KeyError:
            return "Not in High School"
        return graduations[grad_year]


class Authentication:

    @staticmethod
    def valid_confirmation_code(code, confUser):

        if code == confUser["confCode"]:
            return True
        return False

    @staticmethod
    def user_auth(email, password):
        Utils.logger("USER: Authenticating: %s..." % email)
        User = UserTools.all_user_data()["users"][email]

        validPassword = bcrypt.checkpw(bytes(password.encode("utf-8")), User["password"].encode("utf-8"))

        if validPassword:
            return True
        return False

    @staticmethod
    def set_auth_token(response, email):

        print("Created token")
        user_secure_token = secrets.token_hex()
        UserData = UserTools.all_user_data()
        User = UserData["users"][email]

        # USER AUTH COOKIE
        Utils.logger("Created token for: %s --> %s" % (User["email"], user_secure_token))
        expiration_day_count = 365
        response.set_cookie('auth_token', user_secure_token, max_age=86400 * expiration_day_count)

        UserData["users"][email]["token"] = user_secure_token
        Utils.writer(UserData, "databases/user_info.json")
        return True

    @staticmethod
    def valid_auth_token(email, token):
        if not email or not token:
            return False

        User = UserTools.all_user_data()["users"][email]
        UserToken = User["token"]

        print("CHECKING SAVED TOKEN: " + UserToken, email)
        print("CHECKING ATTEMPTED TOKEN:", token)

        if token == UserToken:
            print("VALID TOKEN, ACCESSING...")
            return True
        print("NOT VALID TOKEN. BLOCKING...")
        return False

    @staticmethod
    def new_key():
        return Fernet.generate_key()

    @staticmethod
    def encryption(data, encrypt_key):
        e = Fernet(encrypt_key)
        return e.encrypt(bytes(data, "utf-8")).decode()  # NEEDS TO BE IN BYTES FOR DECRYPTION

    @staticmethod
    def decryption(data, decrypt_key):
        d = Fernet(decrypt_key)
        try:
            decrypted_data = d.decrypt(bytes(data, "utf-8"))
        except cryptography.fernet.InvalidToken:
            return False
        except ValueError:
            return False
        return decrypted_data

    @staticmethod
    def set_secure_login_key(response, email, EUsername, EPassword, naviance):
        username_cookie_name = "ESecureLoginU"
        password_cookie_name = "ESecureLoginP"
        username_key_name = "ESchoolUsernameKey"
        password_key_name = "ESchoolPasswordKey"
        if naviance:
            username_cookie_name = "NavSecureLoginU"
            password_cookie_name = "NavSecureLoginP"
            username_key_name = "NavianceUsernameKey"
            password_key_name = "NaviancePasswordKey"

        username_key = Authentication.new_key()
        password_key = Authentication.new_key()

        encrypted_username = Authentication.encryption(EUsername, username_key)
        encrypted_password = Authentication.encryption(EPassword, password_key)

        expiration_day_count = 365
        response.set_cookie(username_cookie_name, encrypted_username, max_age=86400 * expiration_day_count)
        response.set_cookie(password_cookie_name, encrypted_password, max_age=86400 * expiration_day_count)

        UserData = UserTools.all_user_data()
        UserData["users"][email][username_key_name] = username_key.decode()
        UserData["users"][email][password_key_name] = password_key.decode()
        Utils.writer(UserData, "databases/user_info.json")


class Site:
    # Calibration
    def __init__(self):
        self.schoolYear = "2022-2024"
        self.startSchoolYear = "2022"
        self.endSchoolYear = "2023"
        self.schoolQuarter = "1"

    def site_info(self):
        quarterEndDict = {
            "Quarter1": datetime(2021, 11, 5),
            "Quarter2": datetime(2022, 1, 28),
            "Quarter3": datetime(2022, 4, 8),
            "Quarter4": datetime(2022, 6, 16)
        }
        quarterDelta = str(quarterEndDict[f"Quarter{self.schoolQuarter}"] - datetime.now()).split(",")[0]
        if not re.findall("day", quarterDelta):
            quarterDelta = quarterDelta.split(":")[0] + " hours"

        site_info = {
            "quarterDelta": quarterDelta
        }
        return site_info


class Confirmation:

    @staticmethod
    def sendGmailConfirmationCode(email):
        CLIENT_SECRET_FILE = "/Users/benjamin_stahl/PycharmProjects/WayGrade/databases/client_secret.json"
        API_NAME = "gmail"
        API_VERSION = "v1"
        SCOPES = ["https://mail.google.com/"]
        confCodeMinChar = 6
        confCodeMaxChar = 6
        service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

        string_format = ascii_letters
        generated_string = "".join(
            choice(string_format) for x in range(randint(confCodeMinChar, confCodeMaxChar)))

        emailMsg = 'Your WayGrade Confirmation Code: ' + generated_string
        mimeMessage = MIMEMultipart()
        mimeMessage['to'] = email
        mimeMessage['subject'] = 'WayGrade Confirmation Code'
        mimeMessage.attach(MIMEText(emailMsg, 'plain'))
        raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

        message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
        return generated_string

    @staticmethod
    def sendAdminNotification(email):
        CLIENT_SECRET_FILE = "databases/client_secret.json"
        API_NAME = "gmail"
        API_VERSION = "v1"
        SCOPES = ["https://mail.google.com/"]
        service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

        emailMsg = f"'{email}' just signed up for WayGrade!"
        mimeMessage = MIMEMultipart()
        mimeMessage['to'] = "benastahl@gmail.com"
        mimeMessage['subject'] = 'Someone new just signed up for WayGrade!'
        mimeMessage.attach(MIMEText(emailMsg, 'plain'))
        raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

        message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()

    @staticmethod
    def sendSMTPConfirmationCode(email):
        string_format = ascii_letters
        generated_string = "".join(
            choice(string_format) for x in range(randint(6, 6)))

        smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        smtp_server.login('waygradewebsite@gmail.com', '{}'.format(""))

        msg = EmailMessage()
        msg.set_content("Your WayGrade confirmation code: " + generated_string)
        msg['Subject'] = 'WayGrade Confirmation Code'
        msg['From'] = "WayGrade"
        msg['To'] = email

        smtp_server.send_message(msg=msg)
        print('Successfully the mail is sent')
        smtp_server.quit()
        return generated_string


class Settings:

    @staticmethod
    def unlinkESchool(response, email):
        response.set_cookie("SecureLoginP", "", max_age=0)
        response.set_cookie("SecureLoginU", "", max_age=0)

        UserData = UserTools.all_user_data()
        UserData["users"][email]["ESchoolUsernameKey"] = ""
        UserData["users"][email]["ESchoolPasswordKey"] = ""


class Admin:

    @staticmethod
    def valid_api_key(key):
        with open("databases/api_key.json") as api_keyRaw:
            apiKeyLibrary = json.load(api_keyRaw)["keys"]

            if key in apiKeyLibrary:
                return True
        return False

    @staticmethod
    def valid_admin_auth_token(key):
        admin = UserTools.all_user_data()["users"]["benjamin_stahl@student.waylandps.org"]
        try:
            admin_auth_token = admin["admin_auth_token"]
        except KeyError:
            return False

        if key == admin_auth_token:
            return True
        return False

    @staticmethod
    def user_count():
        return len(UserTools.all_user_data()["users"])

    @staticmethod
    def visitationsToday():
        statistics = UserTools.statistics()
        today = datetime.now().strftime("%m/%d/%y")
        if today not in statistics.keys():
            statistics[today] = {
                "visitations": 0,
                "visitors": []
            }
        Utils.writer(statistics, "databases/statistics.json")

        return statistics[today]["visitations"]

    @staticmethod
    def visitationsTotal():
        return UserTools.statistics()["visitationsTotal"]

    @staticmethod
    def maintenanceWebhook(exc, line, file):
        webhook = DiscordWebhook(
            url="")

        # create embed object for webhook
        embed = DiscordEmbed(title='WayGrade Exception Error Occurred')

        # set footer
        embed.set_footer(text='WayGrade')

        # set timestamp (default is now)
        embed.set_timestamp()

        # add fields to embed
        embed.add_embed_field(name='Exception:', color=15987431, value="```%s```" % exc)
        embed.add_embed_field(name='Exception File:', color=15987431, value="```%s```" % file)
        embed.add_embed_field(name='Exception Line:', color=15987431, value="```%s```" % line)

        # add embed object to webhook
        webhook.add_embed(embed)

        webhook.execute()

    @staticmethod
    def add_user_parameter():
        user_data = UserTools.all_user_data()
        for user in user_data["users"]:
            user_data["users"][user]["schedule"] = {}
        Utils.writer(user_data, "databases/user_info.json")
