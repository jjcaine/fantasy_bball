import sys

from flask import Flask, render_template, request

from app.draft import get_data, compute_value, get_pickled_df, initialize_draft, teams, DraftPickleException
from app.draft import transaction

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'

pickle_path = './df_value.pkl'


@app.route("/", methods=['GET', ['POST']])
def main():
    df_draft = None

    try:
        df_draft = get_pickled_df(pickle_path).to_html()
    except DraftPickleException:
        pass

    if request.method == 'POST':
        if df_draft == None:

        drafted_player = request.form['player']
        drafting_team = request.form['drafting_team']
        draft_amount = request.form['draft_amount']

        df_draft = transaction()

    df_draft = get_data('/Users/jjcaine/Downloads/BBM_projections.xls')
    df_draft = compute_value(df_draft)
    df_draft = initialize_draft(df_draft)
    df_draft.to_pickle(pickle_path)
    players = list(df_draft.index)
    return render_template('index.html', draft_data_table=df_draft.to_html(classes='table'),
                           teams=teams, players=players)


@app.route("/another-route")
def test():
    return get_pickled_df(pickle_path).to_html()