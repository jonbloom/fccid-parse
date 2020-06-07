from bs4 import BeautifulSoup
import requests
from peewee import SqliteDatabase, Model, TextField, DateField
from dotenv import load_dotenv
import os
from time import sleep
from tqdm import tqdm

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
FCCID = os.getenv('FCCID')
URL = f"https://fccid.io/{FCCID}"


db = SqliteDatabase('./fcc.sqlite')


class FCCApplication(Model):
    id = TextField(primary_key=True)
    name = TextField()
    date = DateField()
    status = TextField()

    class Meta:
        database = db


def send_to_discord(which, old, new):
    payload = {
        "content": f"{which} | {new['name']} <@&655296026344816645>",
        "embeds": [{
            "title":  new['name'],
            "fields": [
                {
                    "name":  "Link",
                    "value": f"https://fccid.io/{new['fcc_id']}"
                },
                {
                    "name": "FCC ID",
                    "value": new['fcc_id']
                },
                {
                    "name": "Status",
                    "value": new['status']
                },
            ],
            "color": 2664261
        }]
    }
    if which == 'UPDATED':
        payload['embeds'][0]['fields'].append({
            "name": "Old Status",
            "value": old.status
        })
        payload['embeds'][0]['color'] = 31743
    payload['embeds'][0]['fields'].append({
        "name": "Date",
        "value": new['date']
    })

    webhook_req = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    sleep(1.5)
    rate_limited = (webhook_req.status_code == 429)
    if rate_limited:
        countdown = webhook_req.json()['retry_after']/1000 + 1
        while rate_limited:
            print(f'rate limited, waiting {countdown}s')
            sleep(countdown)
            webhook_req = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            rate_limited = (webhook_req.status_code == 429)
            if rate_limited:
                countdown = webhook_req.json()['retry_after']/1000 + 1


def save_to_db(application):
    new = True
    try:
        _application = FCCApplication.get(id=application['fcc_id'])
        new = False
        if _application.status != application['status']:
            send_to_discord('UPDATED', _application, application)

    except FCCApplication.DoesNotExist:
        _application = FCCApplication()
    _application.id = application['fcc_id']
    _application.name = application['name']
    _application.date = application['date']
    _application.status = application['status']
    _application.save(force_insert=new)

    if new:
        send_to_discord('NEW', None, application)


def get_applications():
    html = requests.get(URL).text
    soup = BeautifulSoup(html, features="html.parser")
    rows = soup.select('.panel-primary table tr')[1:]
    rows.reverse()
    applications = []
    for row in rows:
        cells = row.select('td')
        fcc_id = cells[0].contents[0].text
        date = cells[0].contents[2]
        name = cells[1].contents[0]
        status = cells[1].contents[2]

        applications.append({
            "fcc_id": fcc_id,
            "date": date,
            "name": name,
            "status": status
        })
    return applications


def main():
    for application in tqdm(get_applications()):
        save_to_db(application)


if __name__ == "__main__":
    db.create_tables([FCCApplication], safe=True)
    main()
