from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from warehouse.models import Supplier, Category, Stock
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample data for warehouse testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample suppliers
        suppliers_data = [
            {
                'name': 'Coffee Beans Wholesale',
                'contact_person': 'John Smith',
                'email': 'orders@coffeebeans.com',
                'phone': '+1-555-0123',
                'address': '123 Coffee Street, Bean City, BC 12345'
            },
            {
                'name': 'Office Supply Co.',
                'contact_person': 'Sarah Johnson',
                'email': 'sales@officesupply.com',
                'phone': '+1-555-0456',
                'address': '456 Business Ave, Office Town, OT 67890'
            },
            {
                'name': 'Kitchen Equipment Ltd.',
                'contact_person': 'Mike Wilson',
                'email': 'info@kitchenequip.com',
                'phone': '+1-555-0789',
                'address': '789 Kitchen Blvd, Equipment City, EC 11111'
            }
        ]

        suppliers = []
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults=supplier_data
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'  Created supplier: {supplier.name}')

        # Create sample stock items
        stock_items = [
            # Coffee items
            {
                'name': 'Arabica Coffee Beans',
                'description': 'Premium arabica coffee beans from Colombia',
                'category': 'coffee',
                'supplier': suppliers[0],
                'current_quantity': Decimal('50.0'),
                'minimum_quantity': Decimal('10.0'),
                'unit': 'kg',
                'unit_price': Decimal('25.50')
            },
            {
                'name': 'Robusta Coffee Beans',
                'description': 'Strong robusta coffee beans from Vietnam',
                'category': 'coffee',
                'supplier': suppliers[0],
                'current_quantity': Decimal('30.0'),
                'minimum_quantity': Decimal('15.0'),
                'unit': 'kg',
                'unit_price': Decimal('18.75')
            },
            {
                'name': 'Coffee Filters',
                'description': 'Paper coffee filters, size 4',
                'category': 'consumables',
                'supplier': suppliers[0],
                'current_quantity': Decimal('500.0'),
                'minimum_quantity': Decimal('100.0'),
                'unit': 'pcs',
                'unit_price': Decimal('0.05')
            },
            # Office supplies
            {
                'name': 'Paper Cups 8oz',
                'description': 'Disposable paper cups for coffee',
                'category': 'consumables',
                'supplier': suppliers[1],
                'current_quantity': Decimal('2000.0'),
                'minimum_quantity': Decimal('500.0'),
                'unit': 'pcs',
                'unit_price': Decimal('0.08')
            },
            {
                'name': 'Napkins',
                'description': 'Coffee shop napkins',
                'category': 'consumables',
                'supplier': suppliers[1],
                'current_quantity': Decimal('1000.0'),
                'minimum_quantity': Decimal('200.0'),
                'unit': 'pack',
                'unit_price': Decimal('2.50')
            },
            # Equipment & raw materials
            {
                'name': 'Milk',
                'description': 'Fresh whole milk for coffee drinks',
                'category': 'raw_materials',
                'supplier': suppliers[2],
                'current_quantity': Decimal('20.0'),
                'minimum_quantity': Decimal('10.0'),
                'unit': 'l',
                'unit_price': Decimal('1.25')
            },
            {
                'name': 'Sugar Packets',
                'description': 'Individual sugar packets',
                'category': 'consumables',
                'supplier': suppliers[1],
                'current_quantity': Decimal('800.0'),
                'minimum_quantity': Decimal('200.0'),
                'unit': 'pcs',
                'unit_price': Decimal('0.02')
            },
            # Low stock items for testing
            {
                'name': 'Cleaning Supplies',
                'description': 'All-purpose cleaner for coffee equipment',
                'category': 'cleaning',
                'supplier': suppliers[2],
                'current_quantity': Decimal('2.0'),  # Below minimum
                'minimum_quantity': Decimal('5.0'),
                'unit': 'l',
                'unit_price': Decimal('8.50')
            }
        ]

        for item_data in stock_items:
            category = Category.objects.get(name=item_data['category'])
            stock, created = Stock.objects.get_or_create(
                name=item_data['name'],
                supplier=item_data['supplier'],
                defaults={
                    **item_data,
                    'category': category
                }
            )
            if created:
                self.stdout.write(f'  Created stock item: {stock.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('You can now:')
        self.stdout.write('  - Visit /warehouse/ to see the dashboard')
        self.stdout.write('  - Check /warehouse/reorder/ for low stock items')
        self.stdout.write('  - Manage everything via /admin/')
