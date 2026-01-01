# E-Commerce Backend (Django + DRF)

## Overview

A modular Django REST Framework backend for an e-commerce application. Includes user authentication, product inventory, cart management, and order handling with QR-based payment confirmation.

## Project Structure

```
StoreBackend/
├── account/        # User auth + profile + addresses
├── cart/           # Cart + cart items + save-for-later
├── inventory/      # Products, categories, product images
├── order/          # Orders + order items + payment flow
├── StoreBackend/   # Main Django project config
├── manage.py
└── requirements.txt
```

## Tech Stack

- **Backend**: Django 5.x, Django REST Framework
- **API Docs**: drf-spectacular (Swagger UI, ReDoc)
- **Auth**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (development)
- **Filtering**: django-filter

## Running the Application

The Django development server runs on port 5000:
```bash
cd StoreBackend && python manage.py runserver 0.0.0.0:5000
```

## API Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## Key API Endpoints

### Accounts
- `POST /api/accounts/register/` - Register new user
- `POST /api/accounts/login/` - Login user
- `GET /api/accounts/me/` - Get profile
- `PUT /api/accounts/me/` - Update profile
- `GET/POST /api/accounts/addresses/` - Manage addresses

### Inventory
- `GET /api/inventory/products/` - List products (supports filtering, sorting, pagination)
- `GET /api/inventory/products/{id}/` - Product details
- `GET /api/inventory/categories/` - List categories
- `GET /api/inventory/banners/` - List active banners for mobile app display

### Cart
- `GET /api/cart/` - View cart
- `POST /api/cart/add/` - Add to cart
- `PATCH /api/cart/item/{id}/` - Update cart item
- `DELETE /api/cart/item/{id}/` - Remove item

### Orders
- `POST /api/orders/checkout/` - Create order from cart
- `GET /api/orders/` - List user orders
- `GET /api/orders/{id}/` - Order details

## Recent Changes

- 2026-01-01: Added Banner API for mobile app
  - Created Banner model with mobile-friendly deep linking (link_type + link_value)
  - Added `/api/inventory/banners/` endpoint for displaying promotional offers
  - Banners support scheduling with start_date/end_date and priority ordering
  - Django Admin interface for managing banners

- 2026-01-01: Initial Replit setup
  - Installed Python 3.11 and dependencies
  - Fixed static/media file paths for Replit environment
  - Created database migrations
  - Configured workflow to run on port 5000
