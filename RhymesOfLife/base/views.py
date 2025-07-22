from django.shortcuts import render

def home(request):
    return render(request, 'base/home.html')  # Look for 'home.html' inside 'templates/base/'

def ndst(request):
       return render(request, 'ndst.html')