from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    """
    View function for the home page of Gaduka Gang forum
    """
    return render(request, 'index.html')