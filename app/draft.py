import pandas as pd

teams = 16
team_budget = 269
league_dollars_total = teams * team_budget
roster_size = 14
starters = 10
total_players = teams * roster_size

scoring_categories = ['adjfg%', 'ft%', '3/g', '3%', 'or/g', 'dr/g', 'a/g', 's/g', 'b/g', 'to/g', 'p/g']
display_columns = ['calculated_value', 'calculated_$', 'g', 'm/g'] + scoring_categories


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

    # calculate the mean of our stat categories, using the total number of players that we'll have in the league.
    # The reason for this is we want to drop out the bottom tier of outliers that probably won't be a factor
    # into the draft.
    stat_means = df_stats.loc[:total_players, :].mean()

    # caculcate the std deviation for positive and negative stats. Again, just for the total number of
    # players we'll have in the league
    std_dev = df_stats.loc[:total_players, :].std()

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
    df_value = df.join(value.to_frame(), on="Rank")\
        .rename(columns={0: "calculated_value"})\
        .sort_values(by=['calculated_value'], ascending=False)

    # calculate player $ by determining the $/value point ratio
    total_league_value_output = float(df_value.loc[:total_players, ['calculated_value']].sum())
    dollar_per_value_point = league_dollars_total / total_league_value_output
    df_value['calculated_$'] = dollar_per_value_point * df_value['calculated_value']

    return df_value.set_index('Name', drop=False).loc[:, display_columns]

if __name__ == '__main__':
    df_projections = get_data('/Users/jjcaine/Downloads/BBM_projections.xls')
    df_value = compute_value(df_projections)
