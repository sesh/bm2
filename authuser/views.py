import base64
import hmac
import struct
import time

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView

# mintotp
# https://github.com/susam/mintotp


def hotp(key, counter, digits=6, digest="sha1"):
    key = base64.b32decode(key.upper() + "=" * ((8 - len(key)) % 8))
    counter = struct.pack(">Q", counter)
    mac = hmac.new(key, counter, digest).digest()
    offset = mac[-1] & 0x0F
    binary = struct.unpack(">L", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary)[-digits:].zfill(digits)


def totp(key, time_step=30, digits=6, digest="sha1"):
    return hotp(key, int(time.time() / time_step), digits, digest)


class LoginWithTotpForm(AuthenticationForm):
    one_time_password = forms.CharField(
        max_length=6, required=False, widget=forms.TextInput(attrs={"autocomplete": "one-time-code"})
    )

    def confirm_login_allowed(self, user):
        if user.totp_secret:
            try:
                code = self.cleaned_data["one_time_password"]
                secret = base64.b32encode(user.totp_secret.encode()).decode()
                if code != totp(secret):
                    raise Exception("Code does not match")
            except (IndexError, Exception):
                raise forms.ValidationError("Please enter the correct one time code.")


class LoginWithTotpView(LoginView):
    authentication_form = LoginWithTotpForm
