import json
import os
import logging

from django.template.defaulttags import register

import pandas as pd

from .exceptions import DraftPickleException, NoTransactionFileExists, InvalidTransactionException

num_teams = 16
team_budget = 269
league_dollars_total = num_teams * team_budget
roster_size = 14
starters = 10
total_players = num_teams * roster_size

league_teams = ['Team Lyons (Shawn Lyons)',
                'Florida Man (Charlie Deye)',
                'Team Jacobs (Kyle Jacobs)',
                'Luka Mateam! (Mark Skrzydlak)',
                'Great White Buffalo (Ren Nunes)',
                'NBA- Nothing But Aquisitions (Chris Baird)',
                'Team Sanderson (Aaron Sanderson)',
                'Team Dzialo (Bryan Dzialo)',
                'Team Raterman (Tom Raterman)',
                'If There Ever Was a BM (Nick Trivett)',
                'Control The Narrative (Anthony McCready)',
                'Midrange Jumper Is Underrated (Eric Duncan)',
                'Pipe Dreams (John Caine)',
                'Team DAZA (Luis Daza)',
                'Game... Blouses (Evan Beesley)',
                'Team A Lyons (Adam Lyons)'
                ]

# For mock drafts
league_teams = [
    'Team Caine',
    'Team 2',
    'Team 3',
    'Team 4',
    'Team 5',
    'Team 6',
    'Team 7',
    'Team 8',
    'Team 9',
    'Team 10',
    'Team 11',
    'Team 12',
    'Team 13',
    'Team 14',
    'Team 15',
    'Team 16'
]

scoring_categories = ['adjfg%', 'ft%', '3/g', '3%',
                      'or/g', 'dr/g', 'a/g', 's/g', 'b/g', 'to/g', 'p/g']
display_columns = ['calculated_value', 'g',
                   'm/g', 'Inj', 'Team'] + scoring_categories


def get_data(projections_path):
    """Opens a projection Excel sheet and returns a pandas dataframe"""
    df = pd.read_excel(projections_path, index_col='Rank', dtype={'Inj': str})
    return df


def compute_value(df, replacement_approach='median'):
    """
    Takes in a pandas data frame, shaped appropriately, and a list of scoring categories and returns a pandas dataframe
    with each player, projected value, and a projected dollar amount
    """

    df_stats = df.loc[:, scoring_categories]

    # try to convert turnovers to negative so we can subtract their value
    try:
        df_stats['to/g'] = df_stats['to/g'] * -1
    except KeyError as e:
        print("to/g not in scoring categories")

    # calculate the std deviation for positive and negative stats. Again, just for the total number of
    # players we'll have in the league
    std_dev = df_stats.loc[:total_players, :].std()

    # calculate what a replacement player looks like, depending on the approach (median vs mean)
    if replacement_approach == 'median':
        replacement = df.loc[total_players +
                             10:total_players + 60, scoring_categories].median()
    elif replacement_approach == 'mean':
        replacement = df.loc[total_players +
                             10:total_players + 60, scoring_categories].mean()
    else:
        Exception("Replacement approach must be 'median' or 'mean'")

    # calculate the "value" (ie, z-score) for all stats
    stat_value = (df_stats - replacement) / std_dev

    # calculate total value by summing value from all cats
    value = stat_value.sum(axis=1)

    # join that back to the main stats dataframe
    df_value = df.join(value.to_frame(), on="Rank").rename(columns={
        0: "calculated_value"}).sort_values(by=['calculated_value'], ascending=False)

    # the old index is now arbitrary, so Names will be our new index
    df_value = df_value.set_index('Name', drop=True).loc[:, display_columns]

    # rank players by value. Order will be important later when we look at the top 'x' players by this ranking
    df_value['rank'] = df_value['calculated_value'].rank(ascending=False)

    # get the total output of the league, ie the value sum of all the top x players in our league, where x is
    # the number of players per roster multiplied by the number of teams
    total_league_value_output = float(
        df_value.loc[(df_value['rank'] <= total_players), ['calculated_value']].sum())

    # ratio of dollars per value point. this allows us to project how much each player is "worth"
    dollar_per_value_point = league_dollars_total / total_league_value_output

    # multiple our ratio by the value of each player to get the projected amout
    df_value['calculated_$'] = dollar_per_value_point * \
        df_value['calculated_value']

    # return the df_value with the columns we care about for later on
    final_columns = ['calculated_value', 'calculated_$', 'g',
                     'm/g', 'Team', 'Inj'] + scoring_categories + ['rank']
    return df_value.loc[:, final_columns]


def initialize_draft_dataframe(df):
    """All this does is take in a df and add the 'owned' and 'sold_$' columns"""

    df.insert(2, 'new_$', df['calculated_$'])
    df.insert(3, 'bargain_$', df['calculated_$'] - df['new_$'])
    df.insert(4, 'sold_$', 0)
    df.insert(5, 'owned', 'Avail')
    return df


def transaction(df, player, team, dollar_amount, write_to_log=True, transaction_file_path='transactions.json'):
    """
    Takes in a dataframe, updates the player with who bought them and for what dollar amount, returns the
    updated dataframe. Optionally calls log_transaction to log to the transaction file.
    """
    if player and team and (dollar_amount and dollar_amount > 0):
        if write_to_log:
            log_transaction(transaction_file_path, player, team, dollar_amount)
        df_updated = df.copy()
        df_updated.at[player, 'owned'] = team
        df_updated.at[player, 'sold_$'] = dollar_amount
        return df_updated
    else:
        raise InvalidTransactionException(
            f"Invalid transaction -- player: {player}, team: {team}, dollar amount: {dollar_amount}"
        )


def log_transaction(transaction_file_path, player, team, dollar_amount):
    """Logs a transaction to the transaction file. Will create the file if it does not exist yet."""
    j = {'transactions': []}
    if os.path.isfile(transaction_file_path):
        with open(transaction_file_path, 'r') as transaction_file:
            j = json.load(transaction_file)

    current_transaction = {'player': player,
                           'team': team, 'dollar_amount': dollar_amount}
    j['transactions'].append(current_transaction)

    with open(transaction_file_path, 'w') as transaction_file:
        transaction_file.write(json.dumps(j, indent=4))


def calculate_updated_values(df):
    total_remaining_value = float(df.loc[(df['rank'] <= total_players) & (
        df['owned'] == 'Avail'), 'calculated_value'].sum())
    new_dollar_per_value_point = (
        league_dollars_total - float(df['sold_$'].sum())) / total_remaining_value
    df['new_$'] = new_dollar_per_value_point * df['calculated_value']
    df['bargain_$'] = df['calculated_$'] - df['new_$']
    return df


def calculate_current_team_values(df, teams):
    """Returns a dictionary with all teams and their total value"""
    team_values = {}
    for t in teams:
        value = round(
            float(df.loc[(df['owned'] == t), ['calculated_value']].sum()), 2)
        team_values[t] = value

    return team_values


def calculate_team_spending(df, teams):
    """Returns a dictionary with all teams spending"""
    team_spending = {}
    amount_remaining = {}
    for t in teams:
        dollars_spent = int(df.loc[(df['owned'] == t), ['sold_$']].sum())
        team_spending[t] = dollars_spent
        amount_remaining[t] = team_budget - dollars_spent
    return team_spending, amount_remaining


def count_drafted_players(df, teams):
    """Returns a dictionary with a count of players drafted for each team"""
    player_count = {}
    for t in teams:
        player_count[t] = int(df.loc[(df['owned'] == t), 'g'].count())
    return player_count


def dollar_player_average_remaining(df, teams):
    """Returns a dictionary with how much each team can spend on avg for the number of players they have remaining"""
    average_remaining = {}
    for t in teams:
        average_remaining[t] = round((team_budget - int(df.loc[(df['owned'] == t), ['sold_$']].sum())) / (
            roster_size - int(df.loc[(df['owned'] == t), 'g'].count())), 2)
    return average_remaining


def top_available_players(df, top_n):
    return df.loc[df['owned'] == 'Avail'].head(top_n)


def replay_tranactions(df, transactions_file_path='transactions.json'):
    transactions = {}
    try:
        with open(transactions_file_path, 'r') as transactions_file:
            transactions = json.load(transactions_file)
    except FileNotFoundError:
        raise NoTransactionFileExists

    for t in transactions['transactions']:
        df = transaction(df, t['player'], t['team'],
                         t['dollar_amount'], write_to_log=False)
    return df


def get_pickled_df(path):
    if os.path.isfile(path):
        return pd.read_pickle(path)
    else:
        raise DraftPickleException("Pickle file does not exist")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)