from django import forms
from django.forms import modelformset_factory
from .models import Category, Stock


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Raw Materials, Coffee Beans, Office Supplies',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Optional description of this category...',
                'rows': 3,
                'class': 'form-control'
            })
        }
        help_texts = {
            'name': 'Enter a unique category name. You can create any category you need.',
        }


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make category field show all categories in a nice way
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = "Select a category"


class StockQuantityForm(forms.ModelForm):
    """Form for inline editing of stock quantities"""
    class Meta:
        model = Stock
        fields = ['current_quantity']
        widgets = {
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm stock-quantity-input',
                'style': 'width: 90px; text-align: center;',
                'step': '1',
                'min': '0'
            })
        }


# Create a formset for bulk editing stock quantities
StockQuantityFormSet = modelformset_factory(
    Stock, 
    form=StockQuantityForm, 
    extra=0,
    can_delete=False
)
