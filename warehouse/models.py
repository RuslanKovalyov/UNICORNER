from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Category name (e.g., Raw Materials, Coffee, Office Supplies)")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Stock(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('pack', 'Pack'),
        ('box', 'Box'),
        ('bag', 'Bag'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='stocks')
    
    # Stock information
    current_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    minimum_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Price per unit in ₪ (Israeli Shekels)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    needs_reorder = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = ['name', 'supplier']

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

    def save(self, *args, **kwargs):
        # Auto-update needs_reorder based on current vs minimum quantity
        self.needs_reorder = self.current_quantity <= self.minimum_quantity
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        if self.current_quantity is not None and self.unit_price is not None:
            return self.current_quantity * self.unit_price
        return 0

    @property
    def stock_status(self):
        if self.current_quantity <= 0:
            return "Out of Stock"
        elif self.needs_reorder:
            return "Low Stock"
        else:
            return "In Stock"
