from django.shortcuts import render, redirect

from .utils import get_data, compute_value, get_pickled_df, initialize_draft, league_teams, transaction, \
    calculate_updated_values, replay_tranactions, calculate_current_team_values, calculate_team_spending, \
    count_drafted_players, dollar_player_average_remaining
from .exceptions import DraftNotInitializedException, DraftPickleException
from .forms import DraftEntryForm

pickle_path = './df_value.pkl'
projections_path = '/Users/jjcaine/Downloads/BBM_projections_combined.xls'
transactions_file = 'transactions.json'


def value_dashboard(request):
    """View to display all teams and their current drafted players, team value,
    current spending, amount remaining, and average spending remaining"""
    df_draft = get_pickled_df(pickle_path)

    # summary stats
    team_values = calculate_current_team_values(df_draft, league_teams)
    team_spending, team_amount_remaining = calculate_team_spending(df_draft, league_teams)
    team_players_drafted = count_drafted_players(df_draft, league_teams)
    average_spending_remaining = dollar_player_average_remaining(df_draft, league_teams)

    return render(request, 'value_dashboard.html', {
        'teams': league_teams,
        'team_players_drafted': team_players_drafted,
        'team_values': team_values,
        'team_spending': team_spending,
        'team_amount_remaining': team_amount_remaining,
        'average_spending_remaining': average_spending_remaining
    })


def draft_entry(request):

    try:
        df_draft = get_pickled_df(pickle_path)
    except DraftPickleException:
        df_draft = get_data(projections_path)
        df_draft = compute_value(df_draft, replacement_approach='mean')
        df_draft = initialize_draft(df_draft)

    if request.method == 'POST':
        if df_draft is None:
            raise DraftNotInitializedException(
                "Must initialize draft df before modifying it")
        form = DraftEntryForm(request.POST)

        if form.is_valid():
            drafted_player = form.cleaned_data.get('player')
            drafting_team = form.cleaned_data.get('team')
            draft_amount = int(form.cleaned_data.get('dollar_amount'))

            df_draft = transaction(df_draft, drafted_player,
                                drafting_team, draft_amount)
            df_draft = calculate_updated_values(df_draft)
            df_draft.to_pickle(pickle_path)

            return redirect('draft_entry')

    form = DraftEntryForm()

    players = list(df_draft.index)

    return render(request, 'draft_entry.html', {
        'form': form,
        'teams': league_teams,
        'players': players,
    })


def draft_board(request):
    df_draft = None

    try:
        df_draft = get_pickled_df(pickle_path)
    except DraftPickleException:
        df_draft = get_data(projections_path)
        df_draft = compute_value(df_draft, replacement_approach='mean')
        df_draft = initialize_draft(df_draft)

    df_draft = calculate_updated_values(df_draft)
    df_draft.to_pickle(pickle_path)
    players = list(df_draft.index)

    # summary stats
    team_values = calculate_current_team_values(df_draft, league_teams)
    team_spending, team_amount_remaining = calculate_team_spending(
        df_draft, league_teams)
    team_players_drafted = count_drafted_players(df_draft, league_teams)
    average_spending_remaining = dollar_player_average_remaining(
        df_draft, league_teams)

    def availability(x): return '<span class="available">' + x + \
        '</span>' if x == 'Avail' else '<span class="unavailable">' + x + '</span>'

    return render(request, 'draft_board.html', {
        'draft_data_table': df_draft.round(decimals=2).to_html(classes='table table-hover',
                                                               escape=False,
                                                               formatters={
                                                                   'owned': availability},
                                                               table_id='player-table'),
        'teams': league_teams,
        'players': players,
        'team_values': team_values,
        'team_spending': team_spending,
        'team_amount_remaining': team_amount_remaining,
        'team_players_drafted': team_players_drafted,
        'average_spending_remaining': average_spending_remaining
    }
    )
