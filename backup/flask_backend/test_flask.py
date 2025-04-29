from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Witaj, świecie! Flask działa!'

if __name__ == '__main__':
    print("Uruchamiam minimalną aplikację Flask...")
    app.run(debug=True)
