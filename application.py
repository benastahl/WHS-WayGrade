#!/usr/bin/env python3

import secrets
import bcrypt
import json
import uuid
import re
import numpy

from datetime import datetime
from flask import Flask, request, redirect, make_response, send_file
from flask import render_template
from controls import Utils, Authentication, Site, UserTools, Confirmation, Settings, Admin
from sports import MaxPrepsSchedule, ArbiterSchedule, SportCalendarExport
from flask_mail import Mail, Message
from string import ascii_letters
from random import choice, randint

app = Flask(__name__)


@app.before_request
def before_request():
    if not re.findall("127", str(request.url)):

        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)


@app.route("/privacy", methods=["GET"])
def display_privacy():
    return render_template("privacy_policy.html")


@app.route("/terms-of-service", methods=["GET"])
def display_terms_of_service():
    return render_template("terms_of_service.html")


@app.route("/about", methods=["GET"])
def display_vis_about():
    return render_template("visitor_about.html")


# API


@app.route("/api/user_data", methods=["GET"])
def collect_user_data():
    if request.args.get("api_key"):
        if Admin.valid_api_key(request.args.get("api_key")):
            return UserTools.all_user_data()
    return redirect("/login")


@app.route("/api/statistics", methods=["GET"])
def collect_statistics():
    if request.args.get("api_key"):
        if Admin.valid_api_key(request.args.get("api_key")):
            return UserTools.statistics()
    return redirect("/login")


@app.route("/api/_abck", methods=["GET"])
def secret_auth():
    if request.args.get("api_key") == "djawipoheioahdoiawhdoiauwhdayueg1982w1089h":
        return render_template("_abck.html"), 200
    return redirect("_abck.html"), 403


# ADMIN

@app.route("/admin_login", methods=["GET"])
def display_admin_login():
    return render_template("login.html")


@app.route("/admin_login", methods=["POST"])
def process_admin_login():
    password = request.form["pass"]
    email = request.form["email"]

    checkPassword = bcrypt.checkpw(bytes(password, "utf8"),
                                   b'$2b$12$VlADkLXhxQJUYQ4utWooJec1xSkdBcWKN8iWRfRxHqZe95b2Ng25.')
    checkEmail = bcrypt.checkpw(bytes(email, "utf8"), b'$2b$12$HGeMQQ/FyJf0UB5w1nBaVO8DAM1lkYsq3Djf49gQxye/bq2q476sO')

    if checkPassword and checkEmail:
        response = redirect("/admin_dashboard")
        admin_auth_token = secrets.token_hex()
        userData = UserTools.all_user_data()
        userData["users"]["benjamin_stahl@student.waylandps.org"]["admin_auth_token"] = admin_auth_token

        Utils.writer(userData, "databases/user_info.json")

        response.set_cookie("admin_auth_token", admin_auth_token, max_age=3600)
        return response

    return render_template("admin_login.html", message={"message": "Just stop trying lol"})


@app.route("/admin_dashboard", methods=["GET"])
def display_admin_dashboard():
    if not Admin.valid_admin_auth_token(request.cookies.get("admin_auth_token")):
        return redirect("/login")

    # User Data Collection for Display

    userCount = Admin.user_count()

    visitationsToday = Admin.visitationsToday()

    visitationsTotal = Admin.visitationsTotal()

    users = UserTools.all_user_data()["users"]

    today = datetime.now().strftime("%m/%d/%y")
    visitors = UserTools.statistics()[today]["visitors"]

    return render_template('admin.html',
                           username="benastahl",
                           userCount=str(userCount),
                           users=users,
                           visitationsToday=visitationsToday,
                           visitationsTotal=visitationsTotal,
                           visitors=visitors
                           )


# HOMEPAGE


@app.route("/", methods=["GET"])
def homepage():
    response = make_response(redirect("/login"))
    auth_token = request.cookies.get("auth_token")
    if auth_token:
        users = UserTools.all_user_data()["users"]

        for user in users.values():
            if user["token"] == auth_token:
                response = make_response(redirect("/grades/%s" % user['username']))

    return response


# SIGNUP


@app.route('/signup', methods=["GET"])
def display_signup():
    response = make_response(render_template("signup.html"))
    return response


@app.route('/signup', methods=["POST"])
def process_signup():
    username = request.form["username"]
    password = bcrypt.hashpw(bytes(str(request.form["pass"]).encode("utf-8")), bcrypt.gensalt())
    email = request.form["email"]
    tos_agree = request.form.get("tos-agree")

    if not tos_agree:
        return render_template('signup.html', message={"message": "Agree to the TOS to access the site."})

    creationDate = Utils.utc2est()

    signup_handling = UserTools.request_handling(email=email, username=username, password=password,
                                                 request_type="signup")

    if signup_handling != 200:
        return render_template('signup.html', message=signup_handling)

    response = redirect(f"/confirmation?email={email}")

    with open("databases/confirmation.json", "r") as confirmRaw:
        confirmationUsers = json.load(confirmRaw)
        token = secrets.token_hex()

        # string_format = ascii_letters
        # generated_string = "".join(
        #     choice(string_format) for x in range(randint(6, 6)))
        #
        # msg = Message('WayGrade Confirmation Code', sender='waygradewebsite@gmail.com', recipients=[email])
        # msg.body = "Your WayGrade confirmation code: " + generated_string
        # mail.send(msg)
        try:
            confirmationUsers["TempUsers"][email] = {
                "username": username,
                "email": email,
                "password": str(password.decode("utf-8")),
                "creationDate": creationDate,
                "confCode": Confirmation().sendGmailConfirmationCode(email),
                "token": token
            }
        except Exception as error:
            print("OCCURRED:", error)
            raise error

        Utils.writer(confirmationUsers, "databases/confirmation.json")

    # Set confirmation auth token
    response.set_cookie('conf_token', token, max_age=86400 * 1)

    return response


# CONFIRMATION

@app.route('/confirmation', methods=["GET"])
def display_confirmation():
    email = request.args.get("email")
    conf_token = request.cookies.get("conf_token")

    if not email or not conf_token:
        return redirect("/login")

    return render_template("confirmation.html")


@app.route("/confirmation", methods=["POST"])
def process_confirmation():
    confirmationCode = request.form.get("code")
    email = request.args.get("email")

    confirmationRaw = open("databases/confirmation.json", "r")
    confirmationUsers = json.load(confirmationRaw)
    if not email or email not in confirmationUsers["TempUsers"].keys():
        return redirect("/login")

    confUser = confirmationUsers["TempUsers"][email]

    password = confUser["password"]
    creationDate = confUser["creationDate"]
    username = confUser["username"]

    if not password or not creationDate or not username:
        return redirect("/login")

    confirmation_handling = UserTools.request_handling(code=confirmationCode, request_type="confirmation")

    if not Authentication.valid_confirmation_code(confirmationCode, confUser):
        return render_template("confirmation.html", message=confirmation_handling)

    # User has been confirmed

    confirmationUsers["TempUsers"].pop(email)
    Utils.writer(confirmationUsers, "databases/confirmation.json")

    user_dict = {
        "username": username,
        "email": email,
        "password": password,
        "creationDate": creationDate,
        "ESchoolUsernameKey": "",
        "ESchoolPasswordKey": "",
        "token": "",
        "profilePicture": "",
        "community_service": [],
        "graduation_year": "",
        "naviance": {
            "NavianceSessionToken": "",
            "NavianceUsernameKey": "",
            "NaviancePasswordKey": ""
        },
        "schedule": {}

    }

    Confirmation().sendAdminNotification(email)
    UserTools.log_user(user_dict)

    # Set cookie

    response = make_response(redirect(f'/dashboard/{username}'))
    response.set_cookie('conf_token', "", max_age=0)
    set_cookie = Authentication.set_auth_token(response, email)

    if not set_cookie:
        return redirect('/login')

    Utils.logger(f"{username} ({email}) signed up successfully with password: ({password}).")
    return response


# LOGIN

@app.route('/login', methods=["GET"])
def display_login():
    response = make_response(render_template("login.html"))

    return response


@app.route('/login', methods=["POST"])
def process_login():
    password = request.form["pass"]
    email = request.form["email"]
    user_data = UserTools.all_user_data()

    if email not in user_data["users"].keys():
        return render_template('login.html', message={"message": "Email not found."})

    User = user_data["users"][email]
    username = User["username"]

    login_handling = UserTools.request_handling(email=email,
                                                password=password,
                                                request_type="login",
                                                )
    if login_handling != 200:
        return render_template('login.html', message=login_handling)

    # Set cookie
    response = make_response(redirect(f'/dashboard/{username}'))
    set_cookie = Authentication.set_auth_token(response, email)
    if not set_cookie:
        return redirect('/login')

    Utils.logger(f"{username} ({email}) logged in successfully.")
    return response


# DASHBOARD

@app.route("/dashboard/<username>", methods=["GET"])
def display_dashboard(username):
    return redirect(f"/grades/{username}")


# PROFILE

@app.route("/profile/<username>", methods=["GET"])
def display_profile(username):
    auth_token = request.cookies.get("auth_token")
    email = UserTools.username_to_email(username)

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]
    grade_name = UserTools.grad_year_to_grade(User["graduation_year"])

    return render_template("profile.html", username=username, User=User, grade_name=grade_name)


# SPORTS

@app.route("/sports/<username>", methods=["GET"])
def display_sports(username):
    auth_token = request.cookies.get("auth_token")
    email = UserTools.username_to_email(username)

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]

    selectedSport = "Boys Varsity Football"
    if request.args.get("sport"):
        selectedSport = request.args.get("sport")

    sportSchedule = ArbiterSchedule().schedule(selectedSport)
    sportSchedule.reverse()

    response = make_response(
        render_template("sports.html",
                        username=username,
                        User=User,
                        sportSchedule=sportSchedule,
                        allSports=ArbiterSchedule().teamCodes,
                        selectedSportRoster=MaxPrepsSchedule().roster(selectedSport),
                        selectedSport=selectedSport

                        )
    )

    return response


@app.route("/sports/<username>", methods=["POST"])
def process_sports(username):
    auth_token = request.cookies.get("auth_token")
    email = UserTools.username_to_email(username)

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    selectedSport = "Boys Varsity Football"
    if "refresh sports" in request.form:
        selectedSport = request.form.get("sport-select")

    if "download sports schedule" in request.form:
        calSport = request.form.get("download sports schedule")
        fileName = SportCalendarExport.create_sport_calendar(calSport)
        return send_file("SportCalendars/" + fileName + ".ics", as_attachment=True)

    return redirect(f"/sports/{username}?sport={selectedSport}")


# GRADES

@app.route("/grades/<username>", methods=["GET"])
def display_grades(username):
    auth_token = request.cookies.get('auth_token')
    email = UserTools.username_to_email(username)

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect('/login')

    User = UserTools.all_user_data()["users"][email]

    selectedQuarter = "ALL"
    submitQuarter = "ALL"
    if request.args.get("quarter"):
        submitQuarter = request.args.get("quarter")
        selectedQuarter = request.args.get("quarter")
    if selectedQuarter != "ALL":
        submitQuarter = submitQuarter[1] + "-2022"

    print("Collecting ESchool info with locally saved encrypted username and pass...")

    ESchoolUsernameEncrypted = request.cookies.get("ESecureLoginU")
    ESchoolPasswordEncrypted = request.cookies.get("ESecureLoginP")

    gradesResponse = make_response(
        render_template('grades.html',
                        username=username,
                        site_data=Site().site_info(),
                        class_data=False,
                        User=User
                        )
    )

    if not ESchoolUsernameEncrypted or not ESchoolPasswordEncrypted or not User["ESchoolUsernameKey"] or not User[
        "ESchoolPasswordKey"]:
        return gradesResponse

    ESchoolUsername = Authentication.decryption(ESchoolUsernameEncrypted, User["ESchoolUsernameKey"])
    ESchoolPassword = Authentication.decryption(ESchoolPasswordEncrypted, User["ESchoolPasswordKey"])

    if not ESchoolUsername or not ESchoolPassword:
        return gradesResponse

    print("Collecting display details...")
    CLASS_DETAILS_RESPONSE = UserTools.eschool_login(ESchoolUsername, ESchoolPassword, quarter=submitQuarter)

    if CLASS_DETAILS_RESPONSE["message"] != 200:
        return gradesResponse

    CLASS_DETAILS = UserTools.assignment_details(CLASS_DETAILS_RESPONSE["payload"])
    totalClasses = UserTools.class_count(CLASS_DETAILS["CLASSES"])

    gpa_data = Utils.gpa_calculator(CLASS_DETAILS)
    site_data = Site().site_info()

    letterColors = {
        "A": {
            "background": "#C0F2D8",
            "color": "#2BD47D"
        },
        "B": {
            "background": "#cce5ff",
            "color": "#66b0ff"
        },
        "C": {
            "background": "#ffe8b3",
            "color": "#ffc233"
        },
        "D": {
            "background": "#f7d4d7",
            "color": "#e05260"
        },
        "F": {
            "background": "#f7d4d7",
            "color": "#e05260"
        },
        "TBA": {
            "background": "#cce5ff",
            "color": "#66b0ff"
        }
    }

    gradesResponse = make_response(
        render_template('grades.html',
                        username=username,
                        site_data=site_data,
                        class_data=CLASS_DETAILS,
                        User=User,
                        gpa_data=gpa_data,
                        quarter_selection=["ALL", "Q1", "Q2", "Q3", "Q4"],
                        selectedQuarter=selectedQuarter,
                        totalClasses=str(totalClasses),
                        letterColors=letterColors

                        )
    )

    return gradesResponse


@app.route("/grades/<username>", methods=["POST"])
def process_grades(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]

    # Refresh Grades (refresh-grades)
    if "refresh grades" in request.form:

        # Quarter the user selected
        quarter_selection = request.form.get("quarter-select")

        selectedQuarter = quarter_selection
        if quarter_selection != "ALL":
            quarter_selection = quarter_selection[1] + "-2022"

        # Collect ESchool Info IF info is saved
        ESchoolUsernameEncrypted = request.cookies.get("ESecureLoginU")
        ESchoolPasswordEncrypted = request.cookies.get("ESecureLoginP")

        if not ESchoolUsernameEncrypted or not ESchoolPasswordEncrypted or not User["ESchoolUsernameKey"] or not User[
            "ESchoolPasswordKey"]:
            return redirect(f"/SimplyLogin/{username}")

        ESchoolUsername = Authentication.decryption(ESchoolUsernameEncrypted, User["ESchoolUsernameKey"])
        ESchoolPassword = Authentication.decryption(ESchoolPasswordEncrypted, User["ESchoolPasswordKey"])

        if not ESchoolUsername or not ESchoolPassword:
            return redirect(f"/SimplyLogin/{username}")

        CLASS_DETAILS_RESPONSE = UserTools.eschool_login(ESchoolUsername, ESchoolPassword,
                                                         quarter=quarter_selection)

        CLASS_DETAILS = UserTools.assignment_details(CLASS_DETAILS_RESPONSE["payload"])
        totalClasses = UserTools.class_count(CLASS_DETAILS["CLASSES"])

        letterColors = {
            "A": {
                "background": "#C0F2D8",
                "color": "#2BD47D"
            },
            "B": {
                "background": "#cce5ff",
                "color": "#66b0ff"
            },
            "C": {
                "background": "#ffe8b3",
                "color": "#ffc233"
            },
            "D": {
                "background": "#f7d4d7",
                "color": "#e05260"
            },
            "F": {
                "background": "#f7d4d7",
                "color": "#e05260"
            },
            "TBA": {
                "background": "#cce5ff",
                "color": "#66b0ff"
            }
        }
        gradesResponse = make_response(
            render_template('grades.html',
                            username=username,
                            site_data=Site().site_info(),
                            class_data=CLASS_DETAILS,
                            User=User,
                            gpa_data=Utils.gpa_calculator(CLASS_DETAILS),
                            quarter_selection=["ALL", "Q1", "Q2", "Q3", "Q4"],
                            selectedQuarter=selectedQuarter,
                            totalClasses=str(totalClasses),
                            letterColors=letterColors

                            )
        )
        print("Collected for...", quarter_selection)
        return gradesResponse

    # Not saved
    return redirect(f"/login")


# GPA

@app.route("/gpa/<username>", methods=["GET"])
def display_gpa(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]

    selectedQuarter = "ALL"
    submitQuarter = "ALL"
    if request.args.get("quarter"):
        submitQuarter = request.args.get("quarter")
        selectedQuarter = request.args.get("quarter")
    if selectedQuarter != "ALL":
        submitQuarter = submitQuarter[1] + "-2022"

    print("Collecting ESchool info with locally saved encrypted username and pass...")

    ESchoolUsernameEncrypted = request.cookies.get("ESecureLoginU")
    ESchoolPasswordEncrypted = request.cookies.get("ESecureLoginP")

    gpaResponse = make_response(
        render_template('gpa.html',
                        username=username,
                        site_data=Site().site_info(),
                        gpa_data=False,
                        User=User
                        )
    )

    if not ESchoolUsernameEncrypted or not ESchoolPasswordEncrypted or not User["ESchoolUsernameKey"] or not User[
        "ESchoolPasswordKey"]:
        return gpaResponse

    ESchoolUsername = Authentication.decryption(ESchoolUsernameEncrypted, User["ESchoolUsernameKey"])
    ESchoolPassword = Authentication.decryption(ESchoolPasswordEncrypted, User["ESchoolPasswordKey"])

    if not ESchoolUsername or not ESchoolPassword:
        return gpaResponse

    CLASS_DETAILS_RESPONSE = UserTools.eschool_login(ESchoolUsername, ESchoolPassword, quarter=submitQuarter)

    if CLASS_DETAILS_RESPONSE["message"] != 200:
        return gpaResponse

    gpa_data = Utils.gpa_calculator(CLASS_DETAILS_RESPONSE["payload"])

    gpaResponse = make_response(
        render_template('gpa.html',
                        username=username,
                        User=User,
                        gpa_data=gpa_data,
                        quarter_selection=["ALL", "Q1", "Q2", "Q3", "Q4"],
                        selectedQuarter=selectedQuarter,

                        )
    )

    return gpaResponse  # render_template("gpa.html", username=username)


@app.route("/gpa-details", methods=["GET"])
def display_vis_gpa():
    return render_template('gpa_details.html')


# SCHEDULE
@app.route("/schedule/<username>", methods=["GET"])
def display_schedule(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')
    refresh_schedule = request.args.get("refresh")

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    user_data = UserTools.all_user_data()
    User = user_data["users"][email]
    user_schedule = User["schedule"]
    site_info = Site()

    # Config schedule
    if not user_schedule or refresh_schedule:
        print("Collecting ESchool schedule with locally saved encrypted username and pass...")

        ESchoolUsernameEncrypted = request.cookies.get("ESecureLoginU")
        ESchoolPasswordEncrypted = request.cookies.get("ESecureLoginP")

        schedule_response = make_response(
            render_template('schedule.html',
                            username=username,
                            site_data=site_info.site_info(),
                            schedule=False,
                            User=User
                            )
        )

        if not ESchoolUsernameEncrypted or not ESchoolPasswordEncrypted or not User["ESchoolUsernameKey"] or not User[
            "ESchoolPasswordKey"]:
            return schedule_response

        ESchoolUsername = Authentication.decryption(ESchoolUsernameEncrypted, User["ESchoolUsernameKey"])
        ESchoolPassword = Authentication.decryption(ESchoolPasswordEncrypted, User["ESchoolPasswordKey"])

        if not ESchoolUsername or not ESchoolPassword:
            return schedule_response

        user_schedule = UserTools.eschool_schedule(ESchoolUsername, ESchoolPassword)
        if not user_schedule:
            return schedule_response

        # Save schedule
        print("Saving user schedule...")
        user_data["users"][email]["schedule"] = user_schedule
        Utils.writer(user_data, "databases/user_info.json")

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
    school_day = numpy.is_busday(datetime.now().strftime("%Y-%m-%d"), holidays=holidays)
    return render_template("schedule.html",
                           User=User,
                           username=username,
                           schedule=user_schedule,
                           quarter="Q" + site_info.schoolQuarter,
                           current_letter_day=Utils.get_letter_day(),
                           school_day=school_day
                           )


# COMMUNITY SERVICE

@app.route("/community_service/<username>", methods=["GET"])
def display_service(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]

    response = make_response(
        render_template("community_service.html",
                        username=username,
                        User=User,
                        )
    )

    return response


@app.route("/community_service/<username>", methods=["POST"])
def process_service(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    allData = UserTools.all_user_data()

    if "add-cs-item" in request.form:

        cs_organization = request.form.get("organization")
        cs_activity = request.form.get("activity")
        cs_date_started = request.form.get("date-started")
        cs_date_ended = request.form.get("date-ended")
        cs_hours = request.form.get("hours")
        cs_uuid = str(uuid.uuid1())

        if not cs_organization and not cs_activity and not cs_date_started and not cs_date_ended and not cs_hours:
            return redirect(f"/community_service/{username}")

        allData["users"][email]["community_service"].append(
            {
                "organization": cs_organization,
                "activity": cs_activity,
                "date_started": cs_date_started,
                "date_ended": cs_date_ended,
                "hours": cs_hours,
                "id": cs_uuid
            }
        )
        Utils.writer(allData, "databases/user_info.json")
        return redirect(f"/community_service/{username}")

    if "delete-cs-item" in request.form:
        delete_uuid = request.form["delete-cs-item"]
        item = 0
        for act in allData["users"][email]["community_service"]:
            if delete_uuid == act["id"]:
                del allData["users"][email]["community_service"][item]
                Utils.writer(allData, "databases/user_info.json")
            item += 1

    return redirect(f"/community_service/{username}")


# ABOUT

@app.route("/about/<username>", methods=["GET"])
def display_about(username):
    email = UserTools.username_to_email(username)
    User = UserTools.all_user_data()["users"][email]

    response = make_response(
        render_template("about.html",
                        username=username,
                        User=User,
                        )
    )

    return response


# SETTINGS

@app.route("/settings/<username>", methods=["GET"])
def display_settings(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    User = UserTools.all_user_data()["users"][email]

    return render_template("settings.html", username=username, settings=Utils.settings(),
                           User=User)


@app.route("/settings/<username>", methods=["POST"])
def process_settings(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    response = make_response(("", 204))

    # Account

    if request.form.get("Unlink ESchool account"):
        Settings.unlinkESchool(response=response, email=email)

    # Personalization

    if request.form.get("Profile picture URL"):
        UserData = UserTools.all_user_data()
        UserData["users"][email]["profilePicture"] = request.form.get("Profile picture URL")
        Utils.writer(data=UserData, filename="databases/user_info.json")

    # Account deletion

    if request.form.get("Delete account"):
        UserData = UserTools.all_user_data()

        del UserData["users"][email]
        Utils.writer(UserData, "databases/user_info.json")

        return redirect("/login")

    return response


# ESCHOOL LOGIN

@app.route("/SimplyLogin/<username>", methods=["GET"])
def display_eschool_login(username):
    email = UserTools.username_to_email(username)
    auth_token = request.cookies.get('auth_token')

    if not Authentication.valid_auth_token(email, auth_token):
        return redirect("/login")

    return render_template("eschool_login.html")


@app.route("/SimplyLogin/<username>", methods=["POST"])
def process_eschool_login(username):
    email = UserTools.username_to_email(username)

    eschool_username = request.form["username"]
    eschool_password = request.form["pass"]

    # print("processing eschool login...")
    # login = UserTools.eschool_login(eschool_username, eschool_password, quarter="ALL")
    #
    # if login["message"] != 200:
    #     return render_template("eschool_login.html", message=login["message"])

    response = make_response(redirect(f"/grades/{username}"))
    Authentication.set_secure_login_key(response, email, eschool_username, eschool_password, naviance=False)

    return response


@app.route("/logout", methods=["GET"])
def user_logout():
    response = make_response(redirect("/login"))
    response.delete_cookie("auth_token")
    return response


if __name__ == '__main__':
    app.run(debug=True)
