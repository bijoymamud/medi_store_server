# MediShop - Backend Server Documentation

Welcome to the backend developer documentation for the **MediShop** FastAPI server. This project provides a robust RESTful API leveraging PostgreSQL for data storage, JWT token-based authentication, SSLCommerz payment integration, and background task processing.

---

## 🚀 Architecture & Modules

The server is organized as a modular FastAPI project. Each feature area is structured under the `src/modules/` directory with separate routers, models, schemas, and helpers.

### Technology Stack
*   **Web Framework**: FastAPI (Asynchronous Python)
*   **Database ORM**: SQLAlchemy 2.0
*   **Database Migration**: Automatic startup schema validation and raw SQL migrations
*   **Authentication**: Password hashing via passlib (bcrypt) and double JWT tokens (Access and Refresh)
*   **Payment Gateway**: SSLCommerz IPN (Instant Payment Notification)

---

## 📂 Codebase Directory Structure

*   `src/modules/`
    *   `auth/`
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/auth/router.py): Handles signup, token creation, refresh session validation, and logout.
    *   `users/`
        *   [models.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/users/models.py): Declares the `User` model, featuring active state control (`is_active` column).
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/users/router.py): CRUD endpoints for user records, including admin actions like user list, active toggle (blocking), and bulk user deletion.
    *   `products/`
        *   [models.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/products/models.py): Declares the `Product` model, containing the confidential `purchase_amount` property.
        *   [schemas.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/products/schemas.py): Holds Pydantic validation schemas. Confidential properties are restricted to `AdminProductResponse`, while public endpoints use `ProductResponse` to omit cost data.
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/products/router.py): Endpoints to search products, CRUD products, and fetch admin list representations.
    *   `categories/`
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/categories/router.py): CRUD operations for categories grouping.
    *   `cart/`
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/cart/router.py): Shopping cart operations synced with the database.
    *   `orders/`
        *   [models.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/orders/models.py): Declares `Order` and `OrderItem` models.
        *   [router.py](file:///d:/Bijoy/MediShop/medistore-server/src/modules/orders/router.py): Handles checkouts, SSLCommerz redirection, validation, review verifications, and real-time dashboard analytics calculation.
*   `src/database/`
    *   [connection.py](file:///d:/Bijoy/MediShop/medistore-server/src/database/connection.py): SQLAlchemy engine setup and database session dependency injectors (`get_db`).
*   `src/utils/`
    *   [dependencies.py](file:///d:/Bijoy/MediShop/medistore-server/src/utils/dependencies.py): Security dependencies (`get_current_user`, `get_admin_user`) for endpoint protection.
    *   [email_sender.py](file:///d:/Bijoy/MediShop/medistore-server/src/utils/email_sender.py): Verification code and email dispatch helper.
*   `src/main.py`
    *   Main entry point starting the FastAPI app, registering routers, configuring CORS, and performing startup table schema auto-migrations.

---

## 🏗️ Phase Implementations & Database Schemas

We recently introduced several enhancements to enable purchase cost tracking and improve administration tools:

1.  **DB Auto-Migrations on Startup**:
    *   Main startup logic (`src/main.py`) checks and alters tables on the fly.
    *   Runs `ALTER TABLE products ADD COLUMN IF NOT EXISTS purchase_amount DOUBLE PRECISION DEFAULT 0.0` to ensure legacy product rows are upgraded without manual migration.
2.  **Confidential Product Pricing**:
    *   We added the `purchase_amount` field inside `ProductCreate` and `ProductUpdate` schemas.
    *   Guest users request products through `/api/v1/products/all_products/` which returns `ProductResponse` schema (omitting purchase amount).
    *   Admin users retrieve products through `/api/v1/products/admin/all` and `/admin/{product_id}` which returns `AdminProductResponse` (retaining purchase amount).
3.  **Client Controls (Block/Unblock/Delete)**:
    *   Admin endpoints are secured via `get_admin_user` dependency.
    *   `POST /api/v1/users/{user_id}/toggle-active` toggles the database `is_active` column.
    *   `DELETE /api/v1/users/{user_id}` and `POST /api/v1/users/admin/bulk-delete` deletes individual or groups of users from the platform.
    *   Blocked users (`is_active = False`) are prevented from logging in or requesting fresh tokens inside auth controllers.
4.  **Admin Business Analytics**:
    *   Added the `GET /api/v1/orders/admin/analytics` endpoint.
    *   It calculates real-time metrics in a single request:
        *   `total_revenue`: Aggregate sum of paid or completed orders.
        *   `total_orders`: Count of all order checkouts.
        *   `total_running_orders`: Orders with status `pending` or `on_route`.
        *   `total_investment`: Calculates overall investment based on cost values (`current_stock * purchase_amount + quantity_sold * purchase_amount`).

---

## 💻 Running the Server

To start the server locally:

1.  Configure the `.env` environment variables (database connection, SMTP credentials, SSLCommerz keys).
2.  Run the reload server using:
    ```bash
    # Install Python packages (ensure virtual environment is active if preferred)
    pip install -r requirements.txt

    # Run FastAPI local server
    uvicorn src.main:app --reload
    ```
3.  Execute backend tests suite:
    ```bash
    python -m pytest
    ```
