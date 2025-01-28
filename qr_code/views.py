from django.shortcuts import render
from django import forms
import qrcode
from qrcode.image.pil import PilImage
from qrcode.constants import ERROR_CORRECT_H
from io import BytesIO
import base64
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from urllib.parse import urlparse
import re
from PIL import Image, ImageDraw, ImageColor, ImageOps
from django.conf import settings

IMAGE_PATH = f"{settings.STATIC_ROOT}/main/images/logo/logo-dark.png"


class QRCodeForm(forms.Form):
    url = forms.CharField(
        label="Enter URL",
        widget=forms.TextInput(attrs={"placeholder": "Enter URL here..."})
    )
    bg_color = forms.CharField(
        label="Background Color",
        widget=forms.TextInput(attrs={"type": "color", "value": "#ffff00"})
    )
    fill_color = forms.CharField(
        label="Fill Color",
        widget=forms.TextInput(attrs={"type": "color", "value": "#300030"})
    )
    border_radius = forms.IntegerField(
        label="Border Radius (pixels)",
        initial=20,
        min_value=0,
        max_value=100
    )
    unuse_image = forms.BooleanField(
        label="Remove Logo",
        required=False
    )

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        parsed_url = urlparse(url)

        # If no scheme, prepend http://
        if not parsed_url.scheme:
            url = f"http://{url}"

        # Validate URL
        validator = URLValidator(schemes=["http", "https"])
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL. Please enter a valid URL. Example: https://example.com")

        # Optional: Disallow suspicious characters
        if re.search(r'[\'";]', url):
            raise ValidationError("Invalid URL: contains potentially dangerous characters.")

        return url

    def generate_qr(self):
        """
        1. Generate a black-and-white QR code (PilImage).
        2. Manually recolor black->fill_color, white->bg_color.
        3. Embed the logo (optionally recolor the logo if desired).
        4. Apply rounded corners to the entire image if needed.
        """
        url = self.cleaned_data["url"]
        bg_hex = self.cleaned_data["bg_color"]
        fill_hex = self.cleaned_data["fill_color"]
        border_radius = self.cleaned_data["border_radius"]
        unuse_image = self.cleaned_data["unuse_image"]

        # Convert user-chosen hex color to RGB
        bg_rgb = ImageColor.getrgb(bg_hex)
        fill_rgb = ImageColor.getrgb(fill_hex)

        # 1. Create a BLACK-and-WHITE QR Code (no color mask!)
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # By default, fill_color="black", back_color="white"
        # We'll override them manually AFTER we get the B/W image.
        img_qr_bw = qr.make_image(
            image_factory=PilImage,
            fill_color="black",
            back_color="white"
        ).convert("RGBA")

        # 2. Manually recolor each pixel: black -> fill_rgb, white -> bg_rgb
        width, height = img_qr_bw.size
        pixels = img_qr_bw.load()

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if r < 128 and g < 128 and b < 128:
                    pixels[x, y] = fill_rgb + (255,)
                else:
                    pixels[x, y] = bg_rgb + (255,)

        # 3. (Optional) Embed the logo
        if not unuse_image:
            logo = Image.open(IMAGE_PATH).convert("RGBA")
            alpha_channel = logo.getchannel("A")
            logo_gray = logo.convert("L")
            logo_colorized = ImageOps.colorize(
                logo_gray,
                black=fill_hex,
                white=fill_hex
            )
            logo_colorized.putalpha(alpha_channel)

            bg_for_logo = Image.new("RGBA", logo_colorized.size, bg_rgb + (255,))
            bg_for_logo.paste(logo_colorized, mask=logo_colorized)

            qr_width, qr_height = img_qr_bw.size
            max_logo_width = qr_width * 0.20
            if bg_for_logo.width > max_logo_width:
                ratio = max_logo_width / float(bg_for_logo.width)
                new_size = (int(bg_for_logo.width * ratio), int(bg_for_logo.height * ratio))
                bg_for_logo = bg_for_logo.resize(new_size, Image.LANCZOS)

            margin = 10
            expanded_w = bg_for_logo.width + margin * 2
            expanded_h = bg_for_logo.height + margin * 2
            logo_with_margin = Image.new("RGBA", (expanded_w, expanded_h), bg_rgb + (255,))
            logo_with_margin.paste(bg_for_logo, (margin, margin), bg_for_logo)

            lw, lh = logo_with_margin.size
            center_x = (qr_width - lw) // 2
            center_y = (qr_height - lh) // 2
            img_qr_bw.paste(logo_with_margin, (center_x, center_y), logo_with_margin)

        # 4. Round the corners if border_radius > 0
        if border_radius > 0:
            mask_qr = Image.new("L", (width, height), 0)
            draw_qr = ImageDraw.Draw(mask_qr)
            draw_qr.rounded_rectangle((0, 0, width, height), radius=border_radius, fill=255)
            img_qr_bw.putalpha(mask_qr)

        return img_qr_bw


def generate_qr_code(request):
    qr_image_base64 = None

    if request.method == "POST":
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_image = form.generate_qr()
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
