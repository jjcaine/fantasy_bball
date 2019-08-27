from django import forms


class DraftEntryForm(forms.Form):
    player = forms.CharField(widget=forms.TextInput(attrs={'id': 'player-dropdown', 'placeholder': 'Player', 'autocomplete': 'off'}))
    team = forms.CharField(widget=forms.TextInput(attrs={'id': 'team-dropdown', 'placeholder': 'Team', 'autocomplete': 'off'}))
    dollar_amount = forms.IntegerField(min_value=0, widget=forms.TextInput(attrs={'placeholder': '$ Amount', 'autocomplete': 'off'}))