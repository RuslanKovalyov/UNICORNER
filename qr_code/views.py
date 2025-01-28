from django.shortcuts import render
from django import forms
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import SquareModuleDrawer
from qrcode.constants import ERROR_CORRECT_H
from io import BytesIO
import base64
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from urllib.parse import urlparse
import re
from PIL import Image, ImageDraw, ImageColor, ImageOps
from django.conf import settings

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

        # Optional: Disallow suspicious characters
        if re.search(r'[\'";]', url):
            raise ValidationError("Invalid URL: contains potentially dangerous characters.")

        return url

    def generate_qr(self):
        url = self.cleaned_data["url"]
        bg_color = self.cleaned_data["bg_color"]
        fill_color = self.cleaned_data["fill_color"]
        border_radius = self.cleaned_data["border_radius"]
        unuse_image = self.cleaned_data["unuse_image"]

        # Convert user-chosen hex color to RGB
        bg_rgb = ImageColor.getrgb(bg_color)       # e.g. '#ffff00' -> (255, 255, 0)
        fill_rgb = ImageColor.getrgb(fill_color)   # e.g. '#300030' -> (48, 0, 48)

        # 1. Create the QR code (RGBA)
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_H,  # ~30% error correction
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_kwargs = {
            "image_factory": StyledPilImage,
            "module_drawer": SquareModuleDrawer(),
            "color_mask": SolidFillColorMask(back_color=bg_rgb, front_color=fill_rgb),
        }

        img_qr = qr.make_image(**qr_kwargs).convert("RGBA")

        # 2. (Optional) Embed the logo in the center, recolored + margin
        if not unuse_image:
            logo = Image.open(IMAGE_PATH).convert("RGBA")

            # --- (A) Recolor the black portion of the logo to the QR's fill_color ---
            alpha_channel = logo.getchannel("A")
            logo_gray = logo.convert("L")
            logo_colorized = ImageOps.colorize(
                logo_gray,
                black=fill_color,
                white=fill_color
            )
            # Reapply alpha to preserve transparency shape
            logo_colorized.putalpha(alpha_channel)

            # --- (B) Fill any transparent region with QR's bg_color ---
            bg_for_logo = Image.new("RGBA", logo_colorized.size, bg_rgb + (255,))
            bg_for_logo.paste(logo_colorized, mask=logo_colorized)

            # --- (C) Resize if needed (avoid covering too much of the QR) ---
            qr_width, qr_height = img_qr.size
            max_logo_width = qr_width * 0.20
            if bg_for_logo.width > max_logo_width:
                ratio = max_logo_width / float(bg_for_logo.width)
                new_size = (int(bg_for_logo.width * ratio), int(bg_for_logo.height * ratio))
                bg_for_logo = bg_for_logo.resize(new_size, Image.LANCZOS)

            # --- (D) Add a margin around the logo so it doesn't touch the code modules ---
            margin = 10  # adjust as you like
            expanded_w = bg_for_logo.width + margin * 2
            expanded_h = bg_for_logo.height + margin * 2
            logo_with_margin = Image.new("RGBA", (expanded_w, expanded_h), bg_rgb + (255,))
            logo_with_margin.paste(bg_for_logo, (margin, margin), bg_for_logo)

            # (E) Paste the logo_with_margin in the center of the QR code
            lw, lh = logo_with_margin.size
            pos = (
                (qr_width - lw) // 2,  # center horizontally
                (qr_height - lh) // 2  # center vertically
            )
            img_qr.paste(logo_with_margin, pos, logo_with_margin)

        # 3. Round the corners of the entire QR code
        if border_radius > 0:
            width, height = img_qr.size
            mask_qr = Image.new("L", (width, height), 0)
            draw_qr = ImageDraw.Draw(mask_qr)
            draw_qr.rounded_rectangle((0, 0, width, height), radius=border_radius, fill=255)
            img_qr.putalpha(mask_qr)

        return img_qr


def generate_qr_code(request):
    qr_image_base64 = None

    if request.method == "POST":
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_image = form.generate_qr()

            # Convert the Pillow image to PNG bytes, then base64-encode
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    else:
        form = QRCodeForm()

    return render(
        request,
        "qr_code/qr_code_form.html",
        {"form": form, "qr_image_base64": qr_image_base64},
    )
