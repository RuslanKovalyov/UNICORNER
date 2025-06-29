# Warehouse Management System

## Security & Access Control

The warehouse management system is designed with security in mind. Access is restricted to authorized personnel only.

### Access Levels

1. **Regular Users**: Can access the main website but NOT the warehouse
2. **Managers (Staff)**: Can access both the main website AND the warehouse system
3. **Administrators (Superusers)**: Full access to everything including Django admin

### How to Grant Warehouse Access

#### Option 1: Using Django Admin (Recommended)
1. Go to `/admin/` and log in as an administrator
2. Navigate to "Users" in the admin panel
3. Select the user you want to grant access to
4. Check the "Staff status" checkbox
5. Save the user

#### Option 2: Using Custom Admin Actions
1. Go to `/admin/auth/user/`
2. Select the users you want to grant access to
3. Choose "Grant warehouse access (make staff)" from the Actions dropdown
4. Click "Go"

#### Option 3: Using Management Command
```bash
python manage.py create_manager username email@example.com
```

### How the Security Works

1. **Middleware Protection**: `WarehouseAuthenticationMiddleware` checks all `/warehouse/` URLs
2. **View Decorators**: Each warehouse view is protected with `@staff_required`
3. **Template Conditionals**: Warehouse navigation only shows for staff users

### Access Denied Handling

If a non-staff user tries to access `/warehouse/`, they will be:
1. Redirected to the admin login page
2. After login, if they're still not staff, they'll see an access denied page

## Features

### Dashboard
- Overview of inventory statistics
- Quick access to suppliers and categories
- Summary cards showing stock levels

### Suppliers Management
- Add/edit supplier information
- View all stock items by supplier
- Contact information management

### Stock Management
- Track inventory levels
- Set minimum stock thresholds
- Automatic reorder notifications
- Price and value tracking

### Reorder Management
- Automatic low stock detection
- Reorder list grouped by supplier
- Print-friendly format for ordering

## Getting Started

1. **Set Up Categories**: You can create any categories you need for your business
   - Default categories included: Raw Materials, Consumables, Coffee, Office Supplies, Cleaning Supplies, Other
   - Add new categories via `/admin/warehouse/category/add/`
   - Categories are free-form text - create whatever makes sense for your business
2. **Add Suppliers**: Add your suppliers with contact information
3. **Add Stock Items**: Create inventory items linked to suppliers and categories
4. **Set Minimum Levels**: Configure minimum stock thresholds for automatic reorder alerts

## URL Structure

- `/warehouse/` - Dashboard
- `/warehouse/suppliers/` - Supplier list
- `/warehouse/suppliers/<id>/` - Supplier detail with their stock items
- `/warehouse/stocks/` - All stock items with filtering
- `/warehouse/reorder/` - Items needing reorder

## Admin Integration

The warehouse models are fully integrated with Django admin:
- Bulk actions for marking items for reorder
- Advanced filtering and searching
- Editable list views for quick updates
- Read-only calculated fields (stock status, total value)

## Security Best Practices

1. Only grant staff status to trusted personnel
2. Regularly review user permissions
3. Use strong passwords for manager accounts
4. Consider enabling two-factor authentication for admin accounts
5. Monitor access logs for unusual activity

## Troubleshooting

### "Access Denied" Error
- Check if the user has staff status in admin
- Ensure the user is logged in
- Verify the warehouse middleware is enabled in settings

### Navigation Not Showing Warehouse Link
- User must be logged in AND have staff status
- Check if the navbar template includes the warehouse conditional

### Permission Errors in Admin
- Ensure the custom UserAdmin is properly registered
- Check that the warehouse app is in INSTALLED_APPS
