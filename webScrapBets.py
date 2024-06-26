import json
import sqlite3
import re
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
import time

def setDB(dropTables = False, createTables = False, deleteAllRowsOdds = False):
    con = sqlite3.connect("data.db")
    if dropTables:
        con.execute("DROP TABLE IF EXISTS odds")

    if createTables:
        con.execute("""CREATE TABLE IF NOT EXISTS odds(
                    n_id_odd INTEGER PRIMARY KEY AUTOINCREMENT,
                    s_betOffice TEXT,
                    s_betId TEXT,
                    s_participant1 TEXT,
                    s_participant2 TEXT,
                    s_participantOrder TEXT,
                    s_participantOrderMatch TEXT,
                    n_matchRatio REAL,
                    n_matchRatio1 REAL,
                    n_matchRatio2 REAL,
                    s_expirationDate TEXT,
                    s_expirationTime TEXT,
                    n_1 REAL,
                    n_X REAL,
                    n_2 REAL,
                    n_1X REAL,
                    n_12 REAL,
                    n_X2 REAL,
                    s_date_create TEXT)""")
        
    if deleteAllRowsOdds: 
        con.execute("DELETE FROM odds")
    con.commit()
    con.close()

def saveToDB(dataDB, betOffice):
    con = sqlite3.connect("data.db")
    idToDelete = []
    for id in dataDB:
        idToDelete.append(id[0])
    res = con.execute("delete from odds where s_betId in ('" + "', '".join(idToDelete) + "')")
    con.commit()
    print(betOffice + " - deleted", res.rowcount, "counts")

    res = con.executemany("""INSERT INTO odds(s_betOffice, s_betId, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, n_1, n_X, n_2, n_1X, n_12, n_X2, s_date_create)
                            VALUES ('""" + betOffice + """', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""", dataDB)
    con.commit()
    noOfrowCount = res.rowcount
    print(betOffice + " - inserted", noOfrowCount, "counts")    
    con.close()
    return noOfrowCount

def scrapNIKE():
    sports = ("futbal",
            "hokej",
            # "tenis",
            "basketbal")
    for sport in sports:
        hasMoreBets = True

        urlString = "https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&live=true&menu=%2F" + sport + "&minutes&order&prematch=true&results=false"
        while hasMoreBets:
            response = urlopen(urlString)
            data_json = json.loads(response.read())
            # with open('nike.json', 'w') as f:
            #     f.write(json.dumps(data_json))
            dataDB = []
            for b in data_json['bets']:
                n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
                participant1 = participant2 = ""
                if len(b['participants']) > 1:
                    participant1 = b['participants'][0]
                    participant2 = b['participants'][1]
                    for j in b['selectionGrid']:
                        for k in j:
                            if 'odds' in k and k['odds'] > 1:
                                if k['name'] == participant1: n_1 = k['odds']
                                if k['name'] == "remíza": n_X = k['odds']
                                if k['name'] == participant2: n_2 = k['odds']
                                if k['name'] == "1X": n_1X = k['odds']
                                if k['name'] == "12": n_12 = k['odds']
                                if k['name'] == "X2": n_X2 = k['odds']
                    # if not(n_1 is None and n_X is None and n_2 is None and n_1X is None and n_12 is None and n_X2 is None):
                    dataDB.append((b['betId'], participant1, participant2, b['participantOrder'], b['expirationTime'][0:10], b['expirationTime'][11:16], n_1, n_X, n_2, n_1X, n_12, n_X2))
            saveToDB(dataDB, "NIKE")
            hasMoreBets = False
            if data_json['hasMoreBets']:
                hasMoreBets = True
                urlString = "https://api.nike.sk/api/nikeone/v1/boxes/search/portal?betNumbers&date&limit=50&live=true&menu=%2F" + sport + "&minutes&order="+str(int(data_json['maxBoxOrder']))+"&prematch=true&results=false"

def scrapTIPSPORT():
    urls = ("https://www.tipsport.sk/kurzy/futbal-16?limit=825",
            "https://www.tipsport.sk/kurzy/hokej-23?limit=825",
           # "https://www.tipsport.sk/kurzy/tenis-43?limit=825",
            "https://www.tipsport.sk/kurzy/basketbal-7")
    options = ChromeOptions()
    driver = webdriver.Chrome(options=options)     # driver = webdriver.Chrome('C:/Users/Administrator/AppData/Local/Programs/Python/Python310/chromedriver.exe')
    for url in urls:
        dataDB = []        
        driver.get(url) #  ?limit=325

        # with open('tipsport.html', 'w', encoding="utf-8") as f:
        #     f.write(driver.page_source)      
        # f = open("tipsport.html", "r", encoding="utf8")
        # listMatch = re.findall("(<div class=\"o-matchRow\".*?<div class=\"o-matchRow__results\"></div></div>)", f.read())

        listMatch = re.findall("(<div class=\"o-matchRow\".*?<div class=\"o-matchRow__results\"></div></div>)", driver.page_source)
        for i in listMatch:
            match = re.findall("<span data-m=\"(\d+)\">([^<]*)</span></span>.*?__dateClosed\"><span>(Zajtra|Dnes|\d+. ?\d+. ?\d+) \| (\d+:\d+)", i)
            odds = re.findall(".*?\|\|(1|1x|x|x2|2)\".*?(?:(\d+\.\d+)|setPassive)", i)
            if len(odds) > 0 and len(match[0][1].split(" - ", 1)) > 1:
                n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = expirationdate = None
                for j in odds:
                    if j[0] == '1' and j[1] != '' and float(j[1]) > 1: n_1 = j[1]
                    if j[0] == '1x' and j[1] != '' and float(j[1]) > 1: n_1X = j[1]
                    if j[0] == 'x' and j[1] != '' and float(j[1]) > 1: n_X = j[1]
                    if j[0] == 'x2' and j[1] != '' and float(j[1]) > 1: n_X2 = j[1]
                    if j[0] == '2' and j[1] != '' and float(j[1]) > 1: n_2 = j[1]
                if match[0][2] == "Dnes":
                    expirationdate = datetime.strftime(datetime.today(),"%Y-%m-%d")
                elif match[0][2] == "Zajtra":
                    expirationdate = datetime.strftime(datetime.today() + timedelta(days=1),"%Y-%m-%d")
                else:
                    expirationdate = datetime.strftime(datetime.strptime(re.sub(" ","", match[0][2]),"%d.%m.%Y"),"%Y-%m-%d")
                dataDB.append((match[0][0], match[0][1].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][1].split(" - ", 1)[1]), match[0][1], expirationdate, match[0][3], n_1, n_X, n_2, n_1X, n_12, n_X2))
        saveToDB(dataDB, "TIPSPORT")
    driver.quit()

def scrapFORTUNA():
    urls = ("https://www.ifortuna.sk/bets/ajax/loadmoresport/futbal?timeTo=&rateFrom=&rateTo=&date=&pageSize=100&page=",
            "https://www.ifortuna.sk/bets/ajax/loadmoresport/hokej?timeTo=&rateFrom=&rateTo=&date=&pageSize=100&page=",
          #  "https://www.ifortuna.sk/bets/ajax/loadmoresport/tenis?timeTo=&rateFrom=&rateTo=&date=&pageSize=100&page=",
            "https://www.ifortuna.sk/bets/ajax/loadmoresport/basketbal?timeTo=&rateFrom=&rateTo=&date=&pageSize=100&page=")
    for urlTMP in urls:
        for page in range(30):
            dataDB = []
            req = Request(url=urlTMP+str(page), headers={'User-Agent': 'Mozilla/5.0'})
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
                                if h == '1' and o != '' and float(o) > 1: n_1 = o
                                if h == '10' and o != '' and float(o) > 1: n_1X = o
                                if h == '0' and o != '' and float(o) > 1: n_X = o
                                if h == '02' and o != '' and float(o) > 1: n_X2 = o
                                if h == '2' and o != '' and float(o) > 1: n_2 = o
                                if h == '12' and o != '' and float(o) > 1: n_12 = o
                            dataDB.append((match[0][1], match[0][0].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][0].split(" - ", 1)[1]), match[0][0], datetime.strftime(datetime.strptime(match[0][2][0:6] + datetime.strftime(datetime.now(),"%Y"),"%d.%m.%Y"),"%Y-%m-%d"), match[0][2][7:12], n_1, n_X, n_2, n_1X, n_12, n_X2))
            retVal = saveToDB(dataDB, "FORTUNA")
            if retVal == 0: break

def scrapDOXXBET():
    req = Request(url="https://www.doxxbet.sk/offer/GetOfferList", method='POST')
    data_json = json.loads(urlopen(req).read())
    
    # with open('doxxbet.json', 'w') as f:
    #     f.write(json.dumps(data_json)) 
    # data_json = json.load(open('doxxbet.json', errors='ignore'))

    dataDB = []
    # futbal 54,1  hokej 53, 4     basketbal 50, 2,   tenis 58, 5
    for e in data_json['EventChanceTypes']:
        n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
        if e['EventChanceTypeID'] != 0 and e['LiveBettingView'] != -1 and len(e['EventName'].split(" vs. ", 1)) > 1 and (e['BetradarSportID'] == 1 or e['BetradarSportID'] == 2 or e['BetradarSportID'] == 4): # or e['BetradarSportID'] == 5):
            if str(e['EventChanceTypeID']) + '_1' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_1']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_1']['OddsRate'] > 1: n_1 = data_json['Odds'][str(e['EventChanceTypeID']) + '_1']['OddsRate']
            if str(e['EventChanceTypeID']) + '_X' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_X']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_X']['OddsRate'] > 1: n_X = data_json['Odds'][str(e['EventChanceTypeID']) + '_X']['OddsRate']
            if str(e['EventChanceTypeID']) + '_2' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_2']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_2']['OddsRate'] > 1: n_2 = data_json['Odds'][str(e['EventChanceTypeID']) + '_2']['OddsRate']
            if str(e['EventChanceTypeID']) + '_1X' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_1X']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_1X']['OddsRate'] > 1: n_1X = data_json['Odds'][str(e['EventChanceTypeID']) + '_1X']['OddsRate']
            if str(e['EventChanceTypeID']) + '_X2' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_X2']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_X2']['OddsRate'] > 1: n_X2 = data_json['Odds'][str(e['EventChanceTypeID']) + '_X2']['OddsRate']
            if str(e['EventChanceTypeID']) + '_12' in data_json['Odds'] and 'OddsRate' in data_json['Odds'][str(e['EventChanceTypeID']) + '_12']: 
                if data_json['Odds'][str(e['EventChanceTypeID']) + '_12']['OddsRate'] > 1: n_12 = data_json['Odds'][str(e['EventChanceTypeID']) + '_12']['OddsRate']
            dataDB.append((str(e['EventChanceTypeID']), re.sub(" \(.*\)", "", e['EventName'].split(" vs. ", 1)[0]), re.sub(" \(.*\)", "", e['EventName'].split(" vs. ", 1)[1]), re.sub(" vs. "," - ", e['EventName']) , e['EventDate'][0:10], e['EventDate'][11:16], n_1, n_X, n_2, n_1X, n_12, n_X2))   
            
    saveToDB(dataDB, "DOXXBET")

def scrapTIPOS():
    urls = ("https://tipkurz.etipos.sk/zapasy/28?categoryId=28",
            "https://tipkurz.etipos.sk/zapasy/31?categoryId=31",
           # "https://tipkurz.etipos.sk/zapasy/2?categoryId=2",
            "https://tipkurz.etipos.sk/zapasy/5?categoryId=5")
    options = ChromeOptions()
    driver = webdriver.Chrome(options=options)
    for url in urls:
        driver.get(url) #  ?limit=325
        element = driver.find_element(By.ID, "reactFooterWrapper")
        for i in range(10):
            ActionChains(driver).scroll_to_element(element).perform()
            time.sleep(5)
        
        # with open('tipos.html', 'w', encoding="utf-8") as f:
        #     f.write(driver.page_source)        
        # f = open("tipos.html", "r", encoding="utf8")
        # listMatch = re.findall("(<div data-test-role=\"event-list__item\".*?(?=<div data-test-role=\"event-list__item))", f.read())
        
        listMatch = re.findall("(<div data-test-role=\"event-list__item\".*?(?=<div data-test-role=\"event-list__item))", driver.page_source)
        dataDB = [] 
        for lm in listMatch:
            match = re.findall("event-list__item__detail-link\">([^<]*)</div>.*?<span id=\"eventicon_(\d*).*?v-center date-col pt-3\">(\d+.\d+.\d+)<br>(\d+:\d+)</div>", lm)
            odds = re.findall("class=\"rate-label text-truncate\">(.*?)</div><div class=\"rate d-flex align-items-center justify-content-center\">(\d+\,\d+)</div>", lm)
            if len(odds) > 0 and len(match[0][0].split(" - ", 1)) > 1:
                n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
                for o in odds:
                    if o[0] == match[0][0].split(" - ", 1)[0]: n_1 = re.sub(",", ".", o[1])
                    if o[0] == "Remíza": n_X = re.sub(",", ".", o[1])
                    if o[0] == match[0][0].split(" - ", 1)[1]: n_2 = re.sub(",", ".", o[1])
                # if not(n_1 is None and n_X is None and n_2 is None):
                dataDB.append((match[0][1], match[0][0].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][0].split(" - ", 1)[1]), match[0][0], datetime.strftime(datetime.strptime(match[0][2],"%d.%m.%y"),"%Y-%m-%d"), match[0][3], n_1, n_X, n_2, n_1X, n_12, n_X2))
        saveToDB(dataDB, "TIPOS")

def scrapSYNNOTTIP():
    urls = ("https://sport.synottip.sk/zapasy/28?categoryId=28",
            "https://sport.synottip.sk/zapasy/31?categoryId=31",
          #  "https://sport.synottip.sk/zapasy/2?categoryId=2",
            "https://sport.synottip.sk/zapasy/5?categoryId=5")
    options = ChromeOptions()
    driver = webdriver.Chrome(options=options)
    for url in urls:
        driver.get(url) #  ?limit=325
        try:
            element = driver.find_element(By.ID, "reactFooterWrapper")
            for i in range(10):                
                ActionChains(driver).scroll_to_element(element).perform()                        
                time.sleep(5)
        except:
            print("An exception occurred scrapSYNNOTTIP")   
        
        # with open('synottip.html', 'w', encoding="utf-8") as f:
        #     f.write(driver.page_source)

        listMatch = re.findall("(<div data-test-role=\"event-list__item\".*?(?=<div data-test-role=\"event-list__item))", driver.page_source)
        
        # f = open("synottip.html", "r", encoding="utf8")
        # listMatch = re.findall("(<div data-test-role=\"event-list__item\".*?(?=<div data-test-role=\"event-list__item))", f.read())

        dataDB = [] 
        for lm in listMatch:
            match = re.findall("event-list__item__detail-link\">([^<]*)</div>.*?<span id=\"eventicon_(\d*).*?v-center date-col pt-3\">(\d+.\d+.\d+)<br>(\d+:\d+)</div>", lm)
            odds = re.findall("class=\"rate-label text-truncate\">(.*?)</div><div class=\"rate d-flex align-items-center justify-content-center\">(\d+\,\d+)</div>", lm)
            if len(odds) > 0 and len(match[0][0].split(" - ", 1)) > 1:
                n_1 = n_X = n_2 = n_1X = n_12 = n_X2 = None
                for o in odds:
                    if o[0] == match[0][0].split(" - ", 1)[0]: n_1 = re.sub(",", ".", o[1])
                    if o[0] == "Remíza": n_X = re.sub(",", ".", o[1])
                    if o[0] == match[0][0].split(" - ", 1)[1]: n_2 = re.sub(",", ".", o[1])
                # if not(n_1 is None and n_X is None and n_2 is None):
                dataDB.append((match[0][1], match[0][0].split(" - ", 1)[0], re.sub(" \(.*\)", "", match[0][0].split(" - ", 1)[1]), match[0][0], datetime.strftime(datetime.strptime(match[0][2],"%d.%m.%y"),"%Y-%m-%d"), match[0][3], n_1, n_X, n_2, n_1X, n_12, n_X2))
        saveToDB(dataDB, "SYNNOTTIP")

def setBindings():
    from difflib import SequenceMatcher
    con = sqlite3.connect("data.db")

    con.execute("""UPDATE odds
                SET s_participantOrderMatch = NULL""");
    con.commit()

    cur = con.execute("""SELECT odds_1.s_betOffice s_betOffice1, odds_1.n_id_odd n_id_odd1, odds_1.s_participantOrder s_participantOrder1, odds_1.s_participant1 participant11, odds_1.s_participant2 participant21 
        , odds_2.s_betOffice s_betOffice2, odds_2.n_id_odd n_id_odd2, odds_2.s_participantOrder s_participantOrder2, odds_2.s_participant1 participant12, odds_2.s_participant2 participant22
        FROM odds As odds_1,  odds As odds_2
        WHERE odds_2.s_expirationDate = odds_1.s_expirationDate and odds_2.s_expirationTime = odds_1.s_expirationTime 
        and odds_1.s_betOffice <> odds_2.s_betOffice""")
    dataDB = []
    for row in cur:
        ratio = SequenceMatcher(None, deletePrefixSufix(row[2]), deletePrefixSufix(row[7])).ratio()
        ratio1 = SequenceMatcher(None, deletePrefixSufix(row[3]), deletePrefixSufix(row[8])).ratio()
        ratio2 = SequenceMatcher(None, deletePrefixSufix(row[4]), deletePrefixSufix(row[9])).ratio()
        if (ratio > 0.5 and ratio1 > 0.5 and ratio2 > 0.5):  # or ratio1 == 1.0 or ratio2 == 1.0:
            if (row[6], row[1], ratio) not in dataDB: 
                dataDB.append((row[1], row[6], ratio)) 
                con.execute("""UPDATE odds
                    SET s_participantOrderMatch = ?,
                    n_matchRatio = ?,
                    n_matchRatio1 = ?,
                    n_matchRatio2 = ?
                    where odds.n_id_odd = ?
                    and odds.s_participantOrderMatch Is Null""", (row[2], ratio, ratio1, ratio2, row[6]))
                con.execute("""UPDATE odds
                    SET s_participantOrderMatch = ?,
                    n_matchRatio = ?,
                    n_matchRatio1 = ?,
                    n_matchRatio2 = ?
                    where odds.n_id_odd = ?
                    and odds.s_participantOrderMatch Is Null""", (row[2], ratio, ratio1, ratio2, row[1]))
                con.commit()    

    con.close()

def findBets():
    con = sqlite3.connect("data.db")

    cur = con.execute("""SELECT s_betOffice, COUNT(1)
        FROM odds
        GROUP BY s_betOffice""")
    print("No of odds:")
    for row in cur:
        print(row)
    
    cur = con.execute("""SELECT POCET, COUNT(1) POCTY FROM (
        SELECT odds.s_participantOrderMatch, odds.s_expirationDate, odds.s_expirationTime, COUNT(1) POCET
        FROM odds
		WHERE odds.s_participantOrderMatch Is Not NULL
        GROUP BY odds.s_participantOrderMatch, odds.s_expirationDate, odds.s_expirationTime
        ) GROUP BY POCET""")
    print("No of mergers:")
    for row in cur:
        print(row)

    cur = con.execute("""SELECT chngOdds.s_betOffice, chngOdds.s_participantOrder, chngOdds.s_participantOrderMatch, chngOdds.s_expirationDate, chngOdds.s_expirationTime, BestOdds.DiffToNow
		, BestOdds.koef_1_X2
		, CASE WHEN BestOdds.koef_1_X2 < 100 and BestOdds.max_1 = chngOdds.n_1 then "1_X2 - 1:" || chngOdds.n_1 || ";" else "" end 
		|| CASE WHEN BestOdds.koef_1_X2 < 100 and BestOdds.max_X2 = chngOdds.n_X2 then "1_X2 - X2:" || chngOdds.n_X2 || ";" else "" end 
		AS bet_1_X2
		, BestOdds.koef_2_1X
	    , CASE WHEN BestOdds.koef_2_1X < 100 and BestOdds.max_2 = chngOdds.n_2 then "2_1X - 2:" || chngOdds.n_2 || ";" else "" end 
		|| CASE WHEN BestOdds.koef_2_1X < 100 and BestOdds.max_X2 = chngOdds.n_X2 then "2_1X - 1X:" || chngOdds.n_1X || ";" else "" end 
		AS bet_2_1X
		, BestOdds.koef_X_12
	    , CASE WHEN BestOdds.koef_X_12 < 100 and BestOdds.max_X = chngOdds.n_X then "X_12 - X:" || chngOdds.n_X || ";" else "" end 
		|| CASE WHEN BestOdds.koef_X_12 < 100 and BestOdds.max_12 = chngOdds.n_12 then "X_12 - 12:" || chngOdds.n_12 || ";" else "" end 
		AS bet_X_12	
		, BestOdds.koef_1_X_2
		, CASE WHEN BestOdds.koef_1_X_2 < 100 and BestOdds.max_1 = chngOdds.n_1 then "1_X_2 - 1:" || chngOdds.n_1 || ";" else "" end 
		|| CASE WHEN BestOdds.koef_1_X_2 < 100 and BestOdds.max_X = chngOdds.n_X then "1_X_2 - X:" || chngOdds.n_X || ";" else "" end 
		|| CASE WHEN BestOdds.koef_1_X_2 < 100 and BestOdds.max_2 = chngOdds.n_2 then "1_X_2 - 2:" || chngOdds.n_2 || ";" else "" end 
		AS bet_1_X_2	
		, BestOdds.koef_1_2
		, CASE WHEN BestOdds.koef_1_2 < 100 and BestOdds.max_1 = chngOdds.n_1 then "1_2 - 1:" || chngOdds.n_1 || ";" else "" end 
		|| CASE WHEN BestOdds.koef_1_2 < 100 and BestOdds.max_2 = chngOdds.n_2 then "1_2 - 2:" || chngOdds.n_2 || ";" else "" end 
		AS bet_1_2
		--, BestOdds.*
		--, chngOdds.* 
		from
        (SELECT * FROM (SELECT s_participantOrderMatch, s_expirationDate, s_expirationTime,  
			   JULIANDAY(datetime(s_expirationDate || ' ' || s_expirationTime)) - JULIANDAY(datetime('now','localtime')) DiffToNow, COUNT(1), 
                max(n_1) as max_1, max(n_X) as max_X, max(n_2) as max_2, max(n_1X) as max_1X, max(n_12) as max_12, max(n_X2) as max_X2,
                case when COUNT(1) > 1 and max(n_1) is not null and max(n_X2) is not null then 100/max(n_1) + 100/max(n_X2) end as koef_1_X2,
                case when COUNT(1) > 1 and max(n_2) is not null and max(n_1X) is not null then 100/max(n_2) + 100/max(n_1X) end as koef_2_1X,
                case when COUNT(1) > 1 and max(n_X) is not null and max(n_12) is not null then 100/max(n_X) + 100/max(n_12) end as koef_X_12,
                case when COUNT(1) > 1 and max(n_1) is not null and max(n_X) is not null and max(n_2) is not null then 100/max(n_1) + 100/max(n_X) + 100/max(n_2) end as koef_1_X_2,
				case when COUNT(1) > 1 and max(n_1) is not null and max(n_X) is null and max(n_2) is not null then 100/max(n_1) + 100/max(n_2) end as koef_1_2
                FROM (SELECT s_betOffice, s_participantOrderMatch, s_expirationDate, s_expirationTime, min(n_1) n_1,
					min(n_X) n_X, min(n_2) n_2, min(n_1X) n_1X, min(n_12) n_12, min(n_X2) n_X2
					FROM odds GROUP BY s_betOffice, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime) min_odds
                GROUP BY s_participantOrderMatch, s_expirationDate, s_expirationTime
                ) WHERE (koef_1_X2 < 100 or koef_1_X2 < 100 or koef_2_1X < 100 or koef_X_12 < 100 or koef_1_X_2 < 100 or koef_1_2 < 100) and s_participantOrderMatch is not null) As BestOdds,
        odds as chngOdds
                where BestOdds.s_participantOrderMatch = chngOdds.s_participantOrderMatch 
				and BestOdds.s_expirationDate = chngOdds.s_expirationDate 
				and BestOdds.s_expirationTime = chngOdds.s_expirationTime 
				and (BestOdds.max_1 = chngOdds.n_1 or BestOdds.max_X = chngOdds.n_X or BestOdds.max_2 = chngOdds.n_2 or BestOdds.max_12 = chngOdds.n_12 or BestOdds.max_X2 = chngOdds.n_X2)
            order by 3,4,5""")
    print("Result:")
    for row in cur:
        print(row)
    con.close()

def deleteOldOdds():
    con = sqlite3.connect("data.db")
    res = con.execute("DELETE FROM odds WHERE datetime(s_expirationDate || ' ' || s_expirationTime) < datetime('now','localtime')")
    con.commit()
    print("Deleted ", res.rowcount, "old odds")
    con.close()

def changeDiacritics(stringToChange):
    stringToChange = re.sub("á", "a", stringToChange)
    stringToChange = re.sub("Á", "A", stringToChange)
    stringToChange = re.sub("ą", "a", stringToChange)
    stringToChange = re.sub("Ä", "A", stringToChange)
    stringToChange = re.sub("ä", "a", stringToChange)
    stringToChange = re.sub("ć", "c", stringToChange)
    stringToChange = re.sub("Č", "C", stringToChange)
    stringToChange = re.sub("č", "c", stringToChange)
    stringToChange = re.sub("Ď", "D", stringToChange)
    stringToChange = re.sub("ď", "d", stringToChange)
    stringToChange = re.sub("đ", "d", stringToChange)
    stringToChange = re.sub("ė", "e", stringToChange)
    stringToChange = re.sub("é", "e", stringToChange)
    stringToChange = re.sub("ě", "e", stringToChange)
    stringToChange = re.sub("ë", "e", stringToChange)
    stringToChange = re.sub("ę", "e", stringToChange)
    stringToChange = re.sub("Í", "I", stringToChange)
    stringToChange = re.sub("í", "i", stringToChange)
    stringToChange = re.sub("Ľ", "L", stringToChange)
    stringToChange = re.sub("ľ", "l", stringToChange)
    stringToChange = re.sub("ł", "l", stringToChange)
    stringToChange = re.sub("Ł", "L", stringToChange)
    stringToChange = re.sub("ń", "n", stringToChange)
    stringToChange = re.sub("ň", "n", stringToChange)
    stringToChange = re.sub("Ö", "O", stringToChange)
    stringToChange = re.sub("ö", "o", stringToChange)
    stringToChange = re.sub("ó", "o", stringToChange)
    stringToChange = re.sub("ő", "o", stringToChange)
    stringToChange = re.sub("ř", "r", stringToChange)
    stringToChange = re.sub("Ř", "R", stringToChange)
    stringToChange = re.sub("ś", "s", stringToChange)
    stringToChange = re.sub("Ś", "S", stringToChange)
    stringToChange = re.sub("š", "s", stringToChange)
    stringToChange = re.sub("Š", "S", stringToChange)
    stringToChange = re.sub("ť", "t", stringToChange)
    stringToChange = re.sub("Ť", "T", stringToChange)
    stringToChange = re.sub("ü", "u", stringToChange)
    stringToChange = re.sub("Ú", "U", stringToChange)
    stringToChange = re.sub("Ü", "U", stringToChange)
    stringToChange = re.sub("ú", "u", stringToChange)
    stringToChange = re.sub("ű", "u", stringToChange)
    stringToChange = re.sub("ů", "u", stringToChange)
    stringToChange = re.sub("ý", "y", stringToChange)
    stringToChange = re.sub("ż", "z", stringToChange)
    stringToChange = re.sub("ź", "z", stringToChange)
    stringToChange = re.sub("ž", "z", stringToChange)
    stringToChange = re.sub("Ž", "Z", stringToChange) 
    stringToChange = re.sub(" / ", "/", stringToChange)
    stringToChange = re.sub("  ", " ", stringToChange)
    stringToChange = re.sub("Al-", "Al ", stringToChange)
    stringToChange = re.sub("Al ", "", stringToChange)
    stringToChange = re.sub("1. FC ", "", stringToChange)
    stringToChange = re.sub(" City", "", stringToChange)
    stringToChange = re.sub(" Utd.", "", stringToChange)
    stringToChange = re.sub(" Town", "", stringToChange)
    return stringToChange

def deletePrefixSufix(stringToChange):
    stringToChange = changeDiacritics(stringToChange)
    if re.search("^([A-Z][A-Z])( )(.*)$", stringToChange):        
        stringToChange = re.findall("^([A-Z][A-Z])( )(.*)$", stringToChange)[0][2] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]         
    if re.search("^([A-Z][A-Z][A-Z])( )(.*)$", stringToChange):        
        stringToChange = re.findall("^([A-Z][A-Z][A-Z])( )(.*)$", stringToChange)[0][2] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]         
    if re.search("^(.*)( )([A-Z][A-Z])$", stringToChange):        
        stringToChange = re.findall("^(.*)( )([A-Z][A-Z])$", stringToChange)[0][0] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]  
    if re.search("^(.*)( )([U][1-2][0-9])$", stringToChange):        
        stringToChange = re.findall("^(.*)( )([U][1-2][0-9])$", stringToChange)[0][0] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]  
    if re.search("^(.*)( )([1-2][0-9])$", stringToChange):        
        stringToChange = re.findall("^(.*)( )([1-2][0-9])$", stringToChange)[0][0] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]  
    if re.search("^([1-9][0-9][0-9][0-9])( )(.*)$", stringToChange):        
        stringToChange = re.findall("^([1-9][0-9][0-9][0-9])( )(.*)$", stringToChange)[0][2] # + " " + re.findall("([A-Z][A-Z])( )(.*)", stringToChange)[0][0]  
    return stringToChange

if __name__ == '__main__':
    if True:
        setDB(dropTables = True, createTables = True, deleteAllRowsOdds = True)
        # deleteOldOdds()
        if True:
            scrapNIKE()
            scrapTIPSPORT()
            scrapFORTUNA()
            scrapDOXXBET()
            scrapTIPOS()
            scrapSYNNOTTIP()
        setBindings()
        findBets()