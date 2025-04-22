from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "¡Hola, Hospital General de México!"

if __name__ == '__main__':
    app.run(debug=True)
