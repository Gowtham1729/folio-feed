from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from .forms import InputForm


# Create your views here.
def index(request):
    return JsonResponse(
        {
            "message": "Hello, world!",
            "status": "ok",
        }
    )


def input_view(request):
    if request.method == "POST":
        form = InputForm(request.POST)
        if form.is_valid():
            request.session["user_input"] = form.cleaned_data["user_input"]
            return redirect("display")
    else:
        form = InputForm()
    return render(request, "input.html", {"form": form})


def display_view(request):
    user_input = request.session.get("user_input", "No input provided")
    return render(request, "display.html", {"user_input": user_input})
