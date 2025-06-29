#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/ruslan/Desktop/UNICORNER')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unicorner.settings')

# Setup Django
django.setup()

from warehouse.models import Stock

def test_warehouse_models():
    print("Testing warehouse models...")
    
    # Test if we can query stocks
    try:
        stocks = Stock.objects.all()
        print(f"Found {stocks.count()} stock items")
        
        for stock in stocks[:3]:  # Show first 3
            print(f"- {stock.name}: {stock.current_quantity} {stock.get_unit_display()}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_warehouse_models()
