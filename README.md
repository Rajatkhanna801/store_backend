# 🛍️ Django E-Commerce Store

A comprehensive e-commerce platform built with Django REST Framework, featuring advanced inventory management, cart system, order processing, and a powerful admin interface.

## 🚀 Features

### ✨ Core E-Commerce Features
- **Product Management** - Categories, products with images, pricing, and inventory
- **Shopping Cart** - User-specific cart with item management
- **Order Processing** - Complete order lifecycle with checkout system
- **User Management** - Authentication, profiles, and address management
- **Payment Integration** - UPI payment data generation for orders

### 🔐 Authentication & Security
- **JWT Authentication** - Secure API access with refresh tokens
- **User Registration & Login** - Complete user account management
- **Address Management** - Multiple shipping addresses per user
- **Admin-Only Operations** - Sensitive operations restricted to admin panel

### 📱 Advanced Features
- **Temporary Checkout System** - 10-minute item reservation with auto-expiry
- **Inventory Management** - Real-time stock tracking and validation
- **Cron Jobs** - Automated cleanup of expired checkouts
- **Pagination** - Efficient data handling for large datasets
- **Swagger Documentation** - Complete API documentation with examples

## 🏗️ Project Structure

```
StoreBackend/
├── account/           # User management and authentication
├── cart/             # Shopping cart functionality
├── inventory/        # Product and category management
├── order/            # Order processing and checkout
├── StoreBackend/     # Main project settings and configuration
├── media/            # User-uploaded files (product images)
├── requirements.txt  # Python dependencies
└── manage.py         # Django management script
```

## 🛠️ Technology Stack

- **Backend**: Django 5.2.5 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: DRF Spectacular (Swagger/OpenAPI)
- **Image Processing**: Pillow (PIL)
- **Task Scheduling**: django-crontab
- **Development**: Python 3.11+

## 📋 Requirements

### System Requirements
- Python 3.11+
- pip (Python package manager)
- Git

### Python Dependencies
```
Django==5.2.5
djangorestframework==3.16.1
djangorestframework-simplejwt==5.5.1
drf-spectacular==0.28.0
django-crontab==0.7.1
Pillow==11.3.0
django-filter==25.1
```

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd store
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
cd StoreBackend
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the `StoreBackend` directory:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Checkout Configuration
CHECKOUT_EXPIRY_HOURS=2

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### Cron Job Setup
```bash
# Add cron jobs
python manage.py crontab add

# List active cron jobs
python manage.py crontab show

# Remove cron jobs
python manage.py crontab remove
```

## 🎯 Admin Panel Features

### 👑 User Management (`/admin/account/user/`)
- **User List View**
  - ID, username, email, full name
  - Active status, staff status, superuser status
  - Date joined, last login
  - Order count, cart count
  - Address count

- **User Actions**
  - Mark users as active/inactive
  - Promote/demote staff status
  - Bulk user operations

- **User Details**
  - Personal information
  - Account settings
  - Related orders and cart
  - Address management

### 🏠 Address Management (`/admin/account/address/`)
- **Address List View**
  - User information
  - Address details (street, city, state, pincode)
  - Default address status
  - Address label (home, work, etc.)
  - Creation date

- **Address Actions**
  - Set default address
  - Bulk address operations
  - Address validation

### 🛒 Cart Management (`/admin/cart/cart/`)
- **Cart List View**
  - Cart ID and user information
  - Items count with color coding
  - Total amount display
  - Creation and update timestamps

- **Cart Inline Items**
  - Product information (ID, name)
  - Quantity and status
  - Total price calculation
  - Add/remove items

- **Cart Actions**
  - Clear all cart items
  - Mark items as saved for later
  - Bulk cart operations

### 📦 Product Management (`/admin/inventory/product/`)
- **Product List View**
  - Product ID, name, category
  - Price displays (base, discounted, effective)
  - Stock quantity with color coding
  - Status indicators
  - Creation timestamps

- **Product Details**
  - Basic information
  - Pricing management
  - Inventory tracking
  - Image management
  - Category assignment

- **Product Actions**
  - Mark as in/out of stock
  - Apply/remove discounts
  - Bulk product operations

### 🏷️ Category Management (`/admin/inventory/category/`)
- **Category List View**
  - Category ID, name, description preview
  - Products count
  - Creation timestamps

- **Category Actions**
  - Merge categories
  - Bulk category operations

### 📋 Order Management (`/admin/order/order/`)
- **Order List View**
  - Order ID, user information
  - Status with color coding
  - Payment status with color coding
  - Total amount display
  - Items count
  - Shipping address
  - Creation date

- **Order Details**
  - Order information
  - Shipping details
  - Payment management (admin only)
  - Order items inline
  - Timestamps

- **Order Actions**
  - Mark payment as paid/failed/refunded
  - Update order status
  - Regenerate payment data
  - Bulk order operations

### 🛍️ Checkout Management (`/admin/order/checkout/`)
- **Checkout List View**
  - Checkout ID, user information
  - Shipping address
  - Items count
  - Expiration time
  - Time remaining display
  - Status indicators
  - Creation date

- **Checkout Details**
  - Checkout information
  - Expiration settings
  - Checkout items inline
  - Timestamps

- **Checkout Actions**
  - Mark as expired
  - Extend checkout time
  - Delete expired checkouts

## 🌐 API Endpoints

### 🔐 Authentication
```
POST /api/auth/register/          # User registration
POST /api/auth/login/             # User login
POST /api/auth/refresh/           # Refresh JWT token
POST /api/auth/password/change/   # Change password
```

### 👤 User Management
```
GET    /api/users/profile/        # Get user profile
PUT    /api/users/profile/        # Update user profile
GET    /api/users/addresses/      # List user addresses
POST   /api/users/addresses/      # Create new address
GET    /api/users/addresses/{id}/ # Get specific address
PUT    /api/users/addresses/{id}/ # Update address
DELETE /api/users/addresses/{id}/ # Delete address
```

### 🛍️ Products & Categories
```
GET /api/products/                # List products (paginated)
GET /api/products/{id}/           # Get specific product
GET /api/categories/              # List categories (paginated)
GET /api/categories/{id}/         # Get specific category
GET /api/products/category/{id}/  # Get products by category
```

### 🛒 Shopping Cart
```
GET    /api/cart/                 # Get user's cart
POST   /api/cart/add/             # Add item to cart
PATCH  /api/cart/items/{id}/update/ # Update cart item
DELETE /api/cart/items/{id}/remove/ # Remove cart item
```

### 📋 Orders & Checkout
```
POST   /api/checkout/create/      # Create temporary checkout
GET    /api/checkout/{id}/        # Get checkout details
DELETE /api/checkout/{id}/cancel/ # Cancel checkout
POST   /api/orders/create/        # Create order from checkout
GET    /api/orders/               # List user orders
GET    /api/orders/{id}/          # Get order details
GET    /api/orders/{id}/summary/  # Get order summary
```

## 🔒 Security Features

### Admin-Only Operations
- **Payment Status Changes** - Only admins can modify payment status
- **Order Status Updates** - Admin controls order lifecycle
- **User Management** - Admin controls user accounts and permissions
- **Inventory Management** - Admin controls product availability and pricing

### API Security
- **JWT Authentication** - Secure token-based authentication
- **Permission Classes** - Role-based access control
- **Input Validation** - Comprehensive data validation
- **SQL Injection Protection** - Django ORM security

## 📊 Data Models

### Core Models
- **User** - Extended user model with profile information
- **Address** - User shipping addresses
- **Category** - Product categories
- **Product** - Products with images and pricing
- **Cart** - User shopping carts
- **CartItem** - Items within carts
- **Checkout** - Temporary order reservations
- **CheckoutItem** - Items in temporary checkouts
- **Order** - Completed orders
- **OrderItem** - Items within orders

### Key Relationships
- **User** → **Cart** (One-to-One)
- **User** → **Addresses** (One-to-Many)
- **User** → **Orders** (One-to-Many)
- **Category** → **Products** (One-to-Many)
- **Cart** → **CartItems** (One-to-Many)
- **Checkout** → **CheckoutItems** (One-to-Many)
- **Order** → **OrderItems** (One-to-Many)

## 🚀 Advanced Features

### Temporary Checkout System
- **10-minute item reservation** - Prevents overselling
- **Automatic expiry** - Items return to inventory
- **Configurable timeout** - Environment variable control
- **Cron job cleanup** - Automated maintenance

### Inventory Management
- **Real-time stock tracking** - Accurate inventory levels
- **Stock validation** - Prevents orders exceeding stock
- **Low stock alerts** - Visual indicators in admin
- **Stock updates** - Automatic inventory management

### Payment Integration
- **UPI payment data** - Indian payment system support
- **Payment status tracking** - Complete payment lifecycle
- **Admin payment control** - Secure payment management
- **Payment data generation** - Automatic UPI data creation

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test account
python manage.py test cart
python manage.py test inventory
python manage.py test order
```

### Test Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🚀 Deployment

### Production Settings
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Environment Variables
```env
# Production
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@host:port/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📚 API Documentation

### Swagger UI
Access the interactive API documentation at:
```
http://localhost:8000/api/docs/
```

### OpenAPI Schema
Download the complete API schema at:
```
http://localhost:8000/api/schema/
```

## 🔧 Management Commands

### Available Commands
```bash
# Cleanup expired checkouts
python manage.py cleanup_expired_checkouts

# Fix order prices (for data integrity)
python manage.py fix_order_prices

# Add cron jobs
python manage.py crontab add

# List cron jobs
python manage.py crontab show
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Update documentation
6. Submit a pull request

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues
- **Admin login problems** - Check JWT middleware configuration
- **Migration errors** - Ensure all dependencies are installed
- **API authentication** - Verify JWT token format and expiration
- **Image upload issues** - Check media directory permissions

### Getting Help
- Check the API documentation at `/api/docs/`
- Review the admin panel for data validation
- Check Django logs for detailed error messages
- Ensure all environment variables are set correctly

## 🎉 Acknowledgments

- Django community for the excellent framework
- Django REST Framework for powerful API tools
- DRF Spectacular for comprehensive API documentation
- All contributors to the open-source packages used

---

**Built with ❤️ using Django and modern web technologies**
