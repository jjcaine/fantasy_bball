from flask import Flask

from app.draft import get_data, compute_value

app = Flask(__name__)

@app.route("/")
def main():
    df_projections = get_data('/Users/jjcaine/Downloads/BBM_projections.xls')
    df_value = compute_value(df_projections)
    return df_value.to_html()