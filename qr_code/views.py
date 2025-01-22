from django.shortcuts import render
from django import forms
import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
import base64
from urllib.parse import urlparse


class QRCodeForm(forms.Form):
    url = forms.CharField(
        label="Enter URL",
        widget=forms.TextInput(attrs={'placeholder': 'Enter URL here...'})
    )
    bg_color = forms.CharField(
        label="Background Color",
        widget=forms.TextInput(attrs={'type': 'color', 'value': '#ffffff'})
    )
    fill_color = forms.CharField(
        label="Fill Color",
        widget=forms.TextInput(attrs={'type': 'color', 'value': '#000000'})
    )

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        parsed_url = urlparse(url)

        # If no scheme (http or https), prepend http://
        if not parsed_url.scheme:
            url = f"http://{url}"

        return url

    def generate_qr(self):
        url = self.cleaned_data["url"]
        bg_color = self.cleaned_data["bg_color"]
        fill_color = self.cleaned_data["fill_color"]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=bg_color)
        return img


def generate_qr_code(request):
    qr_image_base64 = None

    if request.method == "POST":
        form = QRCodeForm(request.POST)
        if form.is_valid():
            img = form.generate_qr()
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_data = buffer.getvalue()
            qr_image_base64 = base64.b64encode(img_data).decode('utf-8')
    else:
        form = QRCodeForm()

    return render(request, "qr_code/qr_code_form.html", {"form": form, "qr_image_base64": qr_image_base64})
