from django import forms

class PingForm(forms.Form):
    site_url = forms.CharField(label='URL сайта', required=True)