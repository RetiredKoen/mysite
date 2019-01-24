from django import forms


class RoundReplyForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()
        correct_entered = False
        for key, value in cleaned_data.items():
            if key[-7:] == 'correct':
                correct_entered = False
                if value is not None:
                    correct_entered = True
            if key[-5:] == 'wrong':
                if value is not None:
                    if correct_entered:
                        raise forms.ValidationError("Enter only correct or wrong for a rival", code=key,)
        return cleaned_data


class RoundJudgeForm(forms.Form):
    pass
