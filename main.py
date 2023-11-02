#pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org screeninfo

import asyncio
import sys
import time
import hi
import requests
import keyboard
import pyautogui
from screeninfo import get_monitors
import socketio
import win32api, win32con
sio = socketio.AsyncClient()
f=0
flask_server_url = "https://xixya.com/api"
accumlatedmovment = [0,0,0]
sense = 10 #mouse sensetivity
shortcuts = {
    "Gui":"winleft",
    "⌫":"backspace",
    "Alt":"altleft",
    "⏎":"enter",
    "Ctrl":"ctrlleft",
    "←":"left",
    "↑":"up",
    "↓":"down",
    "→":"right",
    "⇧":"shiftleft",
    "Esc":"esc",
    "Del":"delete",
    "Tab":"tab"}

async def mouseconnect(id):

    await sio.connect('https://xixya.com', socketio_path='/api/socket.io/')

    await sio.emit("/api/connect","typerclient")
    await sio.emit("/api/roominit", {'id': id})
    print("ws connected")

    
async def roomjoin(id):
    await sio.disconnect()
    await asyncio.sleep(1)
    
    await sio.connect('https://xixya.com', socketio_path='/api/socket.io/')
    await sio.emit("/api/roominit", {'id': id})


@sio.on('mouseoffset')
def on_mouseoffset(message):
    global accumlatedmovment
    # Handle the "mouseoffset" event

    if int(message[0]) == 0:
        accumlatedmovment[0] += message[0] *sense
    if int(message[1]) == 0:
        accumlatedmovment[1] += message[1] *sense
    if accumlatedmovment[0] > sense/2 or accumlatedmovment[0] < -sense/2:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(accumlatedmovment[0]), 0, 0, 0)
        accumlatedmovment[0] = 0
    if accumlatedmovment[1] > sense/2 or accumlatedmovment[1] < -sense/2:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, int(accumlatedmovment[1]), 0, 0)
        accumlatedmovment[1] = 0
   
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(message[0]*sense*(abs(message[0])/1)), int(message[1]*sense*(abs(message[1])/1)), 0, 0) #small amount of acceleration

   

screeninfo = []
for m in get_monitors():
    screeninfo.append({"x":m.x, "y":m.y, "width":m.width, "height":m.height,"name":m.name})
#print(screeninfo)


if len(screeninfo) > 1:
    second_screen = screeninfo[1]
    
    # Coordinates of the point on the virtual screen
    x = second_screen["x"] + 100
    y = second_screen["y"] - 20000
    
    pyautogui.moveTo(x, y)



def post_screeninfo(uid,screeninfo):
    try:
        response = requests.post(f"{flask_server_url}/setscreeninfo", json={"id":uid,"screeninfo":screeninfo})
        if response.json()["message"] == "ok":
            print("Connected")
    except:
        print("failed to connecet to main server")


async def sendinput(input):
    keyboard.write(input)

async def clientcomms():
    dataaa = {"clientid": None, "body": None}
    #flask_server_url = "http://nomadst.ddns.net:5000/clientin"
    #flask_server_url ="http://192.168.1.153:5000/clientin"
    ping_interval = 10
    last_response = 0
    try:
        with open("client.txt", "r") as info:
            user_info = info.read()
    except:
        user_info = ""
    if len(user_info) < 2:
        print("id not found, create one thanks")
    while len(user_info) < 2:
        username = input("Username: ")
        password = input("Password: ")
        device_id = input("DeviceName: ")
        if len(device_id) < 2:
            continue
        dataaa["body"] = [username, password, device_id]
        response = requests.post(f"{flask_server_url}/clientin", json=dataaa)
        response.raise_for_status()
        if "message" in response.json():
            print(response.json()["message"])
        if "ID" in response.json():
            print("device added")
            user_info = str(response.json()["ID"])
            with open("client.txt", "w") as info:
                info.write(user_info)
            break
    
    dataaa = {"clientid": user_info}
    body = []
    outputmethod = []
    last_response = 12
    lastconenctiontype = 0
    #post_screeninfo(user_info,screeninfo)
    asyncio.create_task(mouseconnect(user_info))



    while True:
            # Send a heartbeat ping to the Flask server
            try:
                if not body:
                    response = requests.post(f"{flask_server_url}/clientin", json=dataaa)
                    #response.raise_for_status()
                    status = response.json()["status"]
                    if (response.json()["body"]):
                        body.extend(response.json()["body"])
                        outputmethod.extend( response.json()["type"])
                if status == "ok" and last_response != "ok":
                    print("Passive connection, waiting for main connection")
                    ping_interval = 5
                elif status == "active" and last_response != "active":
                    print("Active, waiting for inputs")
                    ping_interval = 0.2 #implement active/non active connection tyty
                
                if status == "active"  and body:
                    print("Command("+"type",str(outputmethod[0])+"):",body[0])
                    ping_interval = 0
                    if outputmethod[0] == 1:
                        keyboard.write(body[0])
                    elif outputmethod[0] == 2:
                        #body[0] = body[0].split(": ")[1]
                        keys = body[0].split("-")
                        for key in keys:
                            if key in shortcuts:
                                keys[keys.index(key)] = shortcuts[key]
                        try:
                            pyautogui.hotkey(*keys)
                        except:print("brokey")
                    elif outputmethod[0] == 4:
                        delaytime = body[0]#.split(": ")[1]
                        time.sleep(float(delaytime))
                    del(body[0])
                    del(outputmethod[0])
                elif status == "active": ping_interval = 0.2
                if last_response == 0:
                    print("Reconnecting Mouse")
                    asyncio.create_task(roomjoin(user_info))
                    print("reconnection attempt done")
                last_response = status

            except Exception as e:
                print(e)
                print(f'Failed to send heartbeat ping')
                last_response = 0
                ping_interval = 5
        
            # Wait for the next heartbeat ping interval
            await asyncio.sleep(ping_interval)
#run both clientcomms and mouseconnect at the same time
#async def main():
    #await asyncio.gather(mouseconnect(),clientcomms())

asyncio.run(clientcomms())


# make the key that is given accountwide, like a sub for user and password
# then each session is logged in,
