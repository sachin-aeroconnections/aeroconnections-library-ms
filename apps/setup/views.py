from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from .forms import ChangePinForm, SetupForm, SetupPinForm
from .models import SetupConfig

User = get_user_model()


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def pin_matches(entered_pin, stored_pin):
    if not stored_pin:
        return False
    return check_password(entered_pin, stored_pin)


class SetupGateView(View):
    """First step: Enter PIN to access setup"""

    def get(self, request):
        config = SetupConfig.get_config()

        if not config.setup_completed:
            return HttpResponseRedirect(reverse_lazy("setup:wizard"))

        if not config.setup_pin:
            return HttpResponseRedirect(reverse_lazy("account_login"))

        return render(request, "setup/gate.html", {
            "form": SetupPinForm()
        })

    def post(self, request):
        form = SetupPinForm(request.POST)
        if form.is_valid():
            config = SetupConfig.get_config()
            entered_pin = form.cleaned_data["pin"]

            if pin_matches(entered_pin, config.setup_pin):
                if entered_pin == config.setup_pin:
                    config.setup_pin = make_password(entered_pin)
                    config.save(update_fields=["setup_pin", "updated_at"])
                request.session["setup_access"] = True
                return HttpResponseRedirect(reverse_lazy("setup:wizard"))
            else:
                messages.error(request, "Invalid PIN. Please try again.")

        return render(request, "setup/gate.html", {"form": form})


class SetupWizardView(View):
    """Main setup wizard"""

    def get(self, request):
        config = SetupConfig.get_config()

        if config.setup_completed:
            if not request.session.get("setup_access"):
                return HttpResponseRedirect(reverse_lazy("setup:gate"))
            return HttpResponseRedirect(reverse_lazy("setup:security"))

        initial_data = {
            "domain": f"{request.scheme}://{request.get_host()}",
        }

        return render(request, "setup/wizard.html", {
            "form": SetupForm(initial=initial_data)
        })

    def post(self, request):
        form = SetupForm(request.POST)
        if form.is_valid():
            config = SetupConfig.get_config()

            admin_username = form.cleaned_data["admin_username"]
            admin_email = form.cleaned_data["admin_email"]
            admin_password = form.cleaned_data["admin_password"]
            setup_pin = form.cleaned_data["setup_pin"]
            domain = form.cleaned_data["domain"]
            library_name = form.cleaned_data["library_name"]
            loan_duration = form.cleaned_data["loan_duration"]
            due_soon_threshold = form.cleaned_data["due_soon_threshold"]
            max_books_per_borrower = form.cleaned_data["max_books_per_borrower"]

            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )

            from apps.notifications.models import Branding, LibrarySettings

            if not LibrarySettings.objects.exists():
                LibrarySettings.objects.create(
                    loan_duration_days=loan_duration,
                    due_soon_threshold=due_soon_threshold,
                    max_books_per_borrower=max_books_per_borrower,
                    is_active=True
                )

            if not Branding.objects.exists():
                Branding.objects.create(
                    library_name=library_name,
                    company_name="AeroConnections",
                    is_active=True
                )

            config.setup_completed = True
            config.setup_pin = make_password(setup_pin)
            config.domain = domain
            config.save()

            request.session.pop("setup_access", None)

            messages.success(request, "Setup completed successfully!")
            return HttpResponseRedirect(reverse_lazy("account_login") + "?setup=complete")

        return render(request, "setup/wizard.html", {"form": form})


class SetupSecurityView(View):
    """Security settings after setup"""

    def get(self, request):
        config = SetupConfig.get_config()

        if not request.session.get("setup_access"):
            return HttpResponseRedirect(reverse_lazy("setup:gate"))

        return render(request, "setup/security.html", {
            "form": ChangePinForm(),
            "current_pin_set": bool(config.setup_pin)
        })

    def post(self, request):
        config = SetupConfig.get_config()
        form = ChangePinForm(request.POST)

        if form.is_valid():
            current_pin = form.cleaned_data["current_pin"]
            new_pin = form.cleaned_data["new_pin"]

            if pin_matches(current_pin, config.setup_pin):
                config.setup_pin = make_password(new_pin)
                config.save()
                messages.success(request, "PIN changed successfully!")
            else:
                messages.error(request, "Current PIN is incorrect.")

        return render(request, "setup/security.html", {
            "form": form,
            "current_pin_set": bool(config.setup_pin)
        })


class SetupCompleteView(View):
    """Show setup completion message"""

    def get(self, request):
        return render(request, "setup/complete.html")
