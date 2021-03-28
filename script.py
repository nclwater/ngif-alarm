import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass
from pymongo import MongoClient, DESCENDING
import os
import pandas as pd
from datetime import timedelta
from time import sleep

mongo_uri = os.getenv('MONGO_URI', 'mongodb://test:password@localhost:27017/test?authSource=admin')
username = os.getenv('EMAIL_USERNAME')
password = os.getenv('EMAIL_PASSWORD', getpass())
interval = os.getenv('INTERVAL')  # minutes

db = MongoClient(mongo_uri).get_database()
readings = db.readings
sensors = db.sensors

last_alarm = {}

number_of_readings = 100
threshold = 0  # mm
period = 15  # minutes


def check_rain():
    name = 'GP2-10-60 (Ensemble E + RG)'
    field = 'Pit Rain Gauge#@1m'
    # Get the last n readings
    df = pd.DataFrame(
        list(readings.find(
            {
                'name': name,
                field: {"$exists": True},
            },
            {field: 1, 'time': 1, '_id': 0}, sort=[('_id', DESCENDING)]).limit(number_of_readings)))

    if len(df) == 0:
        return

    # Convert tips to mm
    df[field] = df[field] * 0.198

    rolling = df.set_index('time')[field].rolling(f'{period}min').sum()
    rolling = rolling[rolling >= threshold]

    if len(rolling) >= 0:
        time = rolling.index.max()
        key = f'{name}/{field}'
        if key not in last_alarm.keys() or time != last_alarm[key]:
            last_alarm[key] = time
            send_email(username, 'Ensemble E Rainfall',
                       df[(df.time <= time) & (df.time >= time-timedelta(minutes=15))].to_html(index=False))


def check_power():
    # Get all elements with power readings from the last 6 hours
    df = pd.DataFrame(
        list(readings.find(
            {
                'time': {'$gt': pd.Timestamp.now() - pd.Timedelta(hours=6)},
                'Power': {'$exists': True},
            },
            {'name': 1, 'Power': 1, 'time': 1, '_id': 0})))
    if len(df) == 0:
        return

    rolling = df.set_index('time').groupby('name')['Power'].rolling(10).sum()
    rolling = rolling[rolling > 0].reset_index().groupby('name').time.max()

    message = 'The following loggers recorded ten consecutive zero power readings:<br><br>'
    send = False

    if len(rolling) >= 0:
        for name, time in rolling.items():
            if name not in last_alarm.keys() or time != last_alarm[name]:
                send = True
                last_alarm[name] = time
                message += f'{name} at {time}<br>'
        if send:
            send_email(username, 'Power warning', message)


def send_email(email_recipient,
               email_subject,
               email_message):

    email_sender = username

    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = email_subject

    msg.attach(MIMEText(email_message, 'html'))

    server = smtplib.SMTP('smtp.office365.com', 587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    text = msg.as_string()
    server.sendmail(email_sender, email_recipient, text)
    server.quit()


def check_rain_and_power_periodically():
    while True:
        check_rain()
        check_power()
        if interval is None:
            break
        sleep(int(interval) * 60)


if __name__ == '__main__':
    check_rain_and_power_periodically()
