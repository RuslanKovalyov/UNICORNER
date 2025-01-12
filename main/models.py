from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
from colorthief import ColorThief
import os
from io import BytesIO


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/images/")
    background_color = models.CharField(max_length=7, blank=True, null=True)  # Store as HEX background color for the product card
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
    # sort by latest
    class Meta:
        ordering = ["-id"]
    
    def save(self, *args, **kwargs):
        # Delete the old image if a new image is being uploaded
        if self.pk:
            try:
                old_image = Product.objects.get(pk=self.pk).image
                if old_image and self.image != old_image:
                    if os.path.isfile(old_image.path):
                        os.remove(old_image.path)
            except Product.DoesNotExist:
                pass
            
        # Resize and save the image in JPEG format
        if self.image:
            img = Image.open(self.image)
            
            # Automatically fix orientation
            img = ImageOps.exif_transpose(img)

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize the image if larger than 1000x1000
            max_size = (1000, 1000)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save the resized image back to the field
            img_io = BytesIO()
            img.save(img_io, format="JPEG", quality=90)
            img_name = os.path.splitext(self.image.name)[0] + ".jpg"  # Ensure .jpg extension
            self.image = ContentFile(img_io.getvalue(), name=img_name)
        
        super().save(*args, **kwargs)
        
        # Calculate the dominant color of background from the image after saving
        # if color is not already exist
        if not self.background_color:
            if self.image and os.path.isfile(self.image.path):
                color_thief = ColorThief(self.image.path)
                dominant_color = color_thief.get_color(quality=1)  # Returns RGB tuple
                
                # Ensure the background color is dark
                saturated_color = self._enhance_saturation(dominant_color)
                adjusted_color = self._ensure_darker_color(saturated_color)
                self.background_color = "#{:02x}{:02x}{:02x}".format(*adjusted_color)
                
                # Save the model again to store the dominant color
                super().save(update_fields=["background_color"])  # Avoid full save
    
    def _enhance_saturation(self, color, factor=10):
        """
        Enhance the saturation of an RGB color.
        """
        avg = sum(color) / 3
        enhanced_color = tuple(
            max(min(int(avg + (c - avg) * factor), 255), 0) for c in color
        )
        return enhanced_color
     
    def _ensure_darker_color(self, color):
        """
        Adjust the color to ensure it's darker than a given brightness threshold.
        """
        threshold = 150  # Brightness threshold
        brightness = sum(color) / 3  # Calculate brightness as average of RGB
        if brightness > threshold:
            # Darken the color
            color = tuple(max(int(c * 0.6), 0) for c in color)  # Reduce brightness by 40%
        return color

    def delete(self, *args, **kwargs):
        # Delete the image file from storage before deleting the object
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        # Call the parent class delete method
        super().delete(*args, **kwargs)

# Signal to delete the image when a Product instance is deleted
@receiver(post_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)