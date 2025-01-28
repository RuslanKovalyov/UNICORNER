import base64
import re
from io import BytesIO
from urllib.parse import urlparse

import qrcode
from PIL import Image, ImageDraw, ImageColor
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.shortcuts import render
from qrcode.image.pil import PilImage
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import SquareModuleDrawer

# TODO: Use a better logo and the correct path for production
IMAGE_PATH = f'{settings.STATIC_ROOT}/main/images/logo/logo-dark.png'


class QRCodeForm(forms.Form):
    url = forms.CharField(
        label="Enter URL",
        widget=forms.TextInput(attrs={'placeholder': 'Enter URL here...'})
    )
    bg_color = forms.CharField(
        label="Background Color",
        widget=forms.TextInput(attrs={'type': 'color', 'value': '#ffff00'})
    )
    fill_color = forms.CharField(
        label="Fill Color",
        widget=forms.TextInput(attrs={'type': 'color', 'value': '#300030'})
    )
    border_radius = forms.IntegerField(
        label="Border Radius (pixels)",
        initial=20,
        min_value=0,
        max_value=100
    )
    unuse_image = forms.BooleanField(
        label='Do not use the Unicorner logo',
        required=False
    )

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        parsed_url = urlparse(url)

        # If no scheme, prepend http://
        if not parsed_url.scheme:
            url = f"https://{url}"

        # Validate URL
        validator = URLValidator(schemes=["http", "https"])
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL. Please enter a valid URL starting with http:// or https://.")

        # Optional: Disallow dangerous characters
        if re.search(r'[\'";]', url):
            raise ValidationError("Invalid URL. It contains potentially dangerous characters.")

        return url

    def generate_qr(self):
        url = self.cleaned_data["url"]
        bg_color = self.cleaned_data["bg_color"]
        fill_color = self.cleaned_data["fill_color"]
        border_radius = self.cleaned_data["border_radius"]
        unuse_image = self.cleaned_data["unuse_image"]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        if unuse_image:
            kwargs = {'image_factory': PilImage, 'fill_color': fill_color, 'back_color': bg_color}
        else:
            bg_rgb = ImageColor.getrgb(bg_color)
            fill_rgb = ImageColor.getrgb(fill_color)
            color_mask = SolidFillColorMask(back_color=bg_rgb, front_color=fill_rgb)
            kwargs = {'image_factory': StyledPilImage, 'embeded_image_path': IMAGE_PATH,
                      'module_drawer': SquareModuleDrawer(), 'color_mask': color_mask}
        # Generate the QR code image
        img = qr.make_image(**kwargs).convert("RGBA")

        # Add rounded corners
        width, height = img.size
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, width, height), radius=border_radius, fill=255)
        img.putalpha(mask)

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
