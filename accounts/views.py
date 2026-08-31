from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    orders = request.user.orders.prefetch_related("items")[:5]
    return render(request, "accounts/dashboard.html", {"orders": orders})


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})
