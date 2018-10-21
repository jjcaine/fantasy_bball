import sys
import logging
import os

from flask import Flask, render_template, request, flash, redirect, url_for
from flask.logging import default_handler

from app.draft import get_data, compute_value, get_pickled_df, initialize_draft, teams, transaction, calculate_updated_values
from app.exceptions import DraftPickleException, DraftNotInitializedException

root = logging.getLogger()
root.addHandler(default_handler)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'

pickle_path = './df_value.pkl'
projections_path = '/Users/jjcaine/Downloads/BBM_projections.xls'


@app.route("/", methods=['GET', 'POST'])
def main():
    df_draft = None

    try:
        df_draft = get_pickled_df(pickle_path)
    except DraftPickleException:
        df_draft = get_data(projections_path)
        df_draft = compute_value(df_draft)
        df_draft = initialize_draft(df_draft)

    if request.method == 'POST':
        if df_draft is None:
            raise DraftNotInitializedException("Must initialize draft df before modifying it")

        drafted_player = request.form.get('drafted_player')
        drafting_team = request.form.get('drafting_team')
        draft_amount = int(request.form.get('draft_amount'))

        df_draft = transaction(df_draft, drafted_player, drafting_team, draft_amount)
        df_draft = calculate_updated_values(df_draft)

    df_draft.to_pickle(pickle_path)
    players = list(df_draft.index)

    return render_template('index.html', draft_data_table=df_draft.to_html(classes='table', escape=False),
                           teams=teams, players=players)


@app.route("/invalidate")
def invalidate():
    os.remove(pickle_path)
    flash("Invalidated saved dataframe, reloaded projections")
    return redirect(url_for('main'))


def hightlight_available(val):
    if val == 'Avail':
        return 'background-color: green'
    else:
        return 'background-color: red'
