🛍️ E-Commerce Backend (Django + DRF)

This is a modular Django + Django REST Framework project that provides the backend for an e-commerce application.
It includes user authentication, product inventory, cart management, and order handling with QR-based payment confirmation.

📂 Project Structure
project_root/
│
├── accounts/      # User auth + profile + addresses
├── inventory/     # Products, categories, product images
├── cart/          # Cart + cart items + save-for-later
├── orders/        # Orders + order items + payment flow
├── project/       # Main Django project config
└── requirements.txt

⚡ Features

Accounts

User registration, login, logout, forgot/reset password

Manage profile & multiple addresses

Inventory

Product catalog with categories & multiple images

Filtering, sorting, and pagination

Admin manages inventory (via Django Admin)

Cart

Add/update/remove items

Save for later (Amazon-style) and move back to active cart

Orders

Checkout cart → create order

Generate QR code for payment

Admin manually verifies payment status

API Docs

Swagger UI (/swagger/)

ReDoc (/redoc/)

🛠️ Installation

Clone the repo

git clone https://github.com/your-username/ecommerce-backend.git
cd ecommerce-backend


Create virtual environment

python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt


Apply migrations

python manage.py migrate


Create superuser (for admin access)

python manage.py createsuperuser


Run development server

python manage.py runserver


Server will start on: http://127.0.0.1:8000/

📜 API Documentation

Swagger UI → http://127.0.0.1:8000/swagger/

ReDoc → http://127.0.0.1:8000/redoc/

OpenAPI Schema JSON → http://127.0.0.1:8000/swagger.json

🔑 API Endpoints Overview
Accounts

POST /api/accounts/register/ → Create new user

POST /api/accounts/login/ → Login user

POST /api/accounts/logout/ → Logout

POST /api/accounts/password/forgot/ → Send reset link/OTP

POST /api/accounts/password/reset/ → Reset password

GET /api/accounts/me/ → Get profile

PUT /api/accounts/me/ → Update profile

GET /api/accounts/addresses/ → List addresses

POST /api/accounts/addresses/ → Add address

PUT /api/accounts/addresses/{id}/ → Update address

DELETE /api/accounts/addresses/{id}/ → Delete address

Inventory

GET /api/products/ → Get product list

Query params:

category (filter by category id or slug)

price_min, price_max (filter by price range)

sort (values: price_asc, price_desc, latest)

page, page_size (pagination)

GET /api/products/{id}/ → Get product details

GET /api/categories/ → List categories

Cart

GET /api/cart/ → View user cart (active + saved items)

POST /api/cart/add/ → Add product to cart

PATCH /api/cart/item/{id}/ → Update cart item (qty, status)

DELETE /api/cart/item/{id}/ → Remove cart item

Orders

POST /api/orders/checkout/ → Place order from cart

GET /api/orders/ → List user orders

GET /api/orders/{id}/ → Get order details

🔧 Tech Stack

Backend: Django 5.x, Django REST Framework

API Docs: drf-yasg (Swagger / OpenAPI docs)

Filtering: django-filter

Media: Pillow (image handling)

Database: SQLite (dev) / PostgreSQL (prod ready)

🚀 Next Steps

Integrate real payment gateway (Razorpay/Stripe/UPI API)

Add unit tests with pytest or Django TestCase

Dockerize project for deployment

Deploy to production (Heroku, AWS, DigitalOcean, etc.)

👨‍💻 Author

Built with ❤️ using Django & DRF.