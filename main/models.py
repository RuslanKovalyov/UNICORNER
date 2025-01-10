from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
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
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
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