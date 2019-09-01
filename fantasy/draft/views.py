import os

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .utils import get_data, compute_value, get_pickled_df, initialize_draft_dataframe, league_teams, transaction, \
    calculate_updated_values, replay_tranactions, calculate_current_team_values, calculate_team_spending, \
    count_drafted_players, dollar_player_average_remaining, top_available_players
from .exceptions import DraftNotInitializedException, DraftPickleException, InvalidTransactionException, NoTransactionFileExists
from .forms import DraftEntryForm, UploadProjectionsForm, CreateDraftForm, DraftConfigurationForm
from .models import Projection, Draft, ScoringCategory

pickle_path = './df_value.pkl'
projections_path = '/Users/jjcaine/Downloads/BBM_projections_combined.xls'
transactions_file = 'transactions.json'


def index(request):
    return render(request, 'index.html')


@login_required()
def value_dashboard(request):
    """View to display all teams and their current drafted players, team value,
    current spending, amount remaining, and average spending remaining"""
    df_draft = get_pickled_df(pickle_path)

    # summary stats
    team_values = calculate_current_team_values(df_draft, league_teams)
    team_spending, team_amount_remaining = calculate_team_spending(
        df_draft, league_teams)
    team_players_drafted = count_drafted_players(df_draft, league_teams)
    average_spending_remaining = dollar_player_average_remaining(
        df_draft, league_teams)

    return render(request, 'value_dashboard.html', {
        'teams': league_teams,
        'team_players_drafted': team_players_drafted,
        'team_values': team_values,
        'team_spending': team_spending,
        'team_amount_remaining': team_amount_remaining,
        'average_spending_remaining': average_spending_remaining
    })


@login_required()
def draft_entry(request):
    try:
        df_draft = get_pickled_df(pickle_path)
    except DraftPickleException:
        df_draft = get_data(projections_path)
        df_draft = compute_value(df_draft, replacement_approach='mean')
        df_draft = initialize_draft_dataframe(df_draft)

    players = list(df_draft.index)

    if request.method == 'POST':
        if df_draft is None:
            raise DraftNotInitializedException(
                "Must initialize draft df before modifying it")
        form = DraftEntryForm(request.POST)

        if form.is_valid():
            drafted_player = form.cleaned_data.get('player')
            drafting_team = form.cleaned_data.get('team')
            draft_amount = int(form.cleaned_data.get('dollar_amount'))

            try:
                df_draft = transaction(df_draft, drafted_player,
                                       drafting_team, draft_amount)
            except InvalidTransactionException:
                messages.error(request, "Invalid transaction. Must receive a player, team, and dollar amount > 0")
                return render(request, 'draft_entry.html', {'form': form, 'teams': league_teams,
                                                            'players': players, })
            df_draft = calculate_updated_values(df_draft)
            df_draft.to_pickle(pickle_path)

            messages.success(request, f"Successfully drafted {drafted_player} to {drafting_team} for ${draft_amount}")
            return redirect('draft_entry')
        else:
            return render(request, 'draft_entry.html', {'form': form, 'teams': league_teams,
                                                        'players': players, })

    form = DraftEntryForm()

    return render(request, 'draft_entry.html', {
        'form': form,
        'teams': league_teams,
        'players': players,
    })


@login_required()
def draft_board(request):
    df_draft = None

    try:
        df_draft = get_pickled_df(pickle_path)
    except DraftPickleException:
        df_draft = get_data(projections_path)
        df_draft = compute_value(df_draft, replacement_approach='mean')
        df_draft = initialize_draft_dataframe(df_draft)

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

    def availability(x):
        return '<span class="available">' + x + \
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


@login_required()
def top_available_players_board(request):
    df_draft = get_pickled_df(pickle_path)
    df_top_available_players = top_available_players(df_draft, 25)

    return render(request, 'top_available_players.html', {
        'draft_data_table': df_top_available_players.round(decimals=2).to_html(classes='table table-hover',
                                                                               escape=False,
                                                                               table_id='player-table'),
    })


@login_required()
def invalidate_draft_frame(request):
    try:
        os.remove(pickle_path)
    except FileNotFoundError:
        messages.warning(request, "No dataframe file to invalidate.")
        pass
    df_draft = get_data(projections_path)
    df_draft = compute_value(df_draft, replacement_approach='mean')
    df_draft = initialize_draft_dataframe(df_draft)
    df_draft = calculate_updated_values(df_draft)
    df_draft.to_pickle(pickle_path)
    messages.success(request, "Invalidated saved dataframe, reloaded projections")
    return redirect('draft_entry')


@login_required()
def replay(request):
    df = get_pickled_df(pickle_path)

    try:
        df = replay_tranactions(df, transactions_file_path=transactions_file)
    except NoTransactionFileExists:
        messages.error(request, "No log exists to replay")
        return redirect('draft_entry')

    df.to_pickle(pickle_path)
    messages.success(request, "Successfully replayed transactions from log")
    return redirect('draft_entry')


@login_required()
def upload_projections(request, draft_id):
    draft = Draft.objects.filter(id=draft_id).first()
    if request.method == 'POST':
        form = UploadProjectionsForm(request.POST, request.FILES)
        if form.is_valid():
            projection = Projection.new_projection(request.user, draft)
            projection_file_extension = os.path.splitext(request.FILES['file'].name)[1]
            with open(os.path.join(settings.MEDIA_ROOT, f"{projection.id}{projection_file_extension}"), 'wb') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)
            return redirect('upload_projections')
    else:
        form = UploadProjectionsForm()
    return render(request, 'upload_projections.html', {'form': form, 'draft': draft})


@login_required()
def create_draft(request):
    if request.method == 'POST':
        form = DraftConfigurationForm(request.POST)
        if form.is_valid():
            draft = form.save()
            return redirect('upload_projections', draft_id=draft.id)
    form = DraftConfigurationForm()
    return render(request, 'create_draft.html', {'form': form})


@login_required()
def draft_configuration_home(request, draft_id):
    draft = Draft.objects.filter(id=draft_id).first()
    return render(request, 'draft_configuration_home.html', {'draft_name': draft.draft_name})


@login_required()
def configure_projection_columns():
    return