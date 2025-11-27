from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import os
from io import StringIO

app = Flask(__name__)
csv_path = 'logs.csv'

@app.route('/', methods=['GET'])
def index():
    gender_filter = request.args.get('gender', 'All')

    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=["Timestamp", "Gender"])
    else:
        df = pd.read_csv(csv_path, names=["Timestamp", "Gender"])

    if gender_filter != "All":
        df = df[df["Gender"] == gender_filter]

    df = df.sort_values(by="Timestamp", ascending=False)
    return render_template("index.html", data=df.to_dict(orient="records"), selected=gender_filter)

@app.route('/download')
def download_csv():
    if not os.path.exists(csv_path):
        return "No data to export.", 404
    return send_file(csv_path, as_attachment=True)

@app.route('/clear', methods=['POST'])
def clear_logs():
    open(csv_path, 'w').close()
    return redirect('/')

# ✅ Required to run the app
if __name__ == '__main__':
    app.run(debug=True)
