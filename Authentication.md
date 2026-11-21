# **Authentication API — Complete Codebase Walkthrough**

We'll go through **your actual project**, not generic FastAPI authentication code.

The goal is to understand every component, every function, the syntax, how data moves through the application, what happens internally when a request arrives, and how all the pieces connect.

By the end, you should be able to explain and trace:

- How the FastAPI application starts
- How routes are registered
- How the database is created and accessed
- How SQLModel models work
- How Pydantic schemas validate requests
- How passwords are hashed and verified
- How JWT access and refresh tokens work
- How dependencies work (`Depends`, `Annotated`)
- How registration, login, refresh, logout, and password reset work
- How protected routes determine who is making the request
- How your code executes from the first HTTP request to the database and back

# **1. First understand the entire architecture**

## **Your Authentication Application**

Client → FastAPI → Dependencies → Database / Security → Response

[#fastapi #authentication_authorization #jwt #rbac | Jayanth CT](https://images.openai.com/static-rsc-4/W0btqeWfF1BqBXM1ma4s7YJKNvqPUOYkwVdfvKDjljjZVVhp0DUNnpXQe6rPZ0EwhO-0kSsXHHQjIhGxwbhU30j5MsDN9Mu5CDaBr7slLGmSHGV_SlUuZS-V4jiNJb3mZLTqru55XxFtjDMsWcgp7gb22KamJo0U8HrohXhVXRs?purpose=inline)

[FastAPI Authentication & Authorization with JWT | Nimra Akram posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/P6VXt4HnSWArg7JP0U0zwOGroHWnsUKLHwGqjZP46B7dVkmzHIsTe9CUljZdYQxZIrn6dN07zByAK1ZdNAV05Jbt6XGAaSz0Idtia0Xv4lW5eovswfZ7cX-93_cD5ipHN_o7bkW-hidUMhVrhJudAub-6NJx3XA_hg3V2B0f08k?purpose=inline)

[API: Beginner to Advance: Building User Registration in FastAPI- Part 8 | by Talib | Medium](https://images.openai.com/static-rsc-4/0zjDinyOr47uePKwKdIUx24u0mRTJp7niEr94NCDG4YTxcSKbETlHFpIbkfkZWKJ8GO9zKplDMj9ReJD1yJkD0wA9fLikJrEEkaXM2wO6aDY2ZQYse9J90p6bJcFguekFTkZQjeeJRhoxGUCbs_wGJq7a-_BHoSiCMVz1pSf8k4?purpose=inline)

10

Your project is divided into logical layers.

```
authentication/
│
├── .env
├── pyproject.toml
├── uv.lock
├── README.md
│
└── app/
    │
    ├── main.py
    ├── models.py
    ├── schemas.py
    │
    ├── api/
    │   ├── dependencies.py
    │   │
    │   └── routes/
    │       ├── auth.py
    │       ├── users.py
    │       └── password_reset.py
    │
    ├── core/
    │   ├── config.py
    │   └── security.py
    │
    └── db/
        └── session.py
```

## **What each layer is responsible for**

| File                           | Responsibility                                              |
| ------------------------------ | ----------------------------------------------------------- |
| `main.py`                      | Creates the FastAPI application and registers routes        |
| `models.py`                    | Defines database tables                                     |
| `schemas.py`                   | Defines the structure and validation of API inputs/outputs  |
| `api/dependencies.py`          | Authentication dependencies, token validation, current user |
| `api/routes/auth.py`           | Registration, login, refresh, logout                        |
| `api/routes/users.py`          | User profile and user-related endpoints                     |
| `api/routes/password_reset.py` | Password reset workflow                                     |
| `core/security.py`             | Hashing, password verification, JWT creation and decoding   |
| `core/config.py`               | Loads configuration and secrets                             |
| `db/session.py`                | Database engine, database sessions, table creation          |

The important architectural principle is:

> **Routes handle HTTP requests. Dependencies provide reusable requirements. Security functions perform security operations. Models represent database data. Schemas define API data.**

# **2. The complete application flow**

Before studying each file, understand the entire lifecycle.

## **User Authentication Lifecycle**

1\. Registration

Client sends email and password → validation → password hashing → database save

2\. Login

Email/password → user lookup → password verification → access + refresh tokens

3\. Authenticated Request

Bearer token → token validation → session check → user lookup → endpoint

4\. Token Refresh

Refresh token → validation → new access token

5\. Logout

Current session ID → revoked session database record → future requests rejected

6\. Password Reset

Email → reset token → token validation → new password hashing → database update

Let's now understand everything from the bottom up.

# **3.&#x20;**`pyproject.toml`**&#x20;— Project dependencies**

```
[project]
name = "authentication"
version = "0.1.0"
description = "Authentication application (sections 12-13)"
readme = "README.md"
requires-python = ">=3.14"

dependencies = [
    "fastapi[standard]>=0.139.0",
    "pwdlib[argon2]>=0.3.0",
    "pydantic-settings>=2.14.2",
    "pydantic[email]>=2.13.4",
    "pyjwt>=2.13.0",
    "sqlmodel>=0.0.39",
]
```

This file defines your Python project and its dependencies.

## `name`

```
name = "authentication"
```

The name of the Python project.

## `requires-python`

```
requires-python = ">=3.14"
```

This says your project requires Python 3.14 or newer.

## **Dependencies**

### **FastAPI**

```
"fastapi[standard]>=0.139.0"
```

FastAPI is your API framework.

It provides:

- Routing
- HTTP request handling
- Dependency injection
- Request validation
- Response serialization
- OpenAPI documentation
- Error handling
- ASGI application functionality

The `[standard]` extra installs additional standard tooling/features associated with FastAPI.

### `pwdlib[argon2]`

```
"pwdlib[argon2]>=0.3.0"
```

Used for password hashing and verification.

You don't store passwords directly.

Instead:

```
User password
      ↓
Password hashing algorithm
      ↓
Password hash
      ↓
Database
```

### `pydantic-settings`

```
"pydantic-settings>=2.14.2"
```

Used to load application settings from environment variables and configuration sources.

For example:

```
JWT_SECRET_KEY=some-secret
```

### `pydantic[email]`

```
"pydantic[email]>=2.13.4"
```

Adds email validation support to Pydantic.

This allows:

```
email: EmailStr
```

Instead of accepting arbitrary text, it validates that the supplied value resembles a valid email address.

### `pyjwt`

```
"pyjwt>=2.13.0"
```

Used to create and decode JWTs.

### `sqlmodel`

```
"sqlmodel>=0.0.39"
```

SQLModel combines ideas from:

- SQLAlchemy — database interaction
- Pydantic — data validation and Python typing

It allows us to define database models using Python classes.

# **4.&#x20;**`main.py`**&#x20;— Application entry point**

Your code:

```
from contextlib import asynccontextmanagerfrom fastapi import FastAPIfrom app.api.routes import auth, password_reset, usersfrom app.db.session import create_db_and_tables@asynccontextmanagerasync def lifespan(app: FastAPI):    create_db_and_tables()    yieldapp = FastAPI(lifespan=lifespan)app.include_router(auth.router)app.include_router(users.router)app.include_router(password_reset.router)
```

This is the file that creates and configures your FastAPI application.

## **4.1 Imports**

```
from contextlib import asynccontextmanager
```

`contextlib` is part of Python's standard library.

It provides tools for managing context-based execution.

The decorator:

```
@asynccontextmanager
```

allows us to create an asynchronous context manager using a generator function.

In this case, we are using it to define the FastAPI application lifespan.

```
from fastapi import FastAPI
```

Imports the `FastAPI` class.

We use it to create our application:

```
app = FastAPI()
```

The `app` object represents the application instance.

It holds:

- Routes
- Middleware
- Application configuration
- OpenAPI information
- Dependencies
- Lifespan behavior

```
from app.api.routes import auth, password_reset, users
```

Imports three route modules.

Each module contains endpoints.

For example:

```
auth
```

Contains:

- `/register`
- `/token`
- `/token/refresh`
- `/logout`

`users` contains user endpoints.

`password_reset` contains password-reset endpoints.

```
from app.db.session import create_db_and_tables
```

Imports the function responsible for creating the database tables.

## **4.2 The lifespan function**

```
@asynccontextmanagerasync def lifespan(app: FastAPI):    create_db_and_tables()    yield
```

This is executed as part of the application's lifecycle.

The lifecycle is conceptually:

```
FastAPI starts
      ↓
Lifespan function begins
      ↓
create_db_and_tables()
      ↓
yield
      ↓
Application serves requests
      ↓
Application shuts down
```

### **Why use lifespan?**

Some tasks should happen when an application starts, rather than every time a request arrives.

Examples:

- Create database tables
- Initialize resources
- Establish connections
- Load configuration
- Initialize caches

In your application:

```
create_db_and_tables()
```

runs when the application starts.

## **What is&#x20;**`yield`**&#x20;doing?**

```
yield
```

This is not simply returning a value.

It separates the lifespan into two phases:

```
@asynccontextmanagerasync def lifespan(app: FastAPI):    # BEFORE application starts serving    create_db_and_tables()    yield    # AFTER yield:    # runs when application shuts down
```

Your current implementation only performs startup work.

There is no shutdown code after `yield`.

## **4.3 Creating the FastAPI application**

```
app = FastAPI(lifespan=lifespan)
```

This creates your FastAPI application.

The argument:

```
lifespan=lifespan
```

connects the function above to the application's lifecycle.

## **4.4 Registering routers**

```
app.include_router(auth.router)app.include_router(users.router)app.include_router(password_reset.router)
```

A route module contains an `APIRouter`.

But creating an `APIRouter` doesn't automatically make it part of the application.

You must attach it.

```
FastAPI application
       │
       ├── auth.router
       │
       ├── users.router
       │
       └── password_reset.router
```

This is why:

```
app.include_router(auth.router)
```

is necessary.

If you forget it, the endpoints inside that router won't be registered with your application.

# **5. Database layer —&#x20;**`db/session.py`

Your code:

```
from typing import Annotatedfrom fastapi import Dependsfrom sqlmodel import Session, SQLModel, create_engineimport app.modelsengine = create_engine("sqlite:///auth.db")def create_db_and_tables():    SQLModel.metadata.create_all(engine)def get_session():    with Session(engine) as session:        yield sessionSessionDep = Annotated[Session, Depends(get_session)]
```

This file establishes the database connection configuration and provides sessions to the application.

## **5.1&#x20;**`create_engine`

```
engine = create_engine("sqlite:///auth.db")
```

An engine is the object SQLAlchemy uses to manage database connectivity.

The engine knows:

- Which database to use
- How to connect to it
- How to execute SQL
- How to manage connections

Your database:

```
auth.db
```

is a SQLite database file.

The URL:

```
"sqlite:///auth.db"
```

means a SQLite database file in the current working directory.

Your application doesn't manually open and close the database file for each operation.

Instead, SQLAlchemy handles the database connection infrastructure.

## **5.2 Why import&#x20;**`app.models`**?**

```
import app.models
```

This import is extremely important.

When Python imports the module, the classes inside it are evaluated:

```
class User(SQLModel, table=True):    ...
```

These classes register their table definitions with SQLModel's metadata.

Conceptually:

```
Import app.models
       ↓
User class created
       ↓
User table registered
       ↓
RevokedSession table registered
       ↓
PasswordResetToken table registered
       ↓
SQLModel.metadata knows all tables
```

Without importing the models, SQLModel may not know which tables it needs to create.

## **5.3 Creating tables**

```
def create_db_and_tables():    SQLModel.metadata.create_all(engine)
```

Let's break it down.

### `SQLModel.metadata`

Contains metadata describing registered database tables.

For example:

```
users
revoked_sessions
password_reset_token
```

### `create_all(engine)`

Checks the metadata and creates the tables that don't already exist.

Conceptually:

```
Application startup
       ↓
Check database
       ↓
Does users table exist?
       ├── No → Create
       └── Yes → Leave it

Does revoked_sessions exist?
       ├── No → Create
       └── Yes → Leave it
```

Important:

`create_all()` is primarily for creating missing tables. It is not a complete database migration system. If your schema changes later, you will need migrations, usually with Alembic.

# **6. Database sessions**

## `get_session()`

```
def get_session():    with Session(engine) as session:        yield session
```

This function creates and provides a database session.

A session is a unit of interaction with the database.

It allows you to:

- Query records
- Add records
- Modify records
- Delete records
- Commit transactions

### **What is a session?**

Imagine you want to register a user.

```
FastAPI request
      ↓
get_session()
      ↓
Session created
      ↓
Query database
      ↓
Add user
      ↓
Commit transaction
      ↓
Session closes
```

The `with` statement ensures the session is closed when the context exits.

```
with Session(engine) as session:
```

This is Python's context manager syntax.

It automatically handles resource cleanup.

## **6.1 Why&#x20;**`yield`**&#x20;instead of&#x20;**`return`**?**

```
def get_session():    with Session(engine) as session:        yield session
```

A normal function:

```
def get_session():    return session
```

would return the object directly.

But a generator function with `yield` allows FastAPI to manage the dependency lifecycle.

The sequence is:

1. FastAPI calls `get_session()`.
2. A session is created.
3. `yield session` gives the session to the route/dependency.
4. Request processing happens.
5. The dependency cleanup occurs.
6. The `with` block exits and closes the session.

This makes it ideal for database resources.

# **7.&#x20;**`SessionDep`**&#x20;— Dependency injection shortcut**

```
SessionDep = Annotated[Session, Depends(get_session)]
```

This is one of the most important pieces of syntax in your project.

Let's understand all three parts.

## `Session`

```
Session
```

The type of object we want.

## `Depends(get_session)`

```
Depends(get_session)
```

Tells FastAPI:

> This parameter should be provided by executing the `get_session` dependency.

FastAPI handles the function call.

You don't manually write:

```
session = get_session()
```

inside every route.

## `Annotated`

```
Annotated[Session, Depends(get_session)]
```

`Annotated` lets us attach additional information to a type.

The first argument is the actual type:

```
Session
```

The second argument is metadata:

```
Depends(get_session)
```

So this:

```
SessionDep = Annotated[Session, Depends(get_session)]
```

creates a reusable dependency type.

Instead of writing:

```
def register(    session: Session = Depends(get_session)):
```

you can write:

```
def register(session: SessionDep):
```

FastAPI understands the dependency because it is embedded in the annotation.

## **Dependency flow**

Route requests a SessionDep

↓

FastAPI sees Depends(get_session)

↓

FastAPI executes get_session()

↓

Database session is created

↓

Session injected into route

↓

Route uses database

↓

Session closes after request

# **8.&#x20;**`models.py`**&#x20;— Database structure**

Your models:

```
from datetime import datetimefrom pydantic import EmailStrfrom sqlmodel import Field, SQLModel
```

These imports are used for database model definitions.

- `datetime` — timestamps
- `EmailStr` — email validation/type
- `Field` — field configuration
- `SQLModel` — model base class

## **8.1 User model**

```
class User(SQLModel, table=True):    __tablename__: str = "users"    id: int | None = Field(default=None, primary_key=True)    email: EmailStr = Field(unique=True, index=True)    hashed_password: str    role: str = Field(default="user")
```

This class represents a database table.

### `class User`

Defines a Python class.

### `(SQLModel, table=True)`

```
class User(SQLModel, table=True):
```

The class inherits from `SQLModel`.

The argument:

```
table=True
```

tells SQLModel:

> This class represents a database table.

Without `table=True`, a SQLModel class can still be used as a data model, but it won't be treated as a database table in the same way.

## `__tablename__`

```
__tablename__: str = "users"
```

Specifies the table name.

Your database table is:

```
users
```

## `id`

```
id: int | None = Field(default=None, primary_key=True)
```

### `int | None`

The value can be:

- An integer
- `None`

Why?

When creating a user, the database hasn't generated the ID yet.

Initially:

```
id = None
```

After inserting the user, the database assigns an ID.

Example:

```
New user
id = None
email = test@example.com
```

After database insertion:

```
id = 1
email = test@example.com
```

### `Field`

Allows additional configuration.

```
Field(default=None, primary_key=True)
```

- `default=None` — initially no ID
- `primary_key=True` — this column uniquely identifies each row

## **Email**

```
email: EmailStr = Field(unique=True, index=True)
```

### `EmailStr`

Validates email format.

Example:

```
user@example.com
```

is accepted.

Something like:

```
hello
```

will fail validation.

### `unique=True`

The database should not allow duplicate email values.

```
user1@example.com → allowed
user1@example.com → duplicate → rejected
```

### `index=True`

Creates a database index.

An index helps the database locate records more efficiently.

Without an index, the database may need to scan many rows.

With an index, queries like:

```
SELECT * FROM users WHERE email = ?
```

can become more efficient.

## `hashed_password`

```
hashed_password: str
```

This stores the password hash.

It should never contain the original password.

Example database record:

```
email: user@example.com
hashed_password: $argon2id$...
```

Not:

```
hashed_password: mypassword123
```

## `role`

```
role: str = Field(default="user")
```

Every newly created user has a default role:

```
user
```

This is intended for authorization.

For example:

```
user
admin
moderator
```

However, in your current implementation, the role is stored but is not yet used to enforce permissions.

# **9. RevokedSession model**

```
class RevokedSession(SQLModel, table=True):    __tablename__: str = "revoked_sessions"    session_id: str = Field(primary_key=True)    expires_at: datetime
```

This table stores session IDs that have been revoked.

The purpose is to allow logout to invalidate tokens before their natural expiration.

## **Why is this necessary?**

JWTs are normally stateless.

If you create a JWT:

```
Token issued
      ↓
Client receives token
      ↓
Token remains valid until expiration
```

The server does not normally need to remember the token.

But this creates a problem.

What if the user logs out?

If you simply delete the token from the frontend:

```
Frontend deletes token
```

the token still exists and could potentially be used by someone who stole it.

Therefore, your application adds a database-backed revocation mechanism.

```
Logout
   ↓
Extract session ID
   ↓
Store session ID in revoked_sessions
   ↓
Future requests check database
   ↓
Session is revoked
   ↓
Reject token
```

Your system uses the `sid` claim in the JWT to identify the session.

# **10. PasswordResetToken model**

```
class PasswordResetToken(SQLModel, table=True):    __tablename__: str = "password_reset_token"    id: int | None = Field(default=None, primary_key=True)    user_id: int = Field(foreign_key="users.id", index=True)    token: str = Field(unique=True, index=True)    expires_at: datetime    used: bool = Field(default=False)
```

This table stores password reset tokens.

### `user_id`

```
user_id: int = Field(foreign_key="users.id", index=True)
```

This identifies the user associated with the reset token.

The foreign key:

```
foreign_key="users.id"
```

means the token references the `id` column in the `users` table.

Conceptually:

```
users
────────────────────────
id | email
1  | a@example.com
2  | b@example.com

password_reset_token
────────────────────────────────────────
id | user_id | token | expires_at
1  | 1       | ...   | ...
2  | 2       | ...   | ...
```

### `used`

```
used: bool = Field(default=False)
```

The token should only be used once.

When a reset succeeds:

```
used = True
```

This prevents reuse of the same reset token.

# **11.&#x20;**`schemas.py`**&#x20;— API data validation**

Your schemas:

```
from pydantic import EmailStrfrom sqlmodel import Field, SQLModelclass UserCreate(SQLModel):    email: EmailStr    password: str = Field(min_length=1, max_length=12)class UserUpdate(SQLModel):    email: EmailStr | None = Noneclass UserResponse(SQLModel):    id: int    email: str    role: strclass PasswordResetRequest(SQLModel):    email: EmailStrclass PasswordResetConfirm(SQLModel):    token: str    new_password: str = Field(min_length=1, max_length=12)
```

The key difference:

**Models**

Database structure

- Tables
- Columns
- Primary keys
- Foreign keys

**Schemas**

API data structure

- Request validation
- Response format
- Required fields
- Type constraints

You could think of schemas as the contract between the client and your API.

## **11.1&#x20;**`UserCreate`

```
class UserCreate(SQLModel):    email: EmailStr    password: str = Field(min_length=1, max_length=12)
```

This defines what a registration request should contain.

Expected JSON:

```
{
  "email": "user@example.com",
  "password": "password123"
}
```

The API validates:

- Email format
- Password type
- Password length

The request doesn't need to contain:

```
{
  "id": 1,
  "role": "admin",
  "hashed_password": "..."
}
```

Those fields are controlled by the server.

## **11.2&#x20;**`UserUpdate`

```
class UserUpdate(SQLModel):    email: EmailStr | None = None
```

The user can update their email.

The field is optional.

```
email: EmailStr | None = None
```

means:

- If an email is supplied, validate it.
- If not supplied, it may be `None`.

This allows partial updates.

## **11.3&#x20;**`UserResponse`

```
class UserResponse(SQLModel):    id: int    email: str    role: str
```

This is the data the API returns to the client.

Notice what's missing:

```
hashed_password
```

That's intentional.

The database model may contain sensitive fields, but the API response schema controls what is exposed.

Example response:

```
{
  "id": 1,
  "email": "user@example.com",
  "role": "user"
}
```

The password hash is not returned.

## **11.4 Password reset schemas**

```
class PasswordResetRequest(SQLModel):    email: EmailStr
```

Used when requesting a reset link.

```
class PasswordResetConfirm(SQLModel):    token: str    new_password: str = Field(min_length=1, max_length=12)
```

Used when submitting a reset token and new password.

# **12.&#x20;**`core/config.py`**&#x20;— Configuration**

Your code:

```
from pydantic_settings import BaseSettings, SettingsConfigDictclass Settings(BaseSettings):    model_config = SettingsConfigDict(env_file=".env")    JWT_SECRET_KEY: strsettings = Settings()
```

This file loads application settings.

## `BaseSettings`

```
class Settings(BaseSettings):
```

`BaseSettings` allows Pydantic to load configuration from sources such as environment variables.

## `model_config`

```
model_config = SettingsConfigDict(env_file=".env")
```

This tells Pydantic Settings to read configuration from:

```
.env
```

## `JWT_SECRET_KEY`

```
JWT_SECRET_KEY: str
```

This declares a required configuration value.

Your `.env` file contains:

```
JWT_SECRET_KEY=...
```

The secret is used to sign and verify JWTs.

## `settings = Settings()`

```
settings = Settings()
```

Creates a settings object.

When this executes:

1. Pydantic reads the configuration.
2. It searches for the environment variable/configuration.
3. It reads the `.env` file if configured.
4. It validates the values.
5. It creates the `settings` object.

Other files can then use:

```
settings.JWT_SECRET_KEY
```

Instead of hardcoding secrets.

# **13.&#x20;**`core/security.py`**&#x20;— The security engine**

This file contains the functions that actually perform the security operations.

```
from datetime import UTC, datetime, timedeltaimport jwtfrom pwdlib import PasswordHashfrom app.core.config import settingspassword_hash = PasswordHash.recommended()DUMMY_HASH = password_hash.hash("dummypassword")ACCESS_TOKEN_ALGORITHM = "HS256"ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES = 10REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS = 7
```

## **13.1 Password hashing configuration**

```
password_hash = PasswordHash.recommended()
```

This creates a password hashing object using a recommended configuration from `pwdlib`.

The hashing object will be used for:

```
password_hash.hash(...)
```

and:

```
password_hash.verify(...)
```

The algorithm is not meant to be a normal fast hash like SHA-256.

Password hashing should be deliberately computationally expensive to make large-scale password guessing more difficult.

## **13.2 Dummy hash**

```
DUMMY_HASH = password_hash.hash("dummypassword")
```

This creates a dummy password hash.

It is used when the login email doesn't exist.

Why?

Consider normal login behavior.

### **User exists**

```
Email lookup
      ↓
User found
      ↓
Verify supplied password against stored hash
```

### **User doesn't exist**

Without the dummy hash:

```
Email lookup
      ↓
User not found
      ↓
Immediately return error
```

This may create timing differences.

An attacker might use timing behavior to determine whether an email exists.

Your implementation performs a password verification against a dummy hash when the user isn't found.

This makes the unknown-user path perform a password-hashing verification operation as well.

## **13.3 Token configuration**

```
ACCESS_TOKEN_ALGORITHM = "HS256"
```

HS256 means:

- HMAC
- SHA-256
- Symmetric signing

The same secret is used to sign and verify tokens.

Your secret is:

```
settings.JWT_SECRET_KEY
```

## **Token expiration**

```
ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES = 10
```

Access tokens expire after 10 minutes by default.

```
REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS = 7
```

Refresh tokens expire after 7 days by default.

# **14. Password hashing functions**

## `hash_password()`

```
def hash_password(plain_password: str) -> str:    return password_hash.hash(plain_password)
```

### **Function definition**

```
def
```

Defines a function.

### **Function name**

```
hash_password
```

This describes the function's purpose.

### **Parameter**

```
plain_password: str
```

The function expects a string.

Example:

```
plain_password = "myPassword123"
```

### **Return type**

```
-> str
```

Indicates that the function returns a string.

### **Function body**

```
return password_hash.hash(plain_password)
```

The plaintext password is passed to the hashing implementation.

Example:

```
hash_password("myPassword123")
```

Conceptual output:

```
$argon2id$v=19$m=...,t=...,p=...$...
```

The actual hash is different because hashing incorporates parameters and salt.

## **14.1 Why don't we store the original password?**

Suppose:

```
Email: user@example.com
Password: myPassword123
```

You should not store:

```
password = myPassword123
```

Instead:

```
password_hash = $argon2id$...
```

During login:

```
User enters password
       ↓
Password verification
       ↓
Compare using hashing algorithm
       ↓
True / False
```

The server does not need to recover the original password.

## **14.2&#x20;**`verify_password()`

```
def verify_password(plain_password: str, hashed_password: str) -> bool:    return password_hash.verify(plain_password, hashed_password)
```

Parameters:

| Parameter         | Meaning                          |
| ----------------- | -------------------------------- |
| `plain_password`  | Password supplied by user        |
| `hashed_password` | Password hash stored in database |

Returns:

```
True
```

or:

```
False
```

Example:

```
verify_password(    "myPassword123",    stored_hash)
```

The password hashing library verifies the password against the stored hash.

You do not write:

```
hash_password(password) == stored_hash
```

because a new hash operation normally generates a new salt, so the encoded result may differ even for the same password.

Instead:

```
verify_password(password, stored_hash)
```

# **15. JWT — Understanding the token before the code**

JWT stands for:

**JSON Web Token**

Your application uses JWTs to represent an authenticated session.

A JWT generally looks like:

```
xxxxx.yyyyy.zzzzz
```

It consists of three parts:

```
HEADER.PAYLOAD.SIGNATURE
```

JWT Anatomy

HEADER

Algorithm and token type

PAYLOAD

Claims such as sub, exp, iat, sid, type

SIGNATURE

Cryptographic proof that the token was signed with the expected secret

## **Header**

Conceptually:

```
{
  "alg": "HS256",
  "typ": "JWT"
}
```

## **Payload**

Your tokens may contain:

```
{
  "sub": "user@example.com",
  "sid": "session-uuid",
  "iat": "...",
  "exp": "...",
  "type": "access"
}
```

### `sub`

Subject.

Identifies who the token represents.

Your application uses the user's email.

### `sid`

Session ID.

Identifies the login session.

### `iat`

Issued At.

Indicates when the token was created.

### `exp`

Expiration.

Indicates when the token should no longer be valid.

### `type`

Your application uses this to distinguish:

```
access
```

from:

```
refresh
```

# **16.&#x20;**`create_access_token()`

Your code:

```
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:    now = datetime.now(UTC)    if expires_delta:        expiration_time = now + expires_delta    else:        expiration_time = now + timedelta(            minutes=ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES        )    payload = {**data, "iat": now, "exp": expiration_time, "type": "access"}    return jwt.encode(        payload=payload,        key=settings.JWT_SECRET_KEY,        algorithm=ACCESS_TOKEN_ALGORITHM,    )
```

Let's go line by line.

## **Function signature**

```
def create_access_token(    data: dict,    expires_delta: timedelta | None = None) -> str:
```

### `data: dict`

The caller provides the claims that should be included in the token.

For example:

```
data = {    "sub": "user@example.com",    "sid": "abc123"}
```

### `expires_delta`

```
timedelta | None
```

Can be:

- A `timedelta`
- `None`

This allows the caller to override the expiration period.

Example:

```
timedelta(minutes=5)
```

### `-> str`

The function returns a JWT string.

## **Current time**

```
now = datetime.now(UTC)
```

Gets the current UTC time.

Using UTC is useful because the application can operate independently of local time zones.

## **Expiration logic**

```
if expires_delta:    expiration_time = now + expires_delta
```

If a custom expiration was provided, use it.

Example:

```
expires_delta = timedelta(minutes=30)
```

Then:

```
Current time
      +
30 minutes
      =
Expiration
```

Otherwise:

```
expiration_time = now + timedelta(    minutes=ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES)
```

This uses your default 10-minute expiration.

## **Building the payload**

```
payload = {    **data,    "iat": now,    "exp": expiration_time,    "type": "access",}
```

### `**data`

Dictionary unpacking.

Suppose:

```
data = {    "sub": "user@example.com",    "sid": "123"}
```

Then:

```
{    **data,    "iat": now,    "exp": expiration_time,    "type": "access"}
```

becomes:

```
{    "sub": "user@example.com",    "sid": "123",    "iat": now,    "exp": expiration_time,    "type": "access"}
```

This is dictionary unpacking.

## **Creating the JWT**

```
jwt.encode(    payload=payload,    key=settings.JWT_SECRET_KEY,    algorithm=ACCESS_TOKEN_ALGORITHM,)
```

The JWT library:

1. Encodes the header.
2. Encodes the payload.
3. Signs the token using your secret and algorithm.
4. Returns the token string.

The secret is not included inside the token.

The token is signed, not encrypted.

Therefore:

> Never put passwords, private information, or secrets inside the JWT payload.

# **17.&#x20;**`create_refresh_token()`

```
def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:    now = datetime.now(UTC)    if expires_delta:        expiration_time = now + expires_delta    else:        expiration_time = now + timedelta(            days=REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS        )    payload = {        **data,        "iat": now,        "exp": expiration_time,        "type": "refresh",    }    return jwt.encode(        payload=payload,        key=settings.JWT_SECRET_KEY,        algorithm=ACCESS_TOKEN_ALGORITHM,    )
```

This is almost identical to access token creation.

The important differences:

| Access token          | Refresh token                     |
| --------------------- | --------------------------------- |
| `type = access`       | `type = refresh`                  |
| 10-minute default     | 7-day default                     |
| Used for API requests | Used to obtain a new access token |

The token type is extremely important.

A refresh token should not be accepted where an access token is required.

Your application checks the type later.

# **18.&#x20;**`decode_token()`

```
def decode_token(token: str) -> dict | None:    try:        payload = jwt.decode(            token,            key=settings.JWT_SECRET_KEY,            algorithms=[ACCESS_TOKEN_ALGORITHM],        )        return payload    except jwt.PyJWTError:        return None
```

This function validates and decodes the token.

## `try`

```
try:
```

Attempts to execute code that may fail.

## `jwt.decode()`

```
payload = jwt.decode(    token,    key=settings.JWT_SECRET_KEY,    algorithms=[ACCESS_TOKEN_ALGORITHM],)
```

The library verifies:

- Signature
- Signing algorithm
- Expiration, when present

If the token is valid:

```
payload
```

is returned.

If it is invalid:

An exception may occur.

## `except jwt.PyJWTError`

```
except jwt.PyJWTError:    return None
```

Catches JWT-related errors.

Instead of letting an invalid token crash the endpoint, your function returns:

```
None
```

Examples:

- Invalid signature
- Expired token
- Malformed token

This gives the rest of your application a simple interface:

```
payload = decode_token(token)if payload:    # Token decoded and validatedelse:    # Token invalid
```

# **19. Registration endpoint —&#x20;**`POST /register`

Your code:

```
@router.post(    "/register',    status_code=status.HTTP_201_CREATED,    response_model=UserResponse,)def register(session: SessionDep, user_data: UserCreate):
```

The actual endpoint is:

```
POST /register
```

Because your auth router has no prefix.

## **What does the decorator do?**

```
@router.post(...)
```

Registers this function as a POST endpoint.

The function becomes associated with:

```
POST /register
```

The decorator also defines:

```
status_code=status.HTTP_201_CREATED
```

Meaning successful registration returns HTTP:

```
201 Created
```

And:

```
response_model=UserResponse
```

This tells FastAPI what the response should look like.

## **Request**

Example:

```
POST /register
Content-Type: application/json
```

Body:

```
{
  "email": "nikhil@example.com",
  "password": "mypassword"
}
```

FastAPI receives the request.

Because the function contains:

```
user_data: UserCreate
```

FastAPI validates the JSON against the `UserCreate` schema.

If the email is invalid or the password fails validation, the function may never execute.

## **Parameter 1:&#x20;**`session`

```
session: SessionDep
```

FastAPI sees the dependency.

It creates a database session through:

```
get_session()
```

The session is injected into the function.

## **Parameter 2:&#x20;**`user_data`

```
user_data: UserCreate
```

FastAPI parses the request JSON and creates a `UserCreate` object.

You can access:

```
user_data.email
```

and:

```
user_data.password
```

## **Step 1 — Check whether the user exists**

```
existing_user = session.exec(    select(User).where(User.email == user_data.email)).first()
```

This is SQLModel/SQLAlchemy query syntax.

Let's break it down.

### `select(User)`

```
select(User)
```

Means:

> Select records from the User model/table.

Conceptually:

```
SELECT * FROM users
```

### `.where()`

```
.where(User.email == user_data.email)
```

Adds a condition.

Conceptually:

```
WHERE email = 'nikhil@example.com'
```

### `session.exec()`

```
session.exec(...)
```

Executes the query.

### `.first()`

```
.first()
```

Returns the first matching record.

If a record exists:

```
existing_user
```

contains a `User` object.

If no record exists:

```
existing_user = None
```

## **Step 2 — Reject duplicates**

```
if existing_user:    raise HTTPException(        status_code=status.HTTP_400_BAD_REQUEST,        detail="Email already registered",    )
```

If a user exists, raise an HTTP exception.

### `HTTPException`

Used to terminate the request with an HTTP error response.

### `raise`

Immediately stops normal execution of the function.

The response becomes:

```
400 Bad Request
```

Example response:

```
{
  "detail": "Email already registered"
}
```

The rest of the function does not execute.

## **Step 3 — Create a new user**

```
new_user = User(    email=user_data.email,    hashed_password=hash_password(user_data.password),)
```

This creates a Python `User` object.

Notice:

```
hashed_password=hash_password(user_data.password)
```

The password is hashed before being stored in the database.

The flow is:

```
Request password
       ↓
user_data.password
       ↓
hash_password()
       ↓
Password hash
       ↓
User object
```

The plaintext password is never assigned to the database model.

## **Step 4 — Add the user**

```
session.add(new_user)
```

This tells the database session:

> This object should be inserted into the database.

At this point, the operation is pending.

It hasn't necessarily been committed.

## **Step 5 — Commit**

```
session.commit()
```

This commits the transaction.

Conceptually:

```
INSERT INTO users ...
```

The transaction becomes persistent.

Without committing, the insert may not become permanently saved.

## **Step 6 — Refresh**

```
session.refresh(new_user)
```

Refreshes the object from the database.

This is useful because the database may have generated values.

For example:

```
new_user.id
```

was initially:

```
None
```

After insertion:

```
new_user.id = 1
```

## **Step 7 — Return**

```
return new_user
```

FastAPI receives the returned object.

But remember:

```
response_model=UserResponse
```

FastAPI serializes the response according to the schema.

The response doesn't expose `hashed_password`.

## **Registration complete**

```
POST /register
       │
       ▼
Validate request
       │
       ▼
Create DB session
       │
       ▼
Find existing user
       │
       ├── Exists → 400
       │
       └── Doesn't exist
               │
               ▼
       Hash password
               │
               ▼
       Create User
               │
               ▼
       session.add()
               │
               ▼
       session.commit()
               │
               ▼
       session.refresh()
               │
               ▼
       Return UserResponse
               │
               ▼
       201 Created
```

# **20. Login endpoint —&#x20;**`POST /token`

This is the most important authentication endpoint.

Your code:

```
@router.post("/token")def login(    session: SessionDep,    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],):
```

Endpoint:

```
POST /token
```

Unlike registration, this endpoint does not accept a regular JSON object.

It uses:

```
OAuth2PasswordRequestForm
```

## **20.1 What is&#x20;**`OAuth2PasswordRequestForm`**?**

```
from fastapi.security import OAuth2PasswordRequestForm
```

This is a FastAPI security helper.

It expects form-encoded data containing fields like:

```
username
password
```

Even if your application uses email addresses, the field name in the OAuth2 form is still:

```
username
```

So the client sends:

```
username=nikhil@example.com
password=mypassword
```

The email goes into `username`.

This is why your code uses:

```
form_data.username
```

instead of:

```
form_data.email
```

## **20.2&#x20;**`Annotated`

```
form_data: Annotated[    OAuth2PasswordRequestForm,    Depends()]
```

This tells FastAPI:

- The expected type is `OAuth2PasswordRequestForm`.
- FastAPI should create this object from the request form data.

The `Depends()` is used to extract and validate the form fields.

## **Example login request**

## **Login Request**

POST /token

Content-Type

application/x-www-form-urlencoded

Body

username=nikhil\@example.com\
password=mypassword

This is different from the registration endpoint.

Registration:

```
{
  "email": "nikhil@example.com",
  "password": "mypassword"
}
```

Login:

```
username=nikhil@example.com
password=mypassword
```

# **21. Step 1 of login — Find the user**

```
existing_user = session.exec(    select(User).where(User.email == form_data.username)).first()
```

The application uses the submitted username as an email.

Conceptually, the database query is:

```
SELECT *
FROM users
WHERE email = 'nikhil@example.com'
LIMIT 1;
```

Possible results:

### **User exists**

```
existing_user = User(...)
```

### **User doesn't exist**

```
existing_user = None
```

# **22. Step 2 — Create the credentials error**

```
credentials_exception = HTTPException(    status_code=status.HTTP_401_UNAUTHORIZED,    detail="Invalid Credentials",    headers={"WWW-Authenticate": "Bearer"},)
```

This creates an exception object.

It doesn't raise the exception yet.

The object is stored in:

```
credentials_exception
```

Later, your code uses:

```
raise credentials_exception
```

## **Why HTTP 401?**

```
401 Unauthorized
```

In authentication systems, this is typically used when the credentials are invalid or the client is not authenticated.

Your API returns:

```
{
  "detail": "Invalid Credentials"
}
```

And the header:

```
WWW-Authenticate: Bearer
```

indicates the authentication scheme.

# **23. Step 3 — If user doesn't exist**

Your code:

```
if not existing_user:    verify_password(form_data.password, DUMMY_HASH)    raise credentials_exception
```

This is an interesting security implementation.

Let's break it down.

### `if not existing_user`

This checks whether the query returned:

```
None
```

If the user doesn't exist, this branch executes.

### **Dummy verification**

```
verify_password(form_data.password, DUMMY_HASH)
```

The application performs a password verification against a dummy hash.

It does not authenticate the user.

The result is ignored.

The purpose is to reduce timing differences between:

- A login attempt with a nonexistent email
- A login attempt with an existing email but incorrect password

Without this, a user might be able to infer whether an email exists based on the response timing.

### **Raise the error**

```
raise credentials_exception
```

The login ends.

The client receives:

```
401 Unauthorized
```

# **24. Step 4 — Verify the password if the user exists**

```
if not verify_password(    form_data.password,    existing_user.hashed_password,):    raise credentials_exception
```

This checks the password.

Let's simplify:

```
verify_password(    entered_password,    database_password_hash,)
```

Returns:

```
True
```

or:

```
False
```

Your code uses:

```
if not verify_password(...):
```

Meaning:

```
If password verification fails
        ↓
Raise 401
```

If the password is correct:

```
verify_password(...) == True
```

Then:

```
not True == False
```

The `if` condition doesn't execute.

The application continues.

# **25. Step 5 — Generate the session ID**

```
data = {    "sub": existing_user.email,    "sid": str(uuid4()),}
```

This is the data that will go into both tokens.

## `uuid4()`

```
from uuid import uuid4
```

UUID stands for:

**Universally Unique Identifier**

`uuid4()` generates a random UUID.

Example:

```
c1dfda9b-2c12-45d5-96d0-3e6ef9202a55
```

Your code converts it to a string:

```
str(uuid4())
```

## **Why do we need a session ID?**

You generate one session ID for the login session.

```
sid
```

It is shared between the access token and refresh token.

Conceptually:

```
Login
  │
  ▼
Generate session ID
  │
  ├── Access token
  │       sid = ABC123
  │
  └── Refresh token
          sid = ABC123
```

This allows the server to revoke the entire session.

Instead of revoking every individual JWT, your application identifies the session using:

```
sid
```

# **26. Step 6 — Create the access token**

```
access_token = create_access_token(data=data)
```

The `data` contains:

```
{    "sub": existing_user.email,    "sid": "generated-session-id"}
```

The security function adds:

```
{    "iat": ...,    "exp": ...,    "type": "access",}
```

The complete payload is conceptually:

```
{
  "sub": "nikhil@example.com",
  "sid": "c1dfda9b-2c12-45d5-96d0-3e6ef9202a55",
  "iat": 1795260000,
  "exp": 1795260600,
  "type": "access"
}
```

The actual JWT is a signed string.

Your default expiration:

```
10 minutes
```

# **27. Step 7 — Create the refresh token**

```
refresh_token = create_refresh_token(data=data)
```

The same initial data is used:

```
{    "sub": existing_user.email,    "sid": "same-session-id"}
```

But the security function adds:

```
"type": "refresh"
```

and a different expiration.

Default:

```
7 days
```

So you get:

```
Access token
├── sub = user email
├── sid = session ID
├── type = access
└── exp = 10 minutes

Refresh token
├── sub = user email
├── sid = same session ID
├── type = refresh
└── exp = 7 days
```

# **28. Step 8 — Return the tokens**

```
return {    "access_token": access_token,    "refresh_token": refresh_token,    "token_type": "bearer",}
```

Successful login response:

```
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

The client now has both tokens.

## **Why two tokens?**

## **Access token**

Short-lived

Used to access protected API endpoints.

In your project: 10 minutes

## **Refresh token**

Longer-lived

Used to obtain a new access token when the access token expires.

In your project: 7 days

Imagine a user is working for two hours.

Without refresh tokens:

```
Login
  ↓
Access token valid for 10 minutes
  ↓
Token expires
  ↓
User must log in again
```

With refresh tokens:

```
Login
  ↓
Access token + refresh token
  ↓
Access token expires
  ↓
Client sends refresh token
  ↓
Server issues new access token
  ↓
User continues working
```

# **29. Complete login flow**

## **Login Sequence**

**Client**

Sends email and password

↓

**FastAPI**

Parses OAuth2 form

↓

**Database**

Find user by email

↓

**Security layer**

Verify password hash

↓

**Session**

Generate sid

↓

**JWT**

Create access token + refresh token

↓

**Response**

Return both tokens

# **30.&#x20;**`OAuth2PasswordBearer`**&#x20;— How protected endpoints receive tokens**

Now we reach one of the most important concepts in FastAPI.

Your code in `dependencies.py`:

```
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

## **What problem does this solve?**

When a user calls a protected endpoint, they send their access token.

Usually through:

```
Authorization: Bearer eyJ...
```

Your backend needs to extract the token from this header.

`OAuth2PasswordBearer` does this extraction.

## **The Authorization header**

```
Authorization: Bearer <access_token>
```

The header consists of:

```
Authorization
     ↓
Bearer
     ↓
JWT
```

`Bearer` means the client possesses a token and presents it to access the resource.

The token acts as a credential.

## **What does&#x20;**`OAuth2PasswordBearer`**&#x20;actually do?**

```
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

When used as a dependency, it:

1. Reads the Authorization header.
2. Expects the Bearer authentication scheme.
3. Extracts the token.
4. Returns the token string to the dependency.

It does **not**, by itself:

- Verify the JWT signature
- Check the user in the database
- Check session revocation
- Check user permissions
- Confirm that the token is an access token

Those operations happen later in your code.

## `tokenUrl="token"`

This tells FastAPI's OAuth2 security/OpenAPI machinery where the token endpoint is located.

Your token endpoint is:

```
@router.post("/token")
```

Therefore:

```
tokenUrl="token"
```

points to the login/token endpoint.

This is primarily used in the OAuth2 scheme and API documentation.

# **31. The authentication dependency chain**

Your `dependencies.py` contains the core mechanism that protects your API.

The chain is:

```
HTTP Request
     │
     ▼
Authorization: Bearer JWT
     │
     ▼
oauth2_scheme
     │
     ▼
Extract token string
     │
     ▼
get_access_token_payload()
     │
     ▼
decode_token()
     │
     ▼
Validate token type + claims
     │
     ▼
AccessTokenPayload
     │
     ▼
get_current_user()
     │
     ├── Check revoked session
     │
     ├── Extract email
     │
     └── Query database
     │
     ▼
CurrentUser
     │
     ▼
Protected endpoint executes
```

This dependency chain is the heart of your authentication system.

# **32.&#x20;**`_invalid_token_exception()`

Your code:

```
def _invalid_token_exception() -> HTTPException:    return HTTPException(        status_code=status.HTTP_401_UNAUTHORIZED,        detail="Invalid token",        headers={"WWW-Authenticate": "Bearer"},    )
```

This is a helper function.

The underscore at the beginning:

```
_invalid_token_exception
```

is a Python convention.

It means:

> This function is intended for internal use within this module.

It doesn't make the function private in a strict technical sense.

## **Why create a helper?**

Without it, you might repeat this everywhere:

```
raise HTTPException(    status_code=401,    detail="Invalid token",    headers={"WWW-Authenticate": "Bearer"},)
```

Instead, your application can reuse a common error definition.

For example:

```
raise _invalid_token_exception()
```

This keeps the error response consistent.

# **33.&#x20;**`get_access_token_payload()`

Your code:

```
def get_access_token_payload(    token: Annotated[str, Depends(oauth2_scheme)],) -> dict:    payload = decode_token(token)    if (        not payload        or payload.get("type") != "access"        or not payload.get("sid")        or not payload.get("sub")    ):        raise _invalid_token_exception()    return payload
```

This is the first validation layer after extracting the token.

## **33.1 The function parameter**

```
token: Annotated[str, Depends(oauth2_scheme)]
```

FastAPI reads this and understands:

```
This function requires a token.
       ↓
Get it from oauth2_scheme.
       ↓
oauth2_scheme extracts it from the Authorization header.
       ↓
Pass the string into token.
```

The route doesn't need to manually read the HTTP header.

## **33.2 Decode the token**

```
payload = decode_token(token)
```

This calls your security function.

Possible results:

### **Valid token**

```
payload = {    "sub": "nikhil@example.com",    "sid": "abc123",    "iat": ...,    "exp": ...,    "type": "access",}
```

### **Invalid token**

```
payload = None
```

## **33.3 Why&#x20;**`not payload`**?**

```
not payload
```

Checks whether the payload is falsy.

For example:

```
None
```

is falsy.

An empty dictionary:

```
{}
```

is also falsy.

So invalid or empty payloads are rejected.

## **33.4 Token type validation**

```
payload.get("type") != "access"
```

Your application expects:

```
"type": "access"
```

Why?

Suppose a client sends a refresh token to a protected endpoint.

The refresh token is also a valid JWT.

The cryptographic signature may be valid.

But it should not be accepted as an access token.

Your type check prevents this:

```
Refresh token
      ↓
JWT decoding succeeds
      ↓
type = refresh
      ↓
Expected type = access
      ↓
Reject
```

This is a critical distinction.

## **33.5 Session ID validation**

```
not payload.get("sid")
```

Checks whether the token has a session ID.

Your authentication system requires a session identifier.

A token without `sid` is rejected.

## **33.6 Subject validation**

```
not payload.get("sub")
```

Checks whether the token identifies a subject.

In your implementation:

```
sub = user email
```

Without a subject, your backend cannot determine which user the token represents.

## **33.7 The complete condition**

```
if (    not payload    or payload.get("type") != "access"    or not payload.get("sid")    or not payload.get("sub")):
```

This means:

> If the token failed decoding, OR it is not an access token, OR it doesn't contain a session ID, OR it doesn't contain a subject, reject it.

`or` means any one of the conditions being true causes the overall condition to be true.

## **33.8 Return the payload**

```
return payload
```

If all checks pass, the payload is returned.

It has now passed:

- JWT decoding/signature validation
- Expiration validation
- Access-token type validation
- Session ID presence validation
- Subject presence validation

But the user has not yet been loaded from the database.

That's the next dependency.

# **34.&#x20;**`AccessTokenPayload`

```
AccessTokenPayload = Annotated[    dict,    Depends(get_access_token_payload),]
```

This creates another reusable dependency shortcut.

When a function uses:

```
payload: AccessTokenPayload
```

FastAPI automatically runs:

```
get_access_token_payload()
```

and injects its return value.

This is dependency chaining.

```
Route asks for AccessTokenPayload
       ↓
FastAPI executes get_access_token_payload
       ↓
That dependency requires oauth2_scheme
       ↓
FastAPI executes oauth2_scheme
       ↓
Token extracted
       ↓
Token decoded
       ↓
Payload returned
       ↓
Injected into route
```

You are building dependencies on top of dependencies.

# **35.&#x20;**`get_current_user()`**&#x20;— The most important dependency**

Your code:

```
def get_current_user(    session: SessionDep,    payload: AccessTokenPayload,):    session_id = payload["sid"]    if not session_id or session.get(RevokedSession, session_id):        raise _invalid_token_exception()    email = payload["sub"]    user = session.exec(        select(User).where(User.email == email)    ).first()    if not user:        raise _invalid_token_exception()    return user
```

This function converts a valid access token into a real database user.

This is the function that answers:

> Who is currently making this request?

## **35.1 Dependency inputs**

```
session: SessionDep
```

FastAPI creates a database session.

```
payload: AccessTokenPayload
```

FastAPI executes the previous dependency chain and supplies the validated token payload.

So this function does not manually:

- Read headers
- Extract the token
- Decode JWT
- Verify the signature

Those operations are handled by its dependency.

## **35.2 Get session ID**

```
session_id = payload["sid"]
```

Retrieves the session identifier.

Example:

```
sid = "c1dfda9b-2c12-45d5-96d0-3e6ef9202a55"
```

## **35.3 Check revocation**

```
if not session_id or session.get(RevokedSession, session_id):
```

This condition has two parts.

### **Part 1**

```
not session_id
```

Reject if there is no session ID.

### **Part 2**

```
session.get(RevokedSession, session_id)
```

This is a database lookup by primary key.

Because your `RevokedSession` model uses:

```
session_id: str = Field(primary_key=True)
```

SQLModel can retrieve the record using:

```
session.get(RevokedSession, session_id)
```

Conceptually:

```
SELECT *
FROM revoked_sessions
WHERE session_id = 'abc123';
```

If a record exists:

```
session.get(...) → RevokedSession object
```

If no record exists:

```
session.get(...) → None
```

Therefore:

```
if session.get(RevokedSession, session_id):
```

means:

> If this session has been revoked, reject the request.

## **35.4 Extract email**

```
email = payload["sub"]
```

Your JWT's subject contains the user's email.

Example:

```
email = "nikhil@example.com"
```

## **35.5 Find the user in the database**

```
user = session.exec(    select(User).where(User.email == email)).first()
```

This retrieves the user associated with the token.

## **35.6 Reject if user no longer exists**

```
if not user:    raise _invalid_token_exception()
```

Even if the token was originally valid, the user may have been deleted.

The application therefore checks the database.

## **35.7 Return the user**

```
return user
```

Now the dependency returns a complete `User` object.

The route can use:

```
current_user.emailcurrent_user.idcurrent_user.role
```

without performing its own authentication logic.

# **36.&#x20;**`CurrentUser`

```
CurrentUser = Annotated[    User,    Depends(get_current_user),]
```

This is the final dependency shortcut.

When a route declares:

```
current_user: CurrentUser
```

FastAPI automatically executes:

```
get_current_user()
```

The entire authentication chain runs.

## **Dependency chain, fully expanded**

Protected route

↓

CurrentUser

↓

get_current_user()

↓

AccessTokenPayload

↓

get_access_token_payload()

↓

oauth2_scheme

↓

Extract Bearer token

↓

Decode JWT

↓

Validate access token

↓

Check revoked session

↓

Load user from DB

↓

Return User

This is dependency injection in action.

You don't need to manually repeat the authentication code in every protected endpoint.

# **37. Protected routes —&#x20;**`users.py`

Your code begins:

```
router = APIRouter(    dependencies=[Depends(get_current_user)],    tags=["users"],)
```

This is important.

The router itself has a dependency.

## **Router-level dependencies**

```
dependencies=[Depends(get_current_user)]
```

Means:

> Every route registered to this router must execute `get_current_user` before it can successfully process the request.

This applies to:

```
/me
/dashboard
```

and the other routes defined in this router.

## **Why is it useful?**

Imagine ten protected endpoints.

Without router-level dependencies:

```
@router.get("/me")def me(current_user: CurrentUser):    ...@router.get("/settings")def settings(current_user: CurrentUser):    ...@router.get("/orders")def orders(current_user: CurrentUser):    ...
```

You would need to repeat authentication-related dependencies.

Router-level dependency:

```
router = APIRouter(    dependencies=[Depends(get_current_user)])
```

Automatically applies authentication.

## **Important distinction**

The router-level dependency:

```
dependencies=[Depends(get_current_user)]
```

runs authentication.

But it doesn't automatically make a variable named:

```
current_user
```

available inside every endpoint.

If an endpoint needs the actual user object, it should explicitly declare:

```
current_user: CurrentUser
```

That's why your endpoints use `CurrentUser` when they need the user.

# **38.&#x20;**`GET /me`

Your code:

```
@router.get(    "/me",    status_code=status.HTTP_200_OK,    response_model=UserResponse,)def get_me(current_user: CurrentUser):    return current_user
```

This endpoint returns the currently authenticated user.

## **Request**

```
GET /me
Authorization: Bearer <access_token>
```

## **What happens internally?**

FastAPI sees:

```
current_user: CurrentUser
```

This triggers the authentication dependency chain.

```
Request
  ↓
Extract JWT
  ↓
Decode JWT
  ↓
Validate
  ↓
Check session revocation
  ↓
Query User
  ↓
Inject User into current_user
```

Then the function executes:

```
def get_me(current_user: CurrentUser):    return current_user
```

It simply returns the authenticated user.

## **Response**

Because you specified:

```
response_model=UserResponse
```

the response is filtered to:

```
{
  "id": 1,
  "email": "nikhil@example.com",
  "role": "user"
}
```

The database password hash is not returned.

# **39.&#x20;**`PATCH /me`**&#x20;— Update email**

Your code:

```
@router.patch(    "/me",    status_code=status.HTTP_200_OK,    response_model=UserResponse,)def update_me(    session: SessionDep,    current_user: CurrentUser,    update_payload: UserUpdate,):
```

This endpoint updates the email address of the authenticated user.

## **Why&#x20;**`PATCH`**?**

`PATCH` is generally used for partial updates.

For example:

```
{
  "email": "newemail@example.com"
}
```

You don't need to send the entire user object.

## **Dependencies**

```
session: SessionDep
```

Provides database access.

```
current_user: CurrentUser
```

Provides the authenticated user.

```
update_payload: UserUpdate
```

Provides the validated request data.

FastAPI handles all three.

## **Step 1 — Check whether an email was supplied**

```
if not update_payload.email:    return current_user
```

If the email is absent or falsy, the function returns the existing user.

No database update is performed.

## **Step 2 — Find the email**

```
user_with_email = session.exec(    select(User).where(User.email == update_payload.email)).first()
```

Checks whether someone already has the requested email.

## **Step 3 — Check whether the email belongs to another user**

```
if user_with_email and user_with_email.id != current_user.id:
```

Two conditions:

### `user_with_email`

Does a record exist?

### `user_with_email.id != current_user.id`

Is it a different user?

This allows the user to retain their own email, but prevents them from changing it to someone else's email.

## **Step 4 — Reject duplicate email**

```
raise HTTPException(    status_code=status.HTTP_400_BAD_REQUEST,    detail="Email already taken",)
```

Returns:

```
400 Bad Request
```

## **Step 5 — Update the user object**

```
current_user.email = update_payload.email
```

Changes the Python object.

At this point, the change is not necessarily permanently saved.

## **Step 6 — Add to session**

```
session.add(current_user)
```

The session tracks the updated object.

## **Step 7 — Commit**

```
session.commit()
```

The update becomes persistent.

## **Step 8 — Refresh**

```
session.refresh(current_user)
```

Refreshes the object from the database.

## **Step 9 — Return**

```
return current_user
```

FastAPI serializes it using `UserResponse`.

# **40.&#x20;**`GET /dashboard`**&#x20;— A critical observation**

Your code:

```
@router.get("/dashboard")def dashboard():    return {"Profit": 1_00_000}
```

This endpoint returns:

```
{
  "Profit": 100000
}
```

But notice:

```
def dashboard():
```

There is no:

```
current_user: CurrentUser
```

However, your router has:

```
dependencies=[Depends(get_current_user)]
```

So authentication still runs.

This means:

```
GET /dashboard
       ↓
Router dependency executes
       ↓
Authentication required
       ↓
Valid access token?
       ↓
Yes → dashboard executes
No → 401
```

This endpoint is protected by authentication.

But it doesn't use the authenticated user's data.

# **41. Token refresh —&#x20;**`POST /token/refresh`

Your code:

```
@router.post("/token/refresh")def refresh_token(    session: SessionDep,    refresh_token: Annotated[str, Body(embed=True)],):
```

This endpoint obtains a new access token using a refresh token.

## **41.1 Request format**

Because of:

```
Body(embed=True)
```

the request body is expected to contain the refresh token inside an embedded field.

Conceptually:

```
{
  "refresh_token": "eyJ..."
}
```

The parameter:

```
refresh_token: Annotated[str, Body(embed=True)]
```

means:

- Expected value is a string
- It comes from the request body
- FastAPI extracts it from the embedded body field

## **41.2 Create the invalid token exception**

```
invalid_exception_token = HTTPException(    status_code=status.HTTP_401_UNAUTHORIZED,    detail="Invalid token",)
```

This is reused when refresh-token validation fails.

## **41.3 Decode the refresh token**

```
payload = decode_token(refresh_token)
```

The token is decoded and validated.

Possible results:

```
payload = dict
```

or:

```
payload = None
```

## **41.4 Verify token type**

```
if not payload or payload.get("type") != "refresh":    raise invalid_exception_token
```

This is important.

An access token should not be accepted here.

The endpoint specifically requires:

```
"type": "refresh"
```

## **41.5 Get session ID**

```
session_id = payload.get("sid")
```

Retrieves the session ID.

## **41.6 Check revocation**

```
if not session_id or session.get(RevokedSession, session_id):    raise invalid_exception_token
```

If the session was logged out, it should be present in:

```
revoked_sessions
```

Therefore refresh is rejected.

## **41.7 Get the subject**

```
email = payload.get("sub")
```

The refresh token identifies the user by email.

## **41.8 Validate subject**

```
if not email:    raise invalid_exception_token
```

Rejects tokens without a subject.

## **41.9 Find the user**

```
user = session.exec(    select(User).where(User.email == email)).first()
```

The database confirms that the user still exists.

## **41.10 Reject deleted users**

```
if not user:    raise invalid_exception_token
```

If the user no longer exists, refresh cannot continue.

## **41.11 Generate a new access token**

```
new_access_token = create_access_token(    data={        "sub": user.email,        "sid": session_id,    })
```

Notice that the new access token contains:

```
subsid
```

The existing session ID is reused.

This means the new access token belongs to the same login session.

## **41.12 Return**

```
return {    "access_token": new_access_token,    "token_type": "bearer",}
```

The refresh token itself is not returned again.

Your refresh endpoint currently creates a new access token but does not rotate the refresh token.

# **42. Refresh-token workflow**

## **Token Refresh**

Client has an expired access token and a valid refresh token

↓

Send refresh token to POST /token/refresh

↓

Decode JWT and verify signature/expiration

↓

Check token type = refresh

↓

Check session ID and revoked sessions

↓

Find user in database

↓

Create new access token

↓

Return new access token

# **43. Logout —&#x20;**`POST /logout`

Your code:

```
@router.post("/logout")def logout(    session: SessionDep,    current_user: CurrentUser,    payload: AccessTokenPayload,):
```

Logout requires:

- Database session
- Current authenticated user
- Access token payload

## **Why do we need both&#x20;**`current_user`**&#x20;and&#x20;**`payload`**?**

### `current_user`

```
current_user: CurrentUser
```

Ensures that the token:

- Is valid
- Is an access token
- Contains required claims
- Has not been revoked
- Belongs to an existing user

### `payload`

```
payload: AccessTokenPayload
```

Provides the actual token payload.

The logout function needs:

```
payload["sid"]
```

to identify the session to revoke.

## **Step 1 — Get the session ID**

```
session_id = payload["sid"]
```

## **Step 2 — Confirm token subject matches user**

```
if payload["sub"] != current_user.email:
```

This verifies that the subject in the token matches the authenticated user object.

If they don't match:

```
raise HTTPException(...)
```

## **Step 3 — Current time**

```
now = datetime.now(UTC)
```

Gets the current UTC time.

## **Step 4 — Find expired revocation records**

```
expired_sessions = session.exec(    select(RevokedSession).where(        RevokedSession.expires_at <= now    )).all()
```

This queries revoked sessions whose expiration time is in the past.

Conceptually:

```
SELECT *
FROM revoked_sessions
WHERE expires_at <= CURRENT_TIME;
```

## **Why clean expired sessions?**

A revoked-session entry only needs to exist while its associated tokens could still be valid.

Once all related tokens have expired, the revocation record is no longer needed.

So your application cleans them up.

## **Step 5 — Delete expired records**

```
for expired_session in expired_sessions:    session.delete(expired_session)
```

This loops over the records.

For each record:

```
session.delete(...)
```

marks it for deletion.

## **Step 6 — Add the current session to the revoked table**

```
session.add(    RevokedSession(        session_id=session_id,        expires_at=now + timedelta(            days=REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS        ),    ))
```

This creates a revocation record.

Example:

```
session_id = c1dfda9b-...
expires_at = now + 7 days
```

Now this session is considered revoked.

## **Step 7 — Commit**

```
session.commit()
```

Both cleanup and the new revoked-session record are committed.

## **Step 8 — Return**

```
return {"detail": "Logged out"}
```

The client receives:

```
{
  "detail": "Logged out"
}
```

# **44. What happens after logout?**

Imagine a token contains:

```
{
  "sub": "nikhil@example.com",
  "sid": "abc123",
  "type": "access"
}
```

After logout, your database contains:

```
revoked_sessions
────────────────────────
session_id | expires_at
abc123     | ...
```

The next request:

```
GET /me
Authorization: Bearer <old_token>
```

The token is still cryptographically valid.

It has not expired.

But the authentication dependency checks:

```
session.get(RevokedSession, "abc123")
```

A record exists.

Therefore:

```
Token signature valid
       ↓
Token not expired
       ↓
Session revoked
       ↓
Reject
```

This is how your application invalidates otherwise valid JWTs.

# **45. Password reset — complete workflow**

Your password reset module has two endpoints:

```
POST /password-reset/request
POST /password-reset/confirm
```

The first generates a reset token.

The second verifies it and changes the password.

# **46.&#x20;**`POST /password-reset/request`

Your code:

```
@router.post("/request")def request_password_reset(    session: SessionDep,    payload: PasswordResetRequest,):
```

Because the router has:

```
router = APIRouter(    prefix="/password-reset",    tags=["password reset"],)
```

The complete endpoint is:

```
POST /password-reset/request
```

## **Request**

```
{
  "email": "nikhil@example.com"
}
```

## **Step 1 — Create a generic message**

```
message = {    "message": "If an account exists with this email, a reset link has been sent"}
```

This message is intentionally generic.

The API does not explicitly tell the client:

```
Email exists
```

or:

```
Email does not exist
```

This reduces account enumeration.

## **Step 2 — Find the user**

```
user = session.exec(    select(User).where(User.email == payload.email)).first()
```

The database checks whether the email belongs to a user.

## **Step 3 — If user doesn't exist**

```
if not user or not user.id:    return message
```

The application returns the same generic message.

This prevents the response from revealing whether the account exists.

## **Step 4 — Generate a random token**

```
token = secrets.token_urlsafe(32)
```

Your code imports:

```
import secrets
```

The `secrets` module is intended for generating cryptographically secure random values.

This token is not a JWT.

It is a random password-reset credential.

Conceptually:

```
random secure value
       ↓
reset token
       ↓
email link
       ↓
user clicks
       ↓
server validates token
```

## **Why not use&#x20;**`uuid4()`**?**

For security-sensitive tokens, the `secrets` module is a good choice because it is specifically intended for generating cryptographically secure random values.

Your code uses:

```
secrets.token_urlsafe(32)
```

## **Step 5 — Create the database record**

```
reset_token = PasswordResetToken(    token=token,    user_id=user.id,    expires_at=datetime.now(UTC) + timedelta(minutes=10),    used=False,)
```

Let's understand each field.

### `token`

```
token=token
```

Stores the generated token.

### `user_id`

```
user_id=user.id
```

Associates it with the user.

### `expires_at`

```
expires_at=datetime.now(UTC) + timedelta(minutes=10)
```

The token expires in 10 minutes.

### `used`

```
used=False
```

The token has not yet been used.

## **Step 6 — Add token**

```
session.add(reset_token)
```

Marks the reset token for insertion.

## **Step 7 — Commit**

```
session.commit()
```

The reset token is saved.

## **Step 8 — Email delivery**

```
# Send the reset link through the configured email provider.
```

This is currently a comment.

Your code creates and stores the token, but it does not actually send an email.

The production workflow would look like:

```
POST /password-reset/request
       ↓
Find user
       ↓
Generate token
       ↓
Store token
       ↓
Generate reset link
       ↓
Send email
```

For example, the email might contain:

```
https://yourfrontend.com/reset-password?token=...
```

Your current implementation stops before sending that email.

# **47.&#x20;**`POST /password-reset/confirm`

Your code:

```
@router.post("/confirm")def confirm_password_reset(    session: SessionDep,    payload: PasswordResetConfirm,):
```

Complete endpoint:

```
POST /password-reset/confirm
```

Expected body:

```
{
  "token": "random-reset-token",
  "new_password": "newpassword"
}
```

## **Step 1 — Create error**

```
invalid_token_error = HTTPException(    status_code=status.HTTP_400_BAD_REQUEST,    detail="Invalid reset token",)
```

This is the error returned for invalid reset tokens.

## **Step 2 — Find token**

```
reset_token = session.exec(    select(PasswordResetToken).where(        PasswordResetToken.token == payload.token    )).first()
```

The database searches for the supplied token.

## **Step 3 — Check existence and usage**

```
if not reset_token or reset_token.used:    raise invalid_token_error
```

Rejects:

- Unknown tokens
- Tokens already used

## **Step 4 — Check expiration**

```
token_expired = (    reset_token.expires_at    < datetime.now(UTC).replace(tzinfo=None))
```

The code compares the token expiration with the current time.

If:

```
expires_at < current_time
```

then the token is expired.

## **Step 5 — Reject expired token**

```
if token_expired:    raise invalid_token_error
```

The password reset stops.

## **Step 6 — Find the user**

```
user = session.get(User, reset_token.user_id)
```

This retrieves the user by primary key.

Conceptually:

```
SELECT *
FROM users
WHERE id = reset_token.user_id;
```

## **Step 7 — Reject if the user doesn't exist**

```
if not user:    raise invalid_token_error
```

## **Step 8 — Hash the new password**

```
user.hashed_password = hash_password(payload.new_password)
```

The new password is hashed.

The old hash is replaced.

## **Step 9 — Mark token as used**

```
reset_token.used = True
```

This prevents the same reset token from being reused.

## **Step 10 — Add both objects to the session**

```
session.add(user)session.add(reset_token)
```

The session tracks:

- Updated user
- Updated reset token

## **Step 11 — Commit**

```
session.commit()
```

Both changes become persistent.

## **Step 12 — Return**

```
return {    "message": "Password reset successfully"}
```

# **48. Password reset workflow**

## **Password Reset**

**1. User requests reset**

POST `/password-reset/request`

↓

**2. Server finds user**

↓

**3. Generate secure random token**

↓

**4. Store token with expiry**

10 minutes

↓

**5. Send reset link**

Not implemented yet in your code

↓

**6. User submits new password**

POST `/password-reset/confirm`

↓

**7. Validate token**

Exists + not used + not expired

↓

**8. Hash new password**

↓

**9. Update database**

Password changed + token used

# **49.&#x20;**`users.py`**&#x20;— Understanding route-level authentication in detail**

This module contains user-related operations.

Your current endpoints:

| Method | Endpoint     | Purpose               | Authentication                     |
| ------ | ------------ | --------------------- | ---------------------------------- |
| GET    | `/me`        | Get current user      | Required                           |
| PATCH  | `/me`        | Update email          | Required                           |
| GET    | `/dashboard` | Return dashboard data | Required through router dependency |

Your router:

```
router = APIRouter(    dependencies=[Depends(get_current_user)],    tags=["users"],)
```

This means every route belonging to this router executes the authentication dependency.

## **49.1&#x20;**`GET /me`

```
@router.get("/me", response_model=UserResponse)def get_me(current_user: CurrentUser):    return current_user
```

The route itself is very simple.

Its complexity is hidden inside the dependency.

The endpoint doesn't need to know:

- How JWTs are decoded
- How the password was verified
- How the session ID was generated
- Whether the session was revoked
- How the user was retrieved

All of that is handled before the function executes.

This is an important backend design concept:

> An endpoint should focus on its actual job, while dependencies handle reusable prerequisites.

# **50.&#x20;**`PATCH /me`**&#x20;— The complete request flow**

Suppose the client sends:

```
{
  "email": "newemail@example.com"
}
```

with an access token.

The flow:

```
HTTP request
      ↓
Router dependency: get_current_user
      ↓
JWT validation
      ↓
Session revocation check
      ↓
User retrieved
      ↓
FastAPI injects current_user
      ↓
FastAPI validates UserUpdate
      ↓
update_me() executes
      ↓
Email uniqueness check
      ↓
Modify current_user.email
      ↓
session.add()
      ↓
session.commit()
      ↓
session.refresh()
      ↓
Return UserResponse
```

# **51. HTTP status codes in your project**

Understanding status codes helps you understand how the API communicates success and failure.

| Status                      | Meaning                                  | Used in your project                            |
| --------------------------- | ---------------------------------------- | ----------------------------------------------- |
| `200 OK`                    | Request succeeded                        | User endpoints, refresh, logout                 |
| `201 Created`               | New resource created                     | Registration                                    |
| `400 Bad Request`           | Request cannot be processed as submitted | Duplicate email, reset token errors             |
| `401 Unauthorized`          | Authentication failed                    | Invalid login/token                             |
| `422 Unprocessable Content` | Validation failed                        | Invalid email, malformed schema, invalid fields |

## **Example: 422**

Request:

```
{
  "email": "not-an-email",
  "password": "123"
}
```

Pydantic validation may reject the request before your route function runs.

FastAPI automatically returns a validation error response.

# **52. The most important FastAPI syntax used in your project**

Let's isolate the syntax you need to understand.

## **A. Decorators**

```
@router.post("/register")
```

A decorator modifies or registers a function.

Here, it registers the function as an HTTP endpoint.

Conceptually:

```
register = router.post("/register")(register)
```

You don't normally write this manually.

## **B. Type annotations**

```
email: EmailStr
```

This tells Python and FastAPI about the expected type.

FastAPI uses annotations to perform validation and build API documentation.

## **C. Return type annotations**

```
def hash_password(password: str) -> str:
```

Means:

```
Input password → str
Output → str
```

## **D. Union types**

```
timedelta | None
```

Means:

```
timedelta OR None
```

Equivalent older syntax:

```
Optional[timedelta]
```

## **E.&#x20;**`Annotated`

```
Annotated[Session, Depends(get_session)]
```

Adds metadata to the type.

FastAPI uses the metadata to determine how to obtain the value.

## **F.&#x20;**`Depends`

```
Depends(get_current_user)
```

Declares a dependency.

FastAPI executes the dependency and injects its result.

## **G.&#x20;**`raise`

```
raise HTTPException(...)
```

Immediately stops normal execution and generates an error response.

## **H.&#x20;**`return`

```
return current_user
```

Returns the value from the function.

## **I.&#x20;**`if`

```
if not user:
```

Conditional execution.

## **J.&#x20;**`or`

```
if not payload or not payload.get("sid"):
```

If any condition is true, the overall condition is true.

## **K. Dictionary&#x20;**`.get()`

```
payload.get("sid")
```

Gets a dictionary value.

Unlike:

```
payload["sid"]
```

`.get()` can return `None` if the key is absent instead of immediately raising `KeyError`.

## **L. Dictionary unpacking**

```
{**data, "type": "access"}
```

Copies the key/value pairs from `data` into a new dictionary and adds the other values.

## **M. Context manager**

```
with Session(engine) as session:
```

Automatically manages the resource lifecycle.

The session is closed when the block exits.

## **N. Generator**

```
yield session
```

Suspends execution and provides the session to FastAPI.

FastAPI resumes dependency cleanup after the request lifecycle.

# **53. How&#x20;**`Depends()`**&#x20;works internally — practical example**

Consider:

```
def get_me(current_user: CurrentUser):    return current_user
```

You might wonder:

> Where is `current_user` coming from? I never pass it manually.

The answer is dependency injection.

FastAPI inspects the function signature.

It sees:

```
current_user: CurrentUser
```

And your definition:

```
CurrentUser = Annotated[    User,    Depends(get_current_user),]
```

FastAPI follows the dependency.

It sees that:

```
get_current_user
```

requires:

```
session: SessionDeppayload: AccessTokenPayload
```

It then resolves those dependencies too.

So it builds a dependency graph.

\#chatgpt-mermaid-\_r_78n\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_78n\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_78n\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_78n\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_78n\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_78n\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_78n\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_78n\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_78n\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_78n\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_78n\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_78n\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_78n\_ p{margin:0;}#chatgpt-mermaid-\_r_78n\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_78n\_ .label text,#chatgpt-mermaid-\_r_78n\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .node rect,#chatgpt-mermaid-\_r_78n\_ .node circle,#chatgpt-mermaid-\_r_78n\_ .node ellipse,#chatgpt-mermaid-\_r_78n\_ .node polygon,#chatgpt-mermaid-\_r_78n\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .rough-node .label text,#chatgpt-mermaid-\_r_78n\_ .node .label text,#chatgpt-mermaid-\_r_78n\_ .image-shape .label,#chatgpt-mermaid-\_r_78n\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_78n\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .rough-node .label,#chatgpt-mermaid-\_r_78n\_ .node .label,#chatgpt-mermaid-\_r_78n\_ .image-shape .label,#chatgpt-mermaid-\_r_78n\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_78n\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_78n\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_78n\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_78n\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_78n\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_78n\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_78n\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_78n\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_78n\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_78n\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_78n\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_78n\_ .icon-shape,#chatgpt-mermaid-\_r_78n\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_78n\_ .icon-shape p,#chatgpt-mermaid-\_r_78n\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_78n\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_78n\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_78n\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_78n\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_78n\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_78n\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_78n\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_78n\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_78n\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_78n\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_78n\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_78n\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_78n\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_78n\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_78n\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_78n\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .node rect,#chatgpt-mermaid-\_r_78n\_ .node circle,#chatgpt-mermaid-\_r_78n\_ .node ellipse,#chatgpt-mermaid-\_r_78n\_ .node polygon,#chatgpt-mermaid-\_r_78n\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_78n\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_78n\_ .mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_78n\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_78n\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_78n\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}GET /meget_me()CurrentUserget_current_user()SessionDepAccessTokenPayloadget_access_token_payload()oauth2_schemeExtract Bearer TokenDecode and Validate JWTCheck Revoked SessionQuery User DatabaseInject User

This is not merely a function call.

FastAPI builds and resolves the dependency tree automatically.

# **54. Complete API endpoint reference**

## **Your current API**

Authentication

**POST&#x20;**`/register`

Create an account.

**POST&#x20;**`/token`

Login and obtain access and refresh tokens.

**POST&#x20;**`/token/refresh`

Obtain a new access token.

**POST&#x20;**`/logout`

Revoke the current session.

Users

**GET&#x20;**`/me`

Retrieve the authenticated user's details.

**PATCH&#x20;**`/me`

Update the authenticated user's email.

**GET&#x20;**`/dashboard`

Get dashboard data. Authenticated through router-level dependency.

Password Reset

**POST&#x20;**`/password-reset/request`

Request a password reset.

**POST&#x20;**`/password-reset/confirm`

Confirm reset and change password.

# **55. Let's simulate a complete user**

We'll use:

```
Email: nik@example.com
Password: MyPassword123
```

## **Step 1 — Registration**

Client:

```
POST /register
```

Body:

```
{
  "email": "nik@example.com",
  "password": "MyPassword123"
}
```

Backend:

```
Validate email/password
       ↓
Check whether email exists
       ↓
Hash password
       ↓
Create User
       ↓
Save to database
```

Database:

```
users
────────────────────────────────────
id | email        | hashed_password | role
1  | nik@...      | $argon2...    | user
```

Response:

```
{
  "id": 1,
  "email": "nik@example.com",
  "role": "user"
}
```

## **Step 2 — Login**

Client:

```
POST /token
```

Form data:

```
username=nik@example.com
password=MyPassword123
```

Backend:

```
Find user
     ↓
Verify password
     ↓
Generate sid
     ↓
Create access token
     ↓
Create refresh token
     ↓
Return tokens
```

Response:

```
{
  "access_token": "ACCESS_JWT",
  "refresh_token": "REFRESH_JWT",
  "token_type": "bearer"
}
```

## **Step 3 — Request protected profile**

Client:

```
GET /me
Authorization: Bearer ACCESS_JWT
```

Backend:

```
Extract token
      ↓
Decode token
      ↓
Validate signature and expiration
      ↓
Check type = access
      ↓
Check sid exists
      ↓
Check session isn't revoked
      ↓
Read sub
      ↓
Find user
      ↓
Inject CurrentUser
      ↓
Execute get_me()
      ↓
Return user
```

Response:

```
{
  "id": 1,
  "email": "nik@example.com",
  "role": "user"
}
```

## **Step 4 — Access token expires**

After 10 minutes:

```
Access token
      ↓
exp reached
      ↓
Invalid for new authenticated requests
```

Client can use the refresh token.

## **Step 5 — Refresh**

Client:

```
POST /token/refresh
```

Body:

```
{
  "refresh_token": "REFRESH_JWT"
}
```

Backend:

```
Decode refresh token
      ↓
Check type = refresh
      ↓
Check session revocation
      ↓
Find user
      ↓
Generate access token
      ↓
Return new access token
```

## **Step 6 — Logout**

Client:

```
POST /logout
Authorization: Bearer ACCESS_JWT
```

Backend:

```
Authenticate request
      ↓
Get sid
      ↓
Remove expired revoked-session records
      ↓
Insert sid into revoked_sessions
      ↓
Commit
      ↓
Return Logged out
```

## **Step 7 — Try using the old token**

Client:

```
GET /me
Authorization: Bearer ACCESS_JWT
```

Backend:

```
JWT valid?
       ↓
Yes
       ↓
Session revoked?
       ↓
Yes
       ↓
Reject 401
```

This is your entire authentication lifecycle.

# **56. What is happening when a protected request arrives? — Deep execution trace**

Let's trace this actual request:

```
GET /me
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
```

This is where all your concepts come together.

## **Execution, step by step**

### **① FastAPI receives the request**

The ASGI server receives the HTTP request and passes it to FastAPI.

```
GET /me
```

FastAPI identifies the matching route.

### **② Router-level dependency runs**

Your `users` router contains:

```
dependencies=[Depends(get_current_user)]
```

So authentication is required before the endpoint can successfully execute.

### **③ Endpoint requires&#x20;**`CurrentUser`

```
def get_me(current_user: CurrentUser):
```

FastAPI inspects the annotation.

It discovers:

```
CurrentUser = Annotated[User, Depends(get_current_user)]
```

Therefore, it needs to execute `get_current_user`.

### **④ FastAPI executes&#x20;**`get_current_user`

```
def get_current_user(    session: SessionDep,    payload: AccessTokenPayload,):
```

It now needs two values.

- A database session
- A validated token payload

### **⑤ FastAPI creates the database session**

```
SessionDep = Annotated[Session, Depends(get_session)]
```

FastAPI executes:

```
get_session()
```

The session becomes available.

### **⑥ FastAPI executes&#x20;**`get_access_token_payload`

```
AccessTokenPayload = Annotated[    dict,    Depends(get_access_token_payload),]
```

FastAPI resolves the token dependency.

### **⑦&#x20;**`oauth2_scheme`**&#x20;extracts the token**

```
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

It reads:

```
Authorization: Bearer eyJ...
```

And extracts:

```
eyJ...
```

### **⑧ JWT is decoded**

```
payload = decode_token(token)
```

The signature and token validity are checked.

### **⑨ Token claims are validated**

```
payload.get("type") == "access"payload.get("sid")payload.get("sub")
```

The token must be an access token and contain the required claims.

### **⑩ Session revocation is checked**

```
session.get(RevokedSession, session_id)
```

If the session has been revoked, the request fails.

### **⑪ User is retrieved from the database**

```
user = session.exec(    select(User).where(User.email == email)).first()
```

### **⑫ User is injected**

The dependency returns:

```
return user
```

FastAPI injects it into:

```
current_user
```

### **⑬ The endpoint finally executes**

```
def get_me(current_user: CurrentUser):    return current_user
```

### **⑭ Response is serialized**

FastAPI converts the result to JSON and applies:

```
response_model=UserResponse
```

The response is sent back.

DatabaseSecurityOAuth2 SchemeFastAPIClientDatabaseSecurityOAuth2 SchemeFastAPIClient#chatgpt-mermaid-\_r_7f8\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_7f8\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_7f8\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_7f8\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_7f8\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_7f8\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_7f8\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_7f8\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_7f8\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_7f8\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_7f8\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_7f8\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_7f8\_ p{margin:0;}#chatgpt-mermaid-\_r_7f8\_ .actor{stroke:rgb(31, 78, 148);fill:rgb(9, 23, 44);stroke-width:1;}#chatgpt-mermaid-\_r_7f8\_ rect.actor.outer-path[data-look="neo"]{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ rect.note[data-look="neo"]{stroke:rgb(58, 132, 63);fill:rgb(48, 48, 48);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ text.actor>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_7f8\_ .actor-line{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ .innerArc{stroke-width:1.5;stroke-dasharray:none;}#chatgpt-mermaid-\_r_7f8\_ .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ [id$="-arrowhead"] path{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ .sequenceNumber{fill:#505050;}#chatgpt-mermaid-\_r_7f8\_ [id$="-sequencenumber"]{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ [id$="-crosshead"] path{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_7f8\_ .messageText{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_7f8\_ .labelBox{stroke:rgba(255, 255, 255, 0.15);fill:rgb(0, 0, 0);filter:none;}#chatgpt-mermaid-\_r_7f8\_ .labelText,#chatgpt-mermaid-\_r_7f8\_ .labelText>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_7f8\_ .loopText,#chatgpt-mermaid-\_r_7f8\_ .loopText>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_7f8\_ .sectionTitle,#chatgpt-mermaid-\_r_7f8\_ .sectionTitle>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_7f8\_ .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:rgba(255, 255, 255, 0.15);fill:rgba(255, 255, 255, 0.15);}#chatgpt-mermaid-\_r_7f8\_ .note{stroke:rgb(58, 132, 63);fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_7f8\_ .noteText,#chatgpt-mermaid-\_r_7f8\_ .noteText>tspan{fill:rgb(237, 237, 237);stroke:none;font-weight:normal;}#chatgpt-mermaid-\_r_7f8\_ .activation0{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_7f8\_ .activation1{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_7f8\_ .activation2{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_7f8\_ .actorPopupMenu{position:absolute;}#chatgpt-mermaid-\_r_7f8\_ .actorPopupMenuPanel{position:absolute;fill:rgb(9, 23, 44);box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#chatgpt-mermaid-\_r_7f8\_ .actor-man circle,#chatgpt-mermaid-\_r_7f8\_ line{fill:rgb(9, 23, 44);stroke-width:2px;}#chatgpt-mermaid-\_r_7f8\_ g rect.rect{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_7f8\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_7f8\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_7f8\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_7f8\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_7f8\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_7f8\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_7f8\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}GET /me + Bearer JWTExtract tokenJWT stringdecode_token(JWT)PayloadValidate type, sid, subCheck revoked sessionNot revokedFind User by subUser objectInject CurrentUserExecute get_me()200 + UserResponse JSON

# **57. Authentication vs. authorization in your project**

These are two different concepts.

## **Authentication**

> Who are you?

Your application establishes identity through:

```
Password
   ↓
Login
   ↓
JWT
   ↓
Current user
```

Examples:

```
get_current_user()
```

is authentication-related.

## **Authorization**

> Are you allowed to do this?

For example:

```
User
   ↓
Can view their own profile? → Yes

User
   ↓
Can delete every other account? → No

Admin
   ↓
Can delete users? → Maybe, if permission allows
```

Your model contains:

```
role: str = Field(default="user")
```

But your code currently doesn't implement role-based permission checks.

You have the foundation for roles, but not the actual authorization system.

For example, a future dependency could check:

```
if current_user.role != "admin":    raise HTTPException(status_code=403)
```

The distinction:

|           | Authentication     | Authorization              |
| --------- | ------------------ | -------------------------- |
| Question  | Who are you?       | What can you do?           |
| Mechanism | Credentials/tokens | Roles/permissions/policies |
| Result    | User identity      | Permission decision        |
| Example   | Valid JWT          | Can access admin endpoint? |

# **58. Every major function — quick reference**

## **Function map**

Application

`lifespan()` — application startup/shutdown lifecycle

`create_db_and_tables()` — creates missing database tables

Database

`get_session()` — provides database session

Security

`hash_password()` — converts plaintext password to secure hash

`verify_password()` — checks supplied password against stored hash

`create_access_token()` — generates short-lived JWT

`create_refresh_token()` — generates long-lived refresh JWT

`decode_token()` — validates and decodes JWT

Authentication dependencies

`_invalid_token_exception()` — standard invalid-token error

`get_access_token_payload()` — validates access-token claims

`get_current_user()` — validates session and retrieves user

Authentication routes

`register()` — creates account

`login()` — verifies credentials and creates tokens

`refresh_token()` — creates new access token

`logout()` — revokes session

User routes

`get_me()` — returns authenticated user

`update_me()` — changes user email

`dashboard()` — returns dashboard data

Password reset

`request_password_reset()` — creates reset token

`confirm_password_reset()` — verifies token and updates password

# **59. How your database looks after using the API**

After a user registers and logs in, the database might look conceptually like this:

## `users`

| id | email            | hashed_password | role |
| -- | ---------------- | --------------- | ---- |
| 1  | nik\@example.com | `$argon2...`    | user |

## `revoked_sessions`

After logout:

| session_id | expires_at    |
| ---------- | ------------- |
| `c1df...`  | 2026-11-28... |

## `password_reset_token`

After requesting a password reset:

| id | user_id | token        | expires_at | used  |
| -- | ------- | ------------ | ---------- | ----- |
| 1  | 1       | Random token | 10 minutes | False |

# **60. Your project's current strengths**

This implementation already contains several useful security concepts.

- Passwords are hashed rather than stored in plaintext.
- Password verification uses a dedicated password-hashing library.
- JWTs have expiration.
- Access and refresh tokens have different types.
- Access tokens are short-lived.
- Login generates a session identifier.
- Protected endpoints use dependency injection.
- Tokens are checked against session revocation.
- Logout revokes the session server-side.
- User responses use a separate schema instead of exposing the database model directly.
- Password-reset tokens expire.
- Password-reset tokens are marked as used.
- Password-reset requests use a generic response to reduce account enumeration.
- Unknown users undergo dummy password verification to reduce timing differences.

These are valuable foundations.

# **61. Important issues I found in your actual code**

This is where understanding the code becomes more valuable than simply memorizing it.

**Security issues and improvements**

These are observations from your implementation, not just generic recommendations.

## **1. JWT secret has been exposed**

Your uploaded `.env` contains the JWT signing secret.

Rotate it immediately.

Anyone possessing the secret could potentially forge JWTs signed using your algorithm and claims.

For this project:

- Generate a new random secret.
- Replace the old secret in `.env`.
- Never commit `.env` to Git.
- Add `.env` to `.gitignore`.
- Keep `.env.example` containing only placeholder values.

Example placeholder:

```
JWT_SECRET_KEY=replace_with_a_secure_random_secret
```

A real secret should be generated securely, not typed manually.

## **2. Password maximum length is only 12 characters**

In `schemas.py`:

```
password: str = Field(min_length=1, max_length=12)
```

And the password-reset schema has the same maximum.

This is unnecessarily restrictive for a modern password system.

A better policy generally permits longer passwords or passphrases, while also avoiding excessive input sizes that can create denial-of-service risks.

For example, consider a reasonable limit around 128 characters, with the exact policy chosen carefully.

## **3. Reset token is stored in plaintext**

Your model:

```
token: str = Field(unique=True, index=True)
```

And the reset endpoint saves:

```
token=token
```

If your database is compromised, an attacker could potentially obtain active password reset tokens.

A better production design stores a hash of the reset token and compares the hash of the submitted token.

The actual reset token is sent to the user, but only its hash is stored server-side.

## **4. Password-reset email delivery isn't implemented**

Your code contains:

```
# Send the reset link through the configured email provider.
```

But no email provider is connected.

Currently:

- Token generated
- Token stored
- Generic response returned

The user never receives the reset link through the application.

## **5. Password reset doesn't revoke existing sessions**

After:

```
user.hashed_password = hash_password(payload.new_password)
```

the password changes.

However, existing access and refresh tokens remain associated with the session IDs they already have.

Your revoked-session system could be used to invalidate existing sessions after password reset, but the current password-reset code does not do that.

A production password reset should normally invalidate or otherwise re-evaluate existing sessions.

## **6. Email change can affect existing JWTs**

Your JWT subject is:

```
sub = user.email
```

Your current-user dependency retrieves the user using:

```
User.email == email
```

When the email changes:

```
current_user.email = update_payload.email
```

old JWTs still contain the old email.

Subsequent requests may fail to find the user.

This effectively invalidates those tokens, but it also creates a potentially surprising behavior.

A more stable subject is often a user ID:

```
{
  "sub": "1"
}
```

or a UUID.

That way, changing email doesn't change the identity represented by the token.

## **7. The dashboard currently returns static data**

```
@router.get("/dashboard")def dashboard():    return {"Profit": 1_00_000}
```

This is clearly demonstration data.

The router is protected, but the endpoint isn't actually retrieving user-specific dashboard data.

## **8. You have a role field but no permission system**

```
role: str = Field(default="user")
```

Currently, a role exists in the database.

But you don't have:

- Role dependency
- Permission checking
- Admin endpoint protection
- Role-based authorization

The role field alone doesn't provide authorization.

## **9. Registration has a race condition possibility**

Your registration logic:

```
existing_user = session.exec(    select(User).where(User.email == user_data.email)).first()if existing_user:    raise HTTPException(...)session.add(new_user)session.commit()
```

Two requests could theoretically arrive simultaneously:

```
Request A → checks email → doesn't exist
Request B → checks email → doesn't exist
Request A → inserts
Request B → attempts insert
```

The database's unique constraint helps protect the email, but you should also handle the resulting database integrity error cleanly.

## **10. Refresh token rotation is not implemented**

Your refresh endpoint returns a new access token.

It does not issue a new refresh token or rotate the existing refresh token.

Refresh-token rotation is a useful security improvement for systems where refresh-token theft and reuse are important concerns.

## **11. Password-reset token expiration handling should be cleaned up**

Your code:

```
reset_token.expires_at < datetime.now(UTC).replace(tzinfo=None)
```

This converts the current time to a timezone-naive datetime.

SQLite commonly returns naive datetimes from stored records, which is why this can work with your current implementation.

However, mixing timezone-aware and timezone-naive datetimes is fragile.

It's better to standardize your datetime storage and comparison strategy.

## **12. Authentication is not the same as authorization**

Your current dependencies answer:

> Is this a valid authenticated user?

They don't automatically answer:

> Is this user allowed to perform this action?

For example, your `PATCH /me` endpoint correctly operates on `current_user`, but if you later introduce:

```
DELETE /users/5
```

you must implement permission logic separately.

# **62. How to test this entire project in Swagger or Postman**

Swagger is available at:

```
http://127.0.0.1:8000/docs
```

Start the application from your project root:

```
uv run fastapi dev app/main.py
```

Your README describes this command and the `/docs` interface.&#x20;

pyproject.toml



## **Test 1 — Register**

POST /register

Request body → JSON

```
{
  "email": "nik@example.com",
  "password": "mypassword"
}
```

Expected:

```
201 Created
```

Response:

```
{
  "id": 1,
  "email": "nik@example.com",
  "role": "user"
}
```

## **Test 2 — Login**

POST /token

Request body → Form URL Encoded

```
username = nik@example.com
password = mypassword
```

Expected response:

```
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

Copy the access token.

## **Test 3 — Get current user**

```
GET /me
```

Header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

Expected:

```
{
  "id": 1,
  "email": "nik@example.com",
  "role": "user"
}
```

## **Test 4 — Update email**

```
PATCH /me
```

Header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

Body:

```
{
  "email": "niknew@example.com"
}
```

Expected:

```
{
  "id": 1,
  "email": "niknew@example.com",
  "role": "user"
}
```

## **Test 5 — Refresh token**

```
POST /token/refresh
```

Body:

```
{
  "refresh_token": "<REFRESH_TOKEN>"
}
```

Expected:

```
{
  "access_token": "...",
  "token_type": "bearer"
}
```

## **Test 6 — Logout**

```
POST /logout
```

Header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

Expected:

```
{
  "detail": "Logged out"
}
```

## **Test 7 — Try using the token after logout**

```
GET /me
```

Use the old token.

Expected:

```
401 Unauthorized
```

This confirms your revocation mechanism is functioning.

## **Test 8 — Request password reset**

```
POST /password-reset/request
```

Body:

```
{
  "email": "nik@example.com"
}
```

Expected:

```
{
  "message": "If an account exists with this email, a reset link has been sent"
}
```

Currently, no email will actually be sent.

## **Test 9 — Confirm password reset**

Once you obtain a token from the database for testing:

```
POST /password-reset/confirm
```

Body:

```
{
  "token": "your-reset-token",
  "new_password": "newpassword"
}
```

Expected:

```
{
  "message": "Password reset successfully"
}
```

# **63. Final mental model — understand your project in one picture**

# **64. The whole system in 15 steps**

Memorize this sequence:

1. **Application starts** → `main.py`
2. **Lifespan executes** → database tables are created
3. **Routers register** → authentication, users, password reset
4. **Client registers** → `POST /register`
5. **Request validated** → `UserCreate`
6. **Password hashed** → `hash_password()`
7. **User saved** → SQLModel session
8. **Client logs in** → `POST /token`
9. **Password verified** → `verify_password()`
10. **Session ID generated** → `uuid4()`
11. **JWTs created** → access + refresh
12. **Client calls protected route** → Bearer token
13. **Dependencies authenticate** → token, session, user
14. **Route executes** → `CurrentUser` injected
15. **Refresh/logout/reset** → token/session/password lifecycle management

# **65. What you should actually remember for interviews and real backend work**

If you understand these concepts, you understand the core of your project:

| Concept                | What you should be able to explain                |
| ---------------------- | ------------------------------------------------- |
| `FastAPI`              | Creates APIs and handles requests                 |
| `APIRouter`            | Groups endpoints into modules                     |
| `SQLModel`             | Defines database models and interacts with the DB |
| `Session`              | Manages database operations and transactions      |
| `Pydantic`             | Validates incoming and outgoing data              |
| `Depends()`            | Dependency injection                              |
| `Annotated`            | Attaches dependency metadata to a type            |
| `PasswordHash`         | Hashes and verifies passwords                     |
| `JWT`                  | Signed token representing claims                  |
| `Access token`         | Short-lived credential for protected APIs         |
| `Refresh token`        | Credential used to obtain new access tokens       |
| `OAuth2PasswordBearer` | Extracts Bearer tokens from requests              |
| `get_current_user`     | Converts a validated token into a database user   |
| `RevokedSession`       | Makes logout possible before token expiration     |
| `401`                  | Authentication failure                            |
| `403`                  | Authenticated but not permitted                   |
| `Authentication`       | Establishing identity                             |
| `Authorization`        | Checking permissions                              |

## **The single most important concept in this codebase**

Everything revolves around this:

```
current_user: CurrentUser
```

When you see that in a FastAPI endpoint, don't think:

> It is just a parameter.

Think:

```
HTTP Request
      ↓
Bearer token
      ↓
Token extraction
      ↓
JWT validation
      ↓
Token type validation
      ↓
Session validation
      ↓
Revocation check
      ↓
Database user lookup
      ↓
CurrentUser injected
      ↓
Endpoint executes
```

That is the actual machinery of authentication in your project.

Your next step should be to understand this dependency chain deeply enough that you can recreate it without looking at the code. Then, when you encounter authentication in a different FastAPI project, you'll recognize the same architecture immediately.

**This is your complete conceptual map of the Authentication application.** We can next go even deeper into the code itself—function by function, with execution traces and actual request/response examples, particularly the dependency chain and JWT internals.