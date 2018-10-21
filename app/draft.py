import os

import pandas as pd

from app.exceptions import DraftPickleException

teams = 16
team_budget = 269
league_dollars_total = teams * team_budget
roster_size = 14
starters = 10
total_players = teams * roster_size

teams = ['Caine', 'Trivett', 'Deye']

scoring_categories = ['adjfg%', 'ft%', '3/g', '3%', 'or/g', 'dr/g', 'a/g', 's/g', 'b/g', 'to/g', 'p/g']
display_columns = ['calculated_value', 'g', 'm/g'] + scoring_categories


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
        replacement = df.loc[total_players + 10:total_players + 60, scoring_categories].median()
    elif replacement_approach == 'mean':
        replacement = df.loc[total_players + 10:total_players + 60, scoring_categories].mean()
    else:
        Exception("Replacement approach must be 'median' or 'mean'")

    # calculate the "value" (ie, z-score) for all stats
    stat_value = (df_stats - replacement) / std_dev

    # calculate total value by summing value from all cats
    value = stat_value.sum(axis=1)

    # join that back to the main stats dataframe
    df_value = df.join(value.to_frame(), on="Rank").rename(columns={0: "calculated_value"}).sort_values(by=['calculated_value'], ascending=False)

    # the old index is now arbitrary, so Names will be our new index
    df_value = df_value.set_index('Name', drop=False).loc[:, display_columns]

    # rank players by value. Order will be important later when we look at the top 'x' players by this ranking
    df_value['Rank'] = df_value['calculated_value'].rank(ascending=False)

    # get the total output of the league, ie the value sum of all the top x players in our league, where x is
    # the number of players per roster multiplied by the number of teams
    total_league_value_output = float(df_value.loc[(df_value['Rank'] <= total_players), ['calculated_value']].sum())

    # ratio of dollars per value point. this allows us to project how much each player is "worth"
    dollar_per_value_point = league_dollars_total / total_league_value_output

    # multiple our ratio by the value of each player to get the projected amout
    df_value['calculated_$'] = dollar_per_value_point * df_value['calculated_value']

    # return the df_value with the columns we care about for later on
    final_columns = ['calculated_value', 'calculated_$', 'g', 'm/g'] + scoring_categories
    return df_value.loc[:, final_columns]


def initialize_draft(df):
    """All this does is take in a df and add the 'owned' and 'sold_$' columns"""

    df.insert(2, 'owned', 'Avail')
    df.insert(3, 'sold_$', 0)
    return df.loc[:]


def transaction(df, player, team, dollar_amount):
    """
    Takes in a dataframe, updates the player with who bought them and for what dollar amount, returns the
    updated dataframe.
    """
    df.at[player, 'owned'] = team
    df.at[player, 'sold_$'] = dollar_amount
    return df


def calculate_updated_values(df):
    total_remaining_value = float(df.loc[(df['Rank'] <= total_players) & (df['Owned'] == 'Avail'), 'calculated_value'].sum())
    new_dollar_per_value_point = (league_dollars_total - float(df['sold_$'].sum())) / total_remaining_value
    df['new_$'] = new_dollar_per_value_point * df['calculated_value']
    df['bargain_diff'] = df['calculated_$'] - df['new_$']
    return df


def get_indicies(df):
    return list(df.index)



def get_pickled_df(path):
    if os.path.isfile(path):
        return pd.read_pickle(path)
    else:
        raise DraftPickleException("Pickle file does not exist")
