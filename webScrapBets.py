import json
import sqlite3
from urllib.request import urlopen

def setDB():
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS odds")
    cur.execute("""CREATE TABLE IF NOT EXISTS odds(n_id_odd INTEGER PRIMARY KEY AUTOINCREMENT, s_betOffice TEXT, s_betId TEXT, participant1 TEXT, participant2 TEXT,
    s_participantOrder TEXT, s_expirationDate TEXT, s_expirationTime TEXT, n_1 REAL, n_X REAL, n_2 REAL, n_1X REAL, n_12 REAL, n_X2 REAL, s_date_create TEXT)""")

def scrapNIKE():
    # f = open('Sport.json')
    # data = json.load(f)
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    # response = urlopen("https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&live=true&minutes&order&prematch=true&results=false")
    response = urlopen("https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&limit=100&live=true&minutes&order=10&prematch=true&results=false")
    data_json = json.loads(response.read())
    with open('nike.json', 'w') as f:
        f.write(json.dumps(data_json))
    dataDB = []
    for i in data_json['bets']:
        n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
        participant1 = participant2 = ""
        if len(i['participants']) > 0: participant1 = i['participants'][0]
        if len(i['participants']) > 1: participant2 = i['participants'][1]                   
        for j in i['selectionGrid']:
            for k in j:
                if 'odds' in k and k['row'] == 0 and k['col'] == 0:
                    n_1 = k['odds']
                if 'odds' in k and k['row'] == 0 and k['col'] == 1:
                    n_X = k['odds']
                if 'odds' in k and k['row'] == 0 and k['col'] == 2:
                    n_2 = k['odds']
                if 'odds' in k and k['row'] == 1 and k['col'] == 0:
                    n_1X = k['odds']
                if 'odds' in k and k['row'] == 1 and k['col'] == 1:
                    n_12 = k['odds']
                if 'odds' in k and k['row'] == 1 and k['col'] == 2:
                    n_X2 = k['odds']
        if not(n_1 is None and n_X is None and n_2 is None and n_1X is None and n_12 is None and n_X2 is None):            
            dataDB.append((i['betId'], participant1, participant2, i['participantOrder'], i['expirationTime'][0:10], i['expirationTime'][11:19], n_1, n_X, n_2, n_1X, n_12, n_X2))

    res = cur.executemany("""INSERT INTO odds(s_betOffice, s_betId, participant1, participant2, s_participantOrder, s_expirationDate, s_expirationTime, n_1, n_X, n_2, n_1X, n_12, n_X2, s_date_create)
                            VALUES ('NIKE', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""", dataDB)
    con.commit()

    print("NIKE - insert", res.rowcount, "counts")

    # f.close()


def scrapTIPSPORT():
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    import re

    driver = webdriver.Chrome('C:/Users/Administrator/AppData/Local/Programs/Python/Python310/chromedriver.exe')
    driver.get("https://www.tipsport.sk/kurzy/futbal-16") #  ?limit=325
    with open('tipsport.txt', 'w') as f:
        f.write(driver.page_source)
        listOdds = re.findall("<span data-m=\"(\d*)\">([^<]*)</span></span>.*?__dateClosed\"><span>(\d*.\d*.\d*)</span><span class=\"marL-leftS\">(\d*:\d*)<.*?\|\|1\">.*?(\d*.\d*)<.*?\|\|1x\">.*?(\d*.\d*)<.*?\|\|x\">.*?(\d*.\d*)<.*?\|\|x2\">.*?(\d*.\d*)<.*?\|\|2\">.*?(\d*.\d*)", driver.page_source)
        for i in listOdds:
            print(i)

    driver.quit()

    # "<span data-m=\"(\d*)\">([^<]*)</span></span>.*?__dateClosed\"><span>(\d*.\d*.\d*)</span><span class=\"marL-leftS\">(\d*:\d*)<.*?\|\|1\">.*?(\d*.\d*)<.*?\|\|1x\">.*?(\d*.\d*)<.*?\|\|x\">.*?(\d*.\d*)<.*?\|\|x2\">.*?(\d*.\d*)<.*?\|\|2\">.*?(\d*.\d*)"gm


if __name__ == '__main__':
    setDB()
    scrapNIKE()
    # scrapTIPSPORT()