# Backend Development Plan (MediStore)

## Project Analysis

### Required Backend Features
* **User Management**: Registration, login, profile management.
* **Authentication & Security**: JWT-based auth, email verification, OTP verification, password reset.
* **Product Catalog**: Browsing products, viewing product details, categorizing products.
* **Cart Management**: Add/remove items, update quantities, calculate totals.
* **Order Processing**: Order confirmation, selecting payment methods, tracking order status.
* **Communication**: Contact us form submissions.

### Business Logic Modules
1. **Auth Module**: Handles registration, login, token generation, email/OTP verification.
2. **User Module**: Manages user profiles and addresses.
3. **Product Module**: Manages inventory, product details, and search.
4. **Category Module**: Manages hierarchical grouping of products.
5. **Cart Module**: Temporary storage for user's intended purchases.
6. **Order Module**: Converting carts to orders, order state machine.
7. **Payment Module**: Handling payment gateway integration.

### Database Requirements
* **Database**: PostgreSQL (recommended for e-commerce due to ACID compliance and relational integrity) using Prisma ORM.
* **Collections/Tables**: Users, Products, Categories, Orders, OrderItems, Cart, CartItems, OTPs.

### Authentication Requirements
* Access Token (short-lived) and Refresh Token (long-lived) via JWT.
* HTTP-only cookies for secure token storage.
* Role-based access control (Admin, User).

### Authorization Requirements
* Users can only access and modify their own carts, orders, and profiles.
* Admins can manage products, categories, and view all orders.

### Third-party Integrations
* **Email Service**: SendGrid or Nodemailer (for OTPs, email verification, order confirmations).
* **Payment Gateway**: Stripe or PayPal (for processing payments).

### File Storage Requirements
* **Cloud Storage**: AWS S3 or Cloudinary for storing product images and user avatars.

### Notification Requirements
* Email notifications for successful registration, password resets, and order confirmations.

### Deployment Requirements
* Dockerized application.
* CI/CD pipeline using GitHub Actions.
* Deployed on Render, AWS, or DigitalOcean.

---

## Architecture Plan

### Application Structure
We will use a modular, component-based architecture using Node.js, Express, and TypeScript.
```
src/
├── config/           # Environment variables and configurations
├── database/         # DB connection and ORM setup
├── middlewares/      # Global and route-specific middlewares
├── modules/          # Domain modules (auth, users, products, etc.)
│   ├── auth/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── routes/
│   │   ├── validators/
│   │   └── tests/
│   └── ...
├── repositories/     # Data access layer (abstracts DB queries)
├── types/            # TypeScript interfaces and types
├── utils/            # Helper functions, error classes
└── app.ts            # Express app configuration
```

### Module Boundaries
Each module is self-contained. A controller handles the HTTP request, validates it, and passes it to the service. The service executes the business logic and uses the repository to interact with the database.

### Service Layer Design
Services will contain purely business logic and remain framework-agnostic. They will not interact directly with Express request/response objects.

### Database Layer Design
The Repository Pattern will be used. Services will call repository methods (e.g., `userRepository.findByEmail(email)`) instead of raw Prisma/SQL queries, making the app easier to test and maintain.

### API Design Strategy
* RESTful API principles.
* Standardized JSend response format (`{ status: "success", data: {...} }` or `{ status: "error", message: "..." }`).
* API versioning (e.g., `/api/v1/...`).

### Error Handling Strategy
* Custom `AppError` class inheriting from `Error` (includes statusCode and isOperational flags).
* Centralized error-handling middleware that catches synchronous and asynchronous errors.

### Logging Strategy
* **Winston** or **Pino** for structured logging.
* HTTP request logging via **Morgan**.

### Validation Strategy
* **Zod** schema validation at the middleware level to validate `req.body`, `req.params`, and `req.query` before they reach the controller.

### Security Strategy
* **Helmet** for secure HTTP headers.
* **Express Rate Limit** to prevent brute-force attacks.
* **CORS** configured strictly for the frontend domain.
* **xss-clean** and **express-mongo-sanitize** (or equivalent) to prevent injection attacks.

### Testing Strategy
* **Unit Tests**: For services and utils using `Jest`.
* **Integration Tests**: For API endpoints using `Supertest` + `Jest`.
* **Mocking**: Mocking the repository layer for unit tests and using an in-memory DB or test DB for integration tests.

---

## Development Roadmap

### [x] Phase 1: Project Setup & Architecture Skeleton
* **Goal**: Initialize the project with the required folder structure, TypeScript, Express, error handling, and testing environment.
* **Deliverables**: Base repository with Express server, standard middlewares, config files, and a health check endpoint.
* **Dependencies**: Node.js, Express, TypeScript, Jest.
* **Test requirements**: Unit test for the health check endpoint.
* **Definition of completion**: Server runs successfully, `npm test` passes, and the base folder structure matches the plan.

### [x] Phase 2: Database Setup & User Module
* **Goal**: Set up PostgreSQL + SQLAlchemy (migrated to Python), create User models, and implement basic user CRUD.
* **Deliverables**: SQLAlchemy schema, DB connection, User Router & Pydantic Schemas.
* **Dependencies**: Phase 1, PostgreSQL, FastAPI.
* **Test requirements**: Integration tests for user creation and retrieval endpoints.
* **Definition of completion**: DB connects successfully, and User endpoints pass integration tests.

### [x] Phase 3: Authentication & Security
* **Goal**: Implement JWT auth, login, registration, email/OTP verification, and password reset.
* **Deliverables**: Auth Controller/Service, JWT utility, Email utility, protected route middleware.
* **Dependencies**: Phase 2, jsonwebtoken, nodemailer/sendgrid, bcryptjs.
* **Test requirements**: Unit tests for JWT/hash utilities. Integration tests for registration, login, and protected routes.
* **Definition of completion**: Users can register, verify email via OTP, log in, and access protected routes.

### [x] Phase 4: Product & Category Management
* **Goal**: Build the catalog system for products and categories.
* **Deliverables**: Product and Category models, repositories, services, and controllers (including image upload logic).
* **Dependencies**: Phase 3, Multer, Cloudinary/AWS S3.
* **Test requirements**: Tests for creating categories, creating products, and retrieving products (with pagination/filtering).
* **Definition of completion**: API supports full CRUD for products and categories with image uploads.

### [x] Phase 5: Cart System
* **Goal**: Implement the shopping cart.
* **Deliverables**: Cart and CartItem models/endpoints to add, update, and remove items.
* **Dependencies**: Phase 4.
* **Test requirements**: Tests ensuring correct cart total calculations and item management.
* **Definition of completion**: Users can manage their cart, and prices/totals are correctly computed based on the DB product prices.

### [x] Phase 5.5: Admin Dashboard
* **Goal**: Implement admin dashboard, protect API endpoints, and allow JSON product imports.
* **Deliverables**: Admin APIs, dashboard UI, secure `get_admin_user` backend routes.

### Phase 6: Order & Checkout Management
* **Goal**: Convert carts to orders and integrate payment processing.
* **Deliverables**: Order models, checkout endpoints, Stripe payment integration.
* **Dependencies**: Phase 5, Stripe SDK.
* **Test requirements**: Tests for order creation and payment intent generation (mocking Stripe).
* **Definition of completion**: Users can place an order, receive a payment intent, and order status updates upon successful payment.

### Phase 7: Polish & Documentation
* **Goal**: Finalize the API, add contact us logic, and prepare for deployment.
* **Deliverables**: Contact endpoints, API documentation (Swagger/Postman), final refactoring.
* **Dependencies**: Phase 6.
* **Test requirements**: End-to-end test flow.
* **Definition of completion**: Fully documented, tested API ready for production deployment.
