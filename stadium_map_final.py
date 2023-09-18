import sqlite3
import ssl
import requests
import codecs

conn = sqlite3.connect('footballvenues.sqlite')
cur = conn.cursor()

cur.executescript('''
DROP TABLE IF EXISTS Competitions;
DROP TABLE IF EXISTS Teams;

CREATE TABLE Competitions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    competition TEXT UNIQUE
);

CREATE TABLE Teams (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    team TEXT UNIQUE,
    venue TEXT,
    address TEXT UNIQUE,
    competition_id INTEGER
);
''')

url = 'https://api.football-data.org/v4/competitions/PL/teams?season=2022'
headers = {'X-Auth-Token': 'ENTER_API_KEY'}

response = requests.get(url, headers=headers)

data = response.json()
competition = data['competition']
teams = data['teams']

competition_name = competition['name']
    
for team in teams:
    team_name = team['shortName']
    venue_name = team['venue']
    venue_address = team['address']
    
    if team_name is None or venue_name is None or venue_address is None:
        continue
        
    cur.execute('INSERT OR IGNORE INTO Competitions (competition) VALUES ( ? )', (competition_name,))
    cur.execute('SELECT id FROM Competitions WHERE competition = ? ', (competition_name,))
    competition_id = cur.fetchone()[0]
    
    cur.execute('''INSERT OR IGNORE INTO Teams 
                (team, venue, address, competition_id) 
                VALUES ( ?, ?, ?, ? )''',
                (team_name, venue_name, venue_address, competition_id))
    
    conn.commit()

print('Successfully Retrieved Premier League Data')    

url = 'https://api.football-data.org/v4/competitions/ELC/teams?season=2022'
response = requests.get(url, headers=headers)

data = response.json()
competition = data['competition']
teams = data['teams']

competition_name = competition['name']
    
for team in teams:
    team_name = team['shortName']
    venue_name = team['venue']
    venue_address = team['address']
    
    if team_name is None or venue_name is None or venue_address is None:
        continue
        
    cur.execute('INSERT OR IGNORE INTO Competitions (competition) VALUES ( ? )', (competition_name,))
    cur.execute('SELECT id FROM Competitions WHERE competition = ? ', (competition_name,))
    competition_id = cur.fetchone()[0]
    
    cur.execute('''INSERT OR IGNORE INTO Teams 
                (team, venue, address, competition_id) 
                VALUES ( ?, ?, ?, ? )''',
                (team_name, venue_name, venue_address, competition_id))
    
    conn.commit()
    
print('Successfully Retrieved Championship Data')

api_key = 'ENTER_YOUR_API_KEY'

conn = sqlite3.connect('footballvenues.sqlite')
cur = conn.cursor()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cur.execute('SELECT address FROM Teams')
rows = cur.fetchall()

for row in rows:
    address = row[0]
    
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'key': api_key,
        'address': address
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == 'OK' and len(data['results']) >0:
        location = data['results'][0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
    else:
        latitude = None
        longitude = None
        
    cur.execute("PRAGMA table_info(Teams)")
    columns = cur.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'coordinates' not in column_names:
        cur.execute("ALTER TABLE Teams ADD COLUMN coordinates TEXT")
    
    cur.execute("UPDATE Teams SET coordinates = ? WHERE address = ?", (f"{latitude}, {longitude}", address))
    conn.commit()
    
conn.close()

conn = sqlite3.connect('footballvenues.sqlite')
cur = conn.cursor()

cur.execute('SELECT * FROM Teams')
fhand = codecs.open('stadium_addresses.js', 'w', 'utf-8')
fhand.write("var stadiumAddresses = [\n")
count = 0 

for row in cur:
    address = row[3]
    coordinates = row[5]
    
    lat, lng = coordinates.split(',')
    where = address.replace("'", "")
    
    try:
        count = count + 1
        if count > 1:
            fhand.write(",\n")
        output = "[" + lat.strip() + "," + lng.strip() + ", '" + where + "']"
        fhand.write(output)
    except:
        continue
        
fhand.write("\n];\n")
cur.close()
fhand.close()
print(count, "records written to stadium_addresses.js")