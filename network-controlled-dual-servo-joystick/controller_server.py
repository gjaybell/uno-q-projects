from flask import Flask, request

app = Flask(__name__)

x_val = 0
y_val = 0

@app.route('/cmd')
def get_cmd():
    return f"{x_val},{y_val}"

@app.route('/update')
def update():
    global x_val, y_val
    x_val = int(request.args.get('x', 0))
    y_val = int(request.args.get('y', 0))
    return "OK"

app.run(host='0.0.0.0', port=5000)
