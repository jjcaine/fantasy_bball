from django import forms
from .models import Draft, ProjectionColumns

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


class BaseProjectionColumnsFormset(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        projection_id = kwargs.pop('projection_id')
        super().__init__(*args, **kwargs)
        self.queryset = ProjectionColumns.objects.filter(id=projection_id)


class ProjectionColumnsConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProjectionColumns
        fields = ['column_name', 'mapped_scoring_category', 'informational', 'discard']
