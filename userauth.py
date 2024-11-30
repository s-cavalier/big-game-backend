from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import time
import datetime
import os

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

@app.route('/uauth', methods=['POST'])
def signIn():
    time.sleep(2)
    user = request.get_json().get('username')
    pnum = request.get_json().get('pnum')
    
    if user is None and pnum is None:
        appendLog('Recieved bad input', 'userAuth')
        return jsonify({'error' : 'No username and phone number passed.', 'code' : 1})
    if user is None:
        appendLog('Recieved bad input', 'userAuth')
        return jsonify({'error' : 'No username passed.', 'code' : 2})
    if pnum is None:
        appendLog('Recieved bad input', 'userAuth')
        return jsonify({'error' : 'No phone number passed.', 'code' : 3})

    db = sqlite3.connect('userinfo.db')
    c = db.cursor()
    
    setup = c.execute(f'SELECT id FROM users WHERE username="{user}" AND pnum="{pnum}";')
    
    uID = setup.fetchone()
    
    if uID is None:
        try:
            c.execute(f"INSERT INTO users (username, pnum) VALUES ('{user}','{pnum}');")
            genUID = c.execute(f"SELECT id FROM users WHERE username='{user}'").fetchone()
            uID = genUID
            db.commit()
        except: 
            c.close()
            appendLog('Recieved bad input (mismatch @ already exists).', 'userAuth')
            return jsonify({'error':'username or phone number already exists', 'code': 4})
    c.close()
    response = make_response(jsonify([]))
    response.set_cookie(
        key="session",
        value=f"{uID[0]}",
        secure=True,
        samesite="Strict",
        max_age=3600
    )
    appendLog(f'Recieved {uID[0]} connected with good user authentication. Sending cookie...', 'userAuth')
    return response

@app.route('/logResponse', methods=['POST'])
def logResponse():
    time.sleep(2)
    formRes = request.get_json()
    try:
        uid = int(request.cookies['session'])
    except KeyError:
        appendLog('Recieved bad session.', 'logResponse')
        return jsonify("Invalid session.")
    except ValueError:
        uid = int(strip(request.cookies['session']))
    db = sqlite3.connect('userinfo.db')
    c = db.cursor()
    c.execute(f"INSERT OR REPLACE INTO forminfo (id, datesAvailable, willingToPay, idealSports, realNAME, extraNotes) VALUES ('{uid}', '{formRes['datesAvailable']}', '{formRes['willingToPay']}', '{formRes['idealSports']}', '{formRes['realName']}', '{formRes['extraNotes']}')")
    db.commit()
    c.close()
    appendLog(f'Recieved {uid} connected. Returning good response.', 'logResponse')
    return jsonify("Good Backend Response")

@app.route('/checkSession', methods=['POST'])
def checkSession():
    time.sleep(2)
    try:
        resChecker = int(request.cookies['session'])
    except KeyError:
        appendLog('Recieved bad session.', 'checkSession')
        return jsonify({ 'error' :'No sess.'})
    except ValueError:
        uid = int(strip(request.cookies['session']))
    db = sqlite3.connect('userinfo.db')
    c = db.cursor()
    tAnswers = (0, None, 0, '', '')
    tAnswers = c.execute(f"SELECT datesAvailable, willingToPay, idealSports, realNAME, extraNotes FROM forminfo WHERE id = {resChecker}").fetchone()
    if tAnswers is None:
        appendLog('Recieved uID {resChecker} connected. No previous info available.', 'checkSession')
        return jsonify({'error':"No old user info available."})
    unpack = tAnswers
    response = make_response (jsonify({
        'dateMask' : unpack[0],
        'canPay' : unpack[1],
        'sportMask' : unpack[2],
        'rName' : unpack[3],
        'extNotes' : unpack[4]
    }))
    response.set_cookie(
        key="session",
        value=f"{resChecker}",
        secure=True,
        samesite="Strict",
        max_age=3600
    )
    appendLog(f'Recieved uID {resChecker} connected. Returned previous forminfo.', 'checkSession')
    return response
    
def appendLog(log: str, type: str) -> None:
    dt = datetime.datetime.now()
    today = dt.date()
    now = dt.time()
    file = None
    try:
        file = open(f'logs/{today}.log', 'x')
    except:
        file = open(f'logs/{today}.log', 'a')
    
    file.write(f'[{now}] {type}: {log}\n')
    file.close()

def strip(word: str) -> str:
    word = ''
    for c in word:
        if not c.isnumeric():
            continue
        word += c
    return word
            

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
