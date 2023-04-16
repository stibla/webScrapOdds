DROP VIEW IF EXISTS v_bestOdds;
CREATE VIEW IF NOT EXISTS v_bestOdds
AS 
	SELECT BestOdds.*, chngOdds.* from
        (SELECT * FROM (
            SELECT part1.s_new_name as participant1, part2.s_new_name as participant2, s_expirationDate, s_expirationTime,  JULIANDAY(datetime(s_expirationDate || ' ' || s_expirationTime)) - JULIANDAY(datetime('now','localtime')) DiffToNow, COUNT(1), 
                max(n_1) as max_1, max(n_X) as max_X, max(n_2) as max_2, max(n_1X) as max_1X, max(n_12) as max_12, max(n_X2) as max_X2,
                case when COUNT(1) > 1 and max(n_1) is not null and max(n_X2) is not null then 100/max(n_1) + 100/max(n_X2) end as koef_1_X2,
                case when COUNT(1) > 1 and max(n_2) is not null and max(n_1X) is not null then 100/max(n_2) + 100/max(n_1X) end as koef_2_1X,
                case when COUNT(1) > 1 and max(n_X) is not null and max(n_12) is not null then 100/max(n_X) + 100/max(n_12) end as koef_X_12,
                case when COUNT(1) > 1 and max(n_1) is not null and max(n_X) is not null and max(n_2) is not null then 100/max(n_1) + 100/max(n_X) + 100/max(n_2) end as koef_1_X_2,
				case when COUNT(1) > 1 and max(n_1) is not null and max(n_X) is null and max(n_2) is not null then 100/max(n_1) + 100/max(n_2) end as koef_1_2
                FROM (SELECT s_betOffice, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, min(n_1) n_1,
					min(n_X) n_X, min(n_2) n_2, min(n_1X) n_1X, min(n_12) n_12, min(n_X2) n_X2
					FROM odds GROUP BY s_betOffice, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime) min_odds
					, e_participants as part1,  e_participants as part2
                where min_odds.s_participant1 = part1.s_old_name and min_odds.s_participant2 = part2.s_old_name
                GROUP BY part1.s_new_name, part2.s_new_name, s_expirationDate, s_expirationTime
                ) WHERE (koef_1_X2 < 100 or koef_1_X2 < 100 or koef_2_1X < 100 or koef_X_12 < 100 or koef_1_X_2 < 100 or koef_1_2 < 100)) As BestOdds,
        (SELECT part1.s_new_name as participant1, part2.s_new_name as participant2, odds.*
                FROM odds, e_participants as part1, e_participants as part2
                where odds.s_participant1 = part1.s_old_name and odds.s_participant2 = part2.s_old_name) as chngOdds
                where BestOdds.participant1 = chngOdds.participant1 and BestOdds.participant2 = chngOdds.participant2 and BestOdds.s_expirationDate = chngOdds.s_expirationDate 
				and BestOdds.s_expirationTime = chngOdds.s_expirationTime 
            order by 1,2,3;



CREATE VIEW IF NOT EXISTS v_noOfmatchGroup
AS 
SELECT POCET, COUNT(1) POCTY FROM (
SELECT part1.s_new_name as participant1, part2.s_new_name as participant2, odds.s_expirationDate, odds.s_expirationTime, COUNT(1) POCET
                FROM odds, e_participants as part1, e_participants as part2
                where odds.s_participant1 = part1.s_old_name and odds.s_participant2 = part2.s_old_name
GROUP BY part1.s_new_name, part2.s_new_name, odds.s_expirationDate, odds.s_expirationTime
) GROUP BY POCET;


CREATE VIEW IF NOT EXISTS v_noOfmatchPerOffice
AS
SELECT s_betOffice, COUNT(1)
FROM odds
GROUP BY s_betOffice;


DROP VIEW IF EXISTS v_odds;
CREATE VIEW IF NOT EXISTS v_odds
AS 
SELECT s_betOffice, s_participant1, s_participant2, part1.s_new_name as participant1, part2.s_new_name as participant2, s_participantOrder, s_expirationDate, s_expirationTime, min(n_1) n_1,
min(n_X) n_X, min(n_2) n_2, min(n_1X) n_1X, min(n_12) n_12, min(n_X2) n_X2
FROM odds, e_participants as part1, e_participants as part2
                where odds.s_participant1 = part1.s_old_name and odds.s_participant2 = part2.s_old_name
GROUP BY s_betOffice, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, part1.s_new_name, part2.s_new_name
order by 7,8,6;



DROP TABLE odds_h;
CREATE TABLE IF NOT EXISTS odds_h(
					_rowid INTEGER,
                    n_id_odd INTEGER, 
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
                    s_date_create TEXT,
					_version INTEGER,
					_updated TEXT,
					_IUD);

DROP TRIGGER odds_delete_history;					
CREATE TRIGGER IF NOT EXISTS odds_delete_history
AFTER DELETE ON odds
BEGIN
    INSERT INTO odds_h (_rowid, n_id_odd, s_betOffice, s_betId, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, n_1, n_X, n_2, n_1X, n_12, n_X2, 
                    s_date_create, _version, _updated, _IUD)
    VALUES (
        old.rowid,
        old.n_id_odd, old.s_betOffice, old.s_betId, old.s_participant1, old.s_participant2, old.s_participantOrder, old.s_expirationDate, old.s_expirationTime, old.n_1, old.n_X, old.n_2, old.n_1X, old.n_12, old.n_X2, old.s_date_create,
        (SELECT COALESCE(MAX(_version), 0) from odds_h WHERE _rowid = old.rowid) + 1,
        datetime('now', 'localtime'),
		"DELETE"
    );
END;

DROP TRIGGER odds_update_history;					
CREATE TRIGGER IF NOT EXISTS odds_update_history
AFTER UPDATE ON odds
FOR EACH ROW
BEGIN
    INSERT INTO odds_h (_rowid, n_id_odd, s_betOffice, s_betId, s_participant1, s_participant2, s_participantOrder, s_expirationDate, s_expirationTime, n_1, n_X, n_2, n_1X, n_12, n_X2, 
                    s_date_create, _version, _updated, _IUD)
    VALUES (
        old.rowid,
        old.n_id_odd, old.s_betOffice, old.s_betId, old.s_participant1, old.s_participant2, old.s_participantOrder, old.s_expirationDate, old.s_expirationTime, old.n_1, old.n_X, old.n_2, old.n_1X, old.n_12, old.n_X2, old.s_date_create,
        (SELECT COALESCE(MAX(_version), 0) from odds_h WHERE _rowid = old.rowid) + 1,
        datetime('now', 'localtime'),
		"UPDATE"
    );
END;


DROP TABLE IF EXISTS e_participants_h;
CREATE TABLE IF NOT EXISTS e_participants_h (
					_rowid INTEGER,
                    n_id_participants INTEGER,
                    s_old_name TEXT,
                    s_new_name TEXT, 
                    s_date_create TEXT,
					_version INTEGER,
					_updated TEXT,
					_IUD);
					
DROP TRIGGER IF EXISTS e_participants_delete_history;					
CREATE TRIGGER IF NOT EXISTS e_participants_delete_history
AFTER DELETE ON e_participants
BEGIN
    INSERT INTO e_participants_h (_rowid, n_id_participants, s_old_name, s_new_name, s_date_create, _version, _updated, _IUD)
    VALUES (
        old.rowid,
        old.n_id_participants, old.s_old_name, old.s_new_name, old.s_date_create,
        (SELECT COALESCE(MAX(_version), 0) from odds_h WHERE _rowid = old.rowid) + 1,
        datetime('now', 'localtime'),
		"DELETE"
    );
END;

DROP TRIGGER IF EXISTS e_participants_update_history;					
CREATE TRIGGER IF NOT EXISTS e_participants_update_history
AFTER UPDATE ON e_participants
FOR EACH ROW
BEGIN
    INSERT INTO e_participants_h (_rowid, n_id_participants, s_old_name, s_new_name, s_date_create, _version, _updated, _IUD)
    VALUES (
        old.rowid,
        old.n_id_participants, old.s_old_name, old.s_new_name, old.s_date_create,
        (SELECT COALESCE(MAX(_version), 0) from odds_h WHERE _rowid = old.rowid) + 1,
        datetime('now', 'localtime'),
		"UPDATE"
    );
END;


INSERT INTO e_participants_deleted(n_id_participants, s_old_name, s_new_name, s_date_create) 
            SELECT n_id_participants, s_old_name, s_new_name, s_date_create FROM e_participants
			WHERE e_participants.s_old_name not in (SELECT odds.s_participant1 from odds)
			AND e_participants.s_old_name not in (SELECT odds.s_participant2 from odds);
					
DELETE FROM e_participants
WHERE e_participants.s_old_name not in (SELECT odds.s_participant1 from odds)
AND e_participants.s_old_name not in (SELECT odds.s_participant2 from odds);

UPDATE e_participants
SET s_new_name = (SELECT e_participants_deleted.s_new_name
                  FROM e_participants_deleted
                  WHERE e_participants.s_old_name = e_participants_deleted.s_old_name)
WHERE EXISTS (SELECT e_participants_deleted.s_new_name
                  FROM e_participants_deleted
                  WHERE e_participants.s_old_name = e_participants_deleted.s_old_name);

DELETE FROM e_participants_deleted
WHERE e_participants_deleted.s_old_name in (SELECT odds.s_participant1 from odds)
OR e_participants_deleted.s_old_name in (SELECT odds.s_participant2 from odds);