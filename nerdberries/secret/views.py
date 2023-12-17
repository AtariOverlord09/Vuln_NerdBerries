from encodings import utf_8
import subprocess
from sys import stderr

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from secret.forms import PingForm


@csrf_exempt
def ping_site(request):
    if request.method == 'POST':
        form = PingForm(request.POST)
        if form.is_valid():
            site_url = form.cleaned_data['site_url']
            command = f'ping {site_url}'
            try:
                result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                result = result.decode('utf-8', errors='replace')
                print(result)
            except subprocess.CalledProcessError as e:
                result = str(e)
        else:
            result = 'Форма содержит ошибки.'
    else:
        form = PingForm()
        result = None

    return render(request, 'secret/ping.html', {'form': form, 'result': result})
