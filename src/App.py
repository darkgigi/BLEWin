from flask import Flask, render_template
from Connection import *
import flaskwebgui

app = Flask(__name__, template_folder='templates')
gui = flaskwebgui.FlaskUI(app=app,server='flask')

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/api/discover')
async def discover_button():
    devices = await discover()
    list_devices = [(device.name, device.address) for device in devices]
    context= {'devices': list_devices}
    return context

@app.route('/discover')
def discover_page():
    return render_template('discover.html', discover = True)

if __name__ == "__main__":
    gui.run()