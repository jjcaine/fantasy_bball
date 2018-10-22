import sys
import logging
import os
from builtins import FileNotFoundError

from flask import Flask, render_template, request, flash, redirect, url_for
from flask.logging import default_handler

from app.draft import get_data, compute_value, get_pickled_df, initialize_draft, league_teams, transaction, \
    calculate_updated_values, replay_tranactions
from app.exceptions import DraftPickleException, DraftNotInitializedException, NoTransactionFileExists

root = logging.getLogger()
root.addHandler(default_handler)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'

pickle_path = './df_value.pkl'
projections_path = '/Users/jjcaine/Downloads/BBM_projections.xls'
transactions_file = 'transactions.json'


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
                           teams=league_teams, players=players)


@app.route("/invalidate_draft_frame")
def invalidate_draft_frame():
    os.remove(pickle_path)
    flash("Invalidated saved dataframe, reloaded projections")
    return redirect(url_for('main'))


@app.route('/replay')
def replay():
    df = get_pickled_df(pickle_path)

    try:
        df = replay_tranactions(df, transactions_file_path=transactions_file)
    except NoTransactionFileExists:
        flash("No log exists to replay")
        return redirect(url_for('main'))

    df.to_pickle(pickle_path)
    print(df)
    flash("Successfully replayed transactions from log")
    return redirect(url_for('main'))


@app.route('/clear-log')
def clear_log():
    try:
        os.remove(transactions_file)
    except FileNotFoundError:
        flash("No log file exists to clear")

    return redirect(url_for('main'))


def hightlight_available(val):
    if val == 'Avail':
        return 'background-color: green'
    else:
        return 'background-color: red'
