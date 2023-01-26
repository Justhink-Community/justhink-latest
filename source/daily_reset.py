import schedule 
import time 
import requests

TIMES_TO_BACKUP = [
    "00:00", "06:00", "09:00", "12:00", "15:00", "18:00"
]
TIME_TO_RESET = "18:00"
TIME_TO_ACTIVATE_SUNDAY = "10:00"


def daily_reset():
    response = requests.get(f"https://justhink.net/daily-reset/DAILY_RESET")

    print(f"Daily reset has been done succesfully: {response} - {response.status_code}")

def daily_backup():
    response = requests.get(f"https://justhink.net/daily-reset/DAILY_BACKUP")

    print(f"Daily backup has been done succesfully: {response} - {response.status_code}")

daily_backup()

for _time in TIMES_TO_BACKUP:
    schedule.every().day.at(_time).do(daily_backup)

schedule.every().monday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().tuesday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().wednesday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().thursday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().friday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().saturday.at(TIME_TO_RESET).do(daily_reset)
schedule.every().sunday.at(TIME_TO_ACTIVATE_SUNDAY).do(daily_reset)


print(f"Daily reset program has been started. It will reset at {TIME_TO_RESET}. (To terminate, press Ctrl + C)")

while 1:
    schedule.run_pending()
    time.sleep(1)