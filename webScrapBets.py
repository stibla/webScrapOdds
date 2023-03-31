import json
import sqlite3
import re
from selenium import webdriver
from datetime import datetime
from urllib.request import Request, urlopen

def setDB(dropTable = False, createTable = False, deleteAllRows = False):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    if dropTable: 
        cur.execute("DROP TABLE IF EXISTS odds")
        cur.execute("DROP TABLE IF EXISTS e_participants")
    if createTable: 
        cur.execute("""CREATE TABLE IF NOT EXISTS odds(
                    n_id_odd INTEGER PRIMARY KEY AUTOINCREMENT, 
                    s_betOffice TEXT, 
                    s_betId TEXT, 
                    s_participant1 TEXT, 
                    s_participant2 TEXT,
                    s_participantOrder TEXT, 
                    s_expirationDate TEXT, 
                    s_expirationTime TEXT, 
                    n_1 REAL, 
                    n_X REAL, 
                    n_2 REAL, 
                    n_1X REAL, 
                    n_12 REAL, 
                    n_X2 REAL, 
                    s_date_create TEXT)""")
        cur.execute("DROP TABLE IF EXISTS e_participants")
        cur.execute("""CREATE TABLE IF NOT EXISTS e_participants (
                    n_id_participants INTEGER PRIMARY KEY AUTOINCREMENT,
                    s_old_name TEXT,
                    s_new_name TEXT, 
                    s_date_create TEXT)""")
    if deleteAllRows: cur.execute("DELETE FROM odds")
    con.commit()

def setParticipantEinDB():
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    res = cur.execute("""INSERT INTO e_participants(s_old_name, s_new_name, s_date_create) 
            SELECT s_participant1, s_participant1, datetime('now', 'localtime') FROM (select s_participant1 FROM odds where s_participant1 not in (select s_old_name from e_participants)
            union all select s_participant2 FROM odds where s_participant2 not in (select s_old_name from e_participants)) GROUP BY s_participant1""")
    con.commit()
    print("Inserted", res.rowcount, "new participants")

def saveToDB(dataDB, betOffice):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    idToDelete = []
    for id in dataDB:
        idToDelete.append(id[0])
    res = cur.execute("delete from odds where s_betId in ('" + "', '".join(idToDelete) + "')")
    con.commit()
    print(betOffice + " - deleted", res.rowcount, "counts")

    res = cur.executemany("""INSERT INTO odds(s_betOffice, s_betId, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, n_1, n_X, n_2, n_1X, n_12, n_X2, s_date_create)
                            VALUES ('""" + betOffice + """', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""", dataDB)
    con.commit()
    print(betOffice + " - insert", res.rowcount, "counts")

def scrapNIKE():
    hasMoreBets = True
    urlString = "https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&live=true&menu=%2Ffutbal&minutes&order&prematch=true&results=false"
    while hasMoreBets:
        response = urlopen(urlString)
        data_json = json.loads(response.read())
        # with open('nike.json', 'w') as f:
        #     f.write(json.dumps(data_json))
        dataDB = []
        for i in data_json['bets']:
            n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
            participant1 = participant2 = ""
            if len(i['participants']) > 1:
                participant1 = i['participants'][0]
                participant2 = i['participants'][1]
                for j in i['selectionGrid']:
                    for k in j:
                        if 'odds' in k and k['row'] == 0 and k['col'] == 0: n_1 = k['odds']
                        if 'odds' in k and k['row'] == 0 and k['col'] == 1: n_X = k['odds']
                        if 'odds' in k and k['row'] == 0 and k['col'] == 2: n_2 = k['odds']
                        if 'odds' in k and k['row'] == 1 and k['col'] == 0: n_1X = k['odds']
                        if 'odds' in k and k['row'] == 1 and k['col'] == 1: n_12 = k['odds']
                        if 'odds' in k and k['row'] == 1 and k['col'] == 2: n_X2 = k['odds']
                if not(n_1 is None and n_X is None and n_2 is None and n_1X is None and n_12 is None and n_X2 is None):
                    dataDB.append((i['betId'], participant1, participant2, i['participantOrder'], i['expirationTime'][0:10], i['expirationTime'][11:16], n_1, n_X, n_2, n_1X, n_12, n_X2))
        saveToDB(dataDB, "NIKE")
        hasMoreBets = False
        if data_json['hasMoreBets']:
            hasMoreBets = True
            urlString = "https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&limit=50&menu=%2Ffutbal&live=true&minutes&order="+str(int(data_json['maxBoxOrder']))+"&prematch=true&results=false"


def scrapTIPSPORT():
    dataDB = []
    driver = webdriver.Chrome('C:/Users/Administrator/AppData/Local/Programs/Python/Python310/chromedriver.exe')
    driver.get("https://www.tipsport.sk/kurzy/futbal-16?limit=825") #  ?limit=325
    # with open('tipsport.html', 'w') as f:
    #     f.write(driver.page_source)
    listMatch = re.findall("(<div class=\"o-matchRow\".*?<div class=\"o-matchRow__results\"></div></div>)", driver.page_source)
    for i in listMatch:
        match = re.findall("<span data-m=\"(\d+)\">([^<]*)</span></span>.*?__dateClosed\"><span>(\d+.\d+.\d+)</span><span class=\"marL-leftS\">(\d+:\d+)", i)
        odds = re.findall(".*?\|\|(1|1x|x|x2|2)\">.*?(?:(\d+\.\d+)|setPassive)", i)
        if len(odds) > 0 and len(match[0][1].split(" - ", 1)) > 1:
            n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
            for j in odds:
                if j[0] == '1': n_1 = j[1]
                if j[0] == '1x': n_1X = j[1]
                if j[0] == 'x': n_X = j[1]
                if j[0] == 'x2': n_X2 = j[1]
                if j[0] == '2': n_2 = j[1]
            dataDB.append((match[0][0], match[0][1].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][1].split(" - ", 1)[1]), match[0][1], datetime.strftime(datetime.strptime(match[0][2],"%d.%m.%Y"),"%Y-%m-%d"), match[0][3], n_1, n_X, n_2, n_1X, n_12, n_X2))
    saveToDB(dataDB, "TIPSPORT")
    driver.quit()

def scrapFORTUNA():
    for page in range(10):
        dataDB = []
        req = Request(url='https://www.ifortuna.sk/bets/ajax/loadmoresport/futbal?timeTo=&rateFrom=&rateTo=&date=&pageSize=100&page='+str(page), headers={'User-Agent': 'Mozilla/5.0'})
        data_html = urlopen(req).read()
        # with open('fortuna.html', 'w') as f:
        #     f.write(re.sub("\n", "", data_html.decode()))
        noWhitespace = re.sub("\n", "", data_html.decode())
        sections = re.findall("(<section.*?</section>)", noWhitespace)
        for s in sections:
            headers = re.findall("<span class=\"odds-name\"> *(\S*) *?</span>", s)
            controlHeaders = ['1', '0', '2', '10', '02', '12']
            if any(x in headers for x in controlHeaders):
                listMatch = re.findall("<tr class=\"\">.*?</tr>", s)                
                for m in listMatch:
                    match = re.findall("<tr class=\"\">.*?<span class=\"market-name\">(.*?)</span>.*?<span class=\"event-info-number\">(\d*?)</span>.*?<span class=\"event-datetime\">(\d\d\.\d\d\. \d\d:\d\d)</span>", m)
                    odds = re.findall("<td class=\"col-odds\">.*?<span class=\"odds-value\">(-?\d+.\d+)</span>.*?</td>", m)
                    if len(odds) > 0 and len(match[0][0].split(" - ", 1)) > 1:
                        n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
                        for o, h in zip(odds, headers):
                            if h == '1': n_1 = o
                            if h == '10': n_1X = o
                            if h == '0': n_X = o
                            if h == '02': n_X2 = o
                            if h == '2': n_2 = o
                            if h == '12': n_12 = o
                        dataDB.append((match[0][1], match[0][0].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][0].split(" - ", 1)[1]), match[0][0], datetime.strftime(datetime.strptime(match[0][2][0:6] + datetime.strftime(datetime.now(),"%Y"),"%d.%m.%Y"),"%Y-%m-%d"), match[0][2][7:12], n_1, n_X, n_2, n_1X, n_12, n_X2))
        saveToDB(dataDB, "FORTUNA")

if __name__ == '__main__':
    # setDB(True, True, False)
    scrapNIKE()
    # scrapTIPSPORT()
    # scrapFORTUNA()
    setParticipantEinDB()