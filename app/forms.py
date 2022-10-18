import requests
from django import forms
from .models import Inquiry



# お問合せ
class InquiryForm(forms.ModelForm):
    def __int__(self, *args, **kwargs):
        super(InquiryForm, self).__init__(*args, **kwargs)
        for field in self.fields.vales():
            field.widget.attrs["class"] = "form-control"

    class Meta:
        model = Inquiry
        fields = ('date', 'matter',)
        # fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(attrs={'readonly': 'readonly'}),
        }
        help_texts = {
            'date': '変更できません',
        }
