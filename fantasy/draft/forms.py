from django import forms
from .models import Draft

class DraftEntryForm(forms.Form):
    player = forms.CharField(widget=forms.TextInput(attrs={'id': 'player-dropdown', 'placeholder': 'Player', 'autocomplete': 'off'}))
    team = forms.CharField(widget=forms.TextInput(attrs={'id': 'team-dropdown', 'placeholder': 'Team', 'autocomplete': 'off'}))
    dollar_amount = forms.IntegerField(min_value=1, widget=forms.TextInput(attrs={'placeholder': '$ Amount', 'autocomplete': 'off'}))


class UploadProjectionsForm(forms.Form):
    file = forms.FileField()


class CreateDraftForm(forms.Form):
    draft_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Draft Name', 'autocomplete': 'off'}))


class DraftConfigurationForm(forms.ModelForm):
    class Meta:
        model = Draft
        fields = ['draft_name', 'scoring_categories']

    def __init__(self, *args, **kwargs):
        super(DraftConfigurationForm, self).__init__(*args, **kwargs)
        self.fields['scoring_categories'].widget = forms.widgets.CheckboxSelectMultiple()