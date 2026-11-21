# Section 13 — Authorization

**Course:** FastAPI Masterclass — Boris Paskhaver  
**Topics:** Role-Based Access Control (RBAC), Admin Routes, OAuth2 Scopes, Scope-Based Route Protection

---

## Lecture 156: Role-Based Access Control

### 1. Authentication vs Authorization

- **Authentication:** Verifies who the user is.
  - Example: Logging in using email and password.
  - In our previous section, JWTs were used to represent an authenticated user.
- **Authorization:** Determines what an authenticated user is allowed to do.
  - Example: Whether a user can delete a room, view all users, or access administrative functionality.
- Authentication does not automatically grant permission to perform every action.

**Example — Rent a Room application:**

- User A creates a room.
- User B is authenticated but did not create that room.
- User B should not be allowed to delete User A's room.
- An administrator may be allowed to delete it.

### 2. Resource Ownership Authorization

- A simple authorization check can be implemented directly inside a route handler.
- Fetch the resource from the database.
- Compare its owner's foreign key with the authenticated user's ID.
- Reject the request if the IDs do not match.

```python
@router.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    current_user: CurrentUser
):
    room = get_room(room_id)

    if room.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another user's room"
        )

    # Continue with deletion
```

- `room.user_id`: Identifies the user who created the room.
- `current_user.id`: Identifies the authenticated user.
- `403 Forbidden`: The user is authenticated but lacks permission.

**Important distinction:**

- Resource ownership is an authorization rule.
- It is different from checking whether someone has an `admin` or `user` role.
- A system may need both ownership checks and role-based checks.

### 3. What Is Role-Based Access Control (RBAC)?

- **RBAC:** Role-Based Access Control.
- An authorization approach where permissions are determined by a user's assigned role.
- A role is a designation that determines what actions a user can perform.

Examples:

- `user`
- `admin`
- `manager`
- `marketing`
- `security`
- `HR`

**Course implementation:**

| Role    | Example permissions                                  |
| ------- | ---------------------------------------------------- |
| `user`  | Access normal user functionality                     |
| `admin` | Access administrative functionality and manage users |

- A regular user may view their own information.
- An administrator may view all users.
- An administrator may delete users.
- The role determines whether an action is permitted.

### 4. Existing User Model

- The course already has a `role` column in the users table.
- Previously, newly registered users received the default role `user`.
- This section expands the implementation to support both `user` and `admin`.

Conceptually:

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    hashed_password: str
    role: str = "user"
```

- The actual course model contains additional fields and configuration.
- The role is stored in the database and can be retrieved through the authenticated user's model instance.

### 5. Why Move Authorization into Dependencies?

- Writing the same authorization checks inside every route creates duplication.
- Duplicated authorization logic is harder to maintain and can lead to inconsistent security.
- FastAPI dependencies allow authorization checks to run before route-handler execution.
- A dependency can raise an exception to stop execution before the route handler runs.

**Course design:**

```text
Incoming request
      |
      v
Authentication dependency
      |
      v
Role authorization dependency
      |
      v
Route handler
      |
      v
Response
```

- If authentication fails, execution stops.
- If role validation fails, execution stops.
- The route handler executes only when the checks pass.

### 6. Python Literal Type

- The course imports `Literal` from `typing`.
- `Literal` restricts a type to a predefined set of values.

```python
from typing import Literal

Role = Literal["user", "admin"]
```

- A parameter annotated with `Role` should accept only `user` or `admin`.
- This is useful for type checking and communicating the allowed values.
- Type annotations do not replace runtime validation or database constraints.

### 7. Creating the RoleRequired Class

- The course creates a reusable class called `RoleRequired`.
- Its purpose is to ensure that a user has a particular role before accessing a route.
- The class accepts the required role when an instance is created.

```python
class RoleRequired:
    def __init__(self, role: Role):
        self.role = role
```

Example:

```python
admin_required = RoleRequired("admin")
```

- `self.role` stores the role required by this particular instance.
- The same class can be reused for different roles.

### 8. Understanding `__call__`

- A Python callable is an object that supports invocation using parentheses.
- Functions are callable.
- Classes are callable because invoking a class creates an instance.
- Ordinary instances are not automatically callable.
- Python's `__call__` magic method makes an instance callable.

```python
class RoleRequired:
    def __init__(self, role: Role):
        self.role = role

    def __call__(self, current_user: CurrentUser):
        if current_user.role != self.role:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires the {self.role} role"
            )

        return current_user
```

**What happens here?**

1. `__init__` receives and stores the required role.
2. FastAPI invokes the instance as a dependency.
3. FastAPI resolves `current_user` through its own dependency.
4. `__call__` receives the authenticated user.
5. The user's role is compared with the required role.
6. A mismatch raises HTTP 403.
7. A match returns the current user.

### 9. Dependency Chaining

- `RoleRequired` depends on `CurrentUser`.
- `CurrentUser` already depends on the authentication/JWT verification logic from Section 12.
- This creates a chain of reusable dependencies.

```text
RoleRequired("admin")
        |
        v
CurrentUser
        |
        v
JWT extraction and validation
        |
        v
Decode token and retrieve user
```

**Key takeaway:**

- Authentication establishes the user's identity.
- `RoleRequired` checks the user's role.
- The route handler receives the authenticated user only after the dependency succeeds.

---

## Lecture 157: Creating Admin Routes

### 1. Why Create a Separate Admin Router?

- Applications often contain multiple administrative endpoints.
- Examples:
  - View all users.
  - Delete a user.
  - Manage accounts.
  - Perform administrative operations.
- Instead of repeating the admin authorization dependency on every route, attach it to the router itself.

### 2. Creating the Admin Router

```python
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[
        Depends(RoleRequired("admin"))
    ]
)
```

**Explanation:**

- `APIRouter`: Groups related endpoints.
- `prefix="/admin"`: Adds `/admin` to every route in this router.
- `tags=["admin"]`: Groups endpoints under an Admin heading in Swagger UI.
- `dependencies`: Executes the specified dependencies before the route handler.

For example:

```python
@admin_router.get("/users")
```

Produces:

```text
GET /admin/users
```

### 3. Router-Level Dependencies

- A dependency attached to a router applies to all routes included in that router.
- Every request to an admin route must pass the role check.
- The route handler does not need to repeat the authorization logic.

```text
GET /admin/users
        |
        v
Admin router dependency
        |
        v
RoleRequired("admin")
        |
        v
Route handler
```

- If the current user is not an admin, FastAPI raises an exception before executing the route handler.
- This also protects future routes added to the same router.

### 4. Registering the Router

```python
app.include_router(admin_router)
```

- Including the router registers its endpoints with the main FastAPI application.
- Without registering it, defining the router alone does not expose its routes.

### 5. Example: Get All Users

```python
@admin_router.get(
    "/users",
    response_model=list[UserResponse]
)
def get_all_users(
    session: SessionDep
):
    return session.exec(
        select(User)
    ).all()
```

- The endpoint retrieves all users from the database.
- `select(User)` constructs a query for the User model.
- `session.exec()` executes the query.
- `.all()` retrieves all matching records.
- The response model controls the shape of the returned data.

**Why is this an admin route?**

- Ordinary users generally should not have unrestricted access to all users' information.
- Administrative access is enforced by the router-level dependency.

### 6. Example: Delete a User

```python
@admin_router.delete(
    "/users/{user_id}",
    response_model=UserResponse
)
def delete_user(
    user_id: int,
    session: SessionDep
):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    session.delete(user)
    session.commit()

    return user
```

**Execution flow:**

1. Receive `user_id` from the path.
2. Retrieve the corresponding user using `session.get()`.
3. If no user exists, return `404 Not Found`.
4. Queue the user for deletion using `session.delete()`.
5. Persist the deletion using `session.commit()`.
6. Return the deleted user's representation.

**Important distinction:**

| Status           | Meaning                                    |
| ---------------- | ------------------------------------------ |
| 401 Unauthorized | Authentication is missing or invalid       |
| 403 Forbidden    | User is authenticated but lacks permission |
| 404 Not Found    | Requested resource does not exist          |

### 7. Testing Admin Authorization

The instructor tests three situations:

**Case 1 — Unauthenticated user**

- No JWT is provided.
- Authentication fails.
- Request is rejected with `401 Unauthorized`.

**Case 2 — Authenticated regular user**

- User successfully logs in.
- Their role is `user`.
- Admin router requires `admin`.
- Role dependency raises `403 Forbidden`.
- Route handler never executes.

**Case 3 — Authenticated admin**

- The user's role is changed to `admin` in the database for demonstration.
- The user logs in again to obtain a token reflecting the updated role.
- Admin dependency succeeds.
- Admin route executes successfully.

**Important production consideration:**

- The instructor manually changes the database role for demonstration.
- Real applications should provide a controlled administrative process for role assignment.
- Never allow ordinary users to set their own role to `admin` through public registration or profile-update endpoints.
- Role changes should be authorized, audited and protected against privilege escalation.

### 8. Three Ways to Apply Dependencies

The instructor demonstrates three approaches.

**Approach A — Router-level dependency**

```python
admin_router = APIRouter(
    dependencies=[
        Depends(RoleRequired("admin"))
    ]
)
```

- Best when all routes in a router share the same authorization requirement.

**Approach B — Route-level dependency**

```python
@router.get(
    "/admin/users",
    dependencies=[
        Depends(RoleRequired("admin"))
    ]
)
def get_users():
    ...
```

- Useful when only one particular route needs the check.
- The dependency runs, but its returned value is not injected into the route handler.

**Approach C — Dependency as a function parameter**

```python
AdminUser = Annotated[
    User,
    Depends(RoleRequired("admin"))
]

@router.get("/admin/users")
def get_users(admin: AdminUser):
    ...
```

- Useful when the route handler needs the authenticated admin user.
- The returned value from the dependency becomes the parameter value.
- A reusable type alias avoids repeating the same dependency declaration.

**Which approach should you use?**

| Requirement                                   | Suitable approach          |
| --------------------------------------------- | -------------------------- |
| All routes in a router require admin          | Router-level               |
| One route needs admin validation only         | Route-level                |
| Route needs the validated admin user          | Parameter-level            |
| Same admin-user dependency across many routes | Reusable `Annotated` alias |

---

## Lecture 158: OAuth2 Scopes

### 1. Why Do We Need Scopes?

- RBAC controls access based on roles.
- But a role may contain multiple permissions.
- Sometimes we need more granular control over individual actions and resources.

Example:

An admin may need permission to:

- Read users.
- Create users.
- Update users.
- Delete users.

However, not every user or service that can read users should also be allowed to delete them.

**Scopes provide this finer-grained authorization.**

### 2. What Is an OAuth2 Scope?

- A scope is a string representing a specific permission.
- It describes what an authenticated client or user is allowed to do.
- Scopes are commonly represented as an action followed by a resource.

Examples:

```text
read:users
write:users
delete:users
read:payments
write:payments
```

- The exact naming convention is application-specific.
- The course uses names such as `read users`, `write users`, and `delete users`.
- A scope is a permission, whereas a role is a designation.

### 3. Role vs Scope

| Role                                | Scope                               |
| ----------------------------------- | ----------------------------------- |
| Describes a user's category         | Describes a specific permission     |
| Example: `admin`                    | Example: `delete users`             |
| Usually groups multiple permissions | Represents an individual permission |
| Controls access at a broader level  | Enables granular access control     |

Example:

```text
Role: admin

Scopes:
- read users
- write users
- delete users
```

Another role might have:

```text
Role: support

Scopes:
- read users
```

Both roles can share a permission without having the same role.

### 4. Defining Scopes in FastAPI

The course extends the existing `OAuth2PasswordBearer` configuration.

```python
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "read users": "Read users",
        "write users": "Create or update users",
        "delete users": "Delete users"
    }
)
```

**Explanation:**

- `tokenUrl`: The endpoint used to obtain the token.
- `scopes`: A dictionary describing the available permissions.
- Dictionary keys represent scope names.
- Dictionary values provide human-readable descriptions.

### 5. Scopes in Swagger UI

- FastAPI uses the scope definitions to display available permissions in the Swagger authorization interface.
- The user can select the scopes they want to request.
- These selections are submitted with the OAuth2 password form in the course implementation.
- The scope descriptions help explain what each permission represents.

**Important:** Defining scopes in `OAuth2PasswordBearer` does not automatically grant those permissions or enforce them.

It primarily declares the available scopes and supports the OAuth2 security integration.

### 6. Assigning Scopes to Users

The course uses a simplified demonstration:

1. User opens Swagger UI.
2. User selects requested scopes.
3. The token endpoint receives those requested scopes.
4. The selected scopes are included in the JWT payload.
5. Future requests can inspect the JWT to determine the user's permissions.

Conceptually:

```json
{
  "sub": "user@example.com",
  "scopes": ["read users", "delete users"]
}
```

- The `sub` claim identifies the token subject.
- The `scopes` claim contains the permissions granted to that token.

**Critical security warning from the course:**

- The demonstration grants whatever scopes the user requests.
- This is intentionally simplified and is not safe for production.
- A user must never be allowed to grant themselves privileged permissions simply by selecting them in a login form.

### 7. Production Scope Assignment

In a real application, the backend must decide which scopes a user receives.

Possible approaches:

- Derive scopes from the user's role.
- Store permissions in a database.
- Maintain a user-to-scope relationship.
- Allow administrators to assign permissions.
- Apply business rules when generating tokens.

Example:

```text
User role: support

Backend-approved scopes:
- read users
- read bookings
```

The backend should generate the token using these approved permissions, not blindly trust the scopes requested by the client.

### 8. Storing Scopes in JWTs

- The course embeds scopes directly into the JWT.
- This works with the stateless authentication approach introduced in Section 12.
- The server can read the scopes from a verified token on subsequent requests.

Example:

```python
token_data = {
    "sub": user.email,
    "scopes": granted_scopes
}
```

- The JWT must be cryptographically verified before its claims are trusted.
- JWT payloads are encoded, not encrypted.
- Do not store passwords, secrets or other sensitive information in JWT claims.

---

## Lecture 159: Scope-Based Route Protection

### 1. Role Protection Is Not Always Enough

Consider two admin routes:

```text
GET    /admin/users
DELETE /admin/users/{user_id}
```

Both require an admin role, but they need different permissions.

- Viewing users requires `read users`.
- Deleting users requires `delete users`.

The admin role alone does not distinguish between these actions.

We therefore combine:

- Role-based authorization.
- Scope-based authorization.

### 2. `Security` vs `Depends`

- FastAPI provides `Security`, which is closely related to `Depends`.
- `Security` supports OAuth2 scope requirements.
- It allows a dependency to receive the scopes required by a particular endpoint.

Conceptually:

```python
Security(
    get_current_user,
    scopes=["read users"]
)
```

- `get_current_user` performs authentication and authorization checks.
- `scopes` declares the permissions required by the endpoint.
- FastAPI passes the required scopes into the dependency through its security dependency mechanism.

### 3. Understanding `SecurityScopes`

FastAPI provides `SecurityScopes` to access the scopes required by the current request.

```python
from fastapi import Security
from fastapi.security import SecurityScopes
```

A scope-aware dependency can be structured like this:

```python
def get_current_user_with_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    ...
```

**Important concepts:**

- `security_scopes.scopes`: Contains the required scopes declared by the endpoint and its dependency chain.
- The dependency can compare these required scopes with the scopes granted in the JWT.
- If a required scope is missing, it raises an authorization exception.

### 4. Scope Validation Logic

Conceptual implementation:

```python
def get_current_user_with_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    payload = decode_token(token)

    username = payload.get("sub")
    token_scopes = payload.get("scopes", [])

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

    user = get_user_by_email(username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

    return user
```

- `security_scopes.scopes`: Permissions required by the endpoint.
- `token_scopes`: Permissions granted to the user in the token.
- The loop checks whether every required scope exists.
- If a required permission is missing, access is denied.
- If all checks pass, the authenticated user is returned.

This is a conceptual representation of the course's validation flow; retain the course's existing JWT decoding, user lookup and exception-handling implementation when applying it to the project.

### 5. Protecting Individual Routes

Example:

```python
@admin_router.get("/users")
def get_all_users(
    current_user: Annotated[
        User,
        Security(
            get_current_user_with_scopes,
            scopes=["read users"]
        )
    ],
    session: SessionDep
):
    return session.exec(select(User)).all()
```

The deletion endpoint requires a different scope:

```python
@admin_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: Annotated[
        User,
        Security(
            get_current_user_with_scopes,
            scopes=["delete users"]
        )
    ],
    session: SessionDep
):
    ...
```

- The first route requires `read users`.
- The second route requires `delete users`.
- Each route declares its own permission requirement.

### 6. Combining Role and Scope Authorization

The course retains the admin router-level dependency:

```python
admin_router = APIRouter(
    prefix="/admin",
    dependencies=[
        Depends(RoleRequired("admin"))
    ]
)
```

Individual routes then declare their scopes.

```text
Request: GET /admin/users
        |
        v
Authentication check
        |
        v
Role check: admin?
        |
        v
Scope check: read users?
        |
        v
Route handler
```

For deletion:

```text
Request: DELETE /admin/users/2
        |
        v
Authentication check
        |
        v
Role check: admin?
        |
        v
Scope check: delete users?
        |
        v
Route handler
```

**Important:**

- The role dependency is applied at the router level.
- The scope dependency is applied to individual routes.
- Both checks must succeed.
- You can use roles alone, scopes alone, or combine them depending on the application's authorization design.

---

## Lecture 160: Testing Scopes

The instructor tests combinations of roles and scopes using Swagger UI.

### Scenario 1 — Admin With No Scopes

User:

```text
Role: admin
Scopes: []
```

Request:

```text
GET /admin/users
```

Result:

- Authentication succeeds.
- Admin role check succeeds.
- Scope check fails because `read users` is missing.
- Response: `403 Forbidden`.
- Route handler does not execute.

**Lesson:** Being an admin does not automatically satisfy every scope requirement.

### Scenario 2 — Admin With Read Scope

User:

```text
Role: admin
Scopes:
- read users
```

Requests:

```text
GET /admin/users
DELETE /admin/users/2
```

Results:

| Endpoint                | Result  | Reason                 |
| ----------------------- | ------- | ---------------------- |
| `GET /admin/users`      | Allowed | Has `read users`       |
| `DELETE /admin/users/2` | Denied  | Missing `delete users` |

**Lesson:** Scopes can grant access to one operation without granting access to another.

### Scenario 3 — Admin With Both Scopes

User:

```text
Role: admin
Scopes:
- read users
- delete users
```

Results:

- Can retrieve all users.
- Can delete users.
- Both the router-level role check and individual route scope checks succeed.

### Scenario 4 — Regular User With All Scopes

User:

```text
Role: user
Scopes:
- read users
- write users
- delete users
```

Result:

- Authentication succeeds.
- Scope requirements may be satisfied.
- Admin router-level role check fails.
- The request is rejected with `403 Forbidden`.
- Scope validation does not make the user an administrator.

**Lesson:** Having a permission does not automatically satisfy a separate role requirement.

### 5. Authorization Matrix

| User | Role  | Scopes              | Admin GET | Admin DELETE |
| ---- | ----- | ------------------- | --------- | ------------ |
| A    | admin | None                | Denied    | Denied       |
| B    | admin | read users          | Allowed   | Denied       |
| C    | admin | read + delete users | Allowed   | Allowed      |
| D    | user  | read + delete users | Denied    | Denied       |

### 6. Execution Order

For the course's implementation:

1. The request reaches the admin router.
2. The router-level admin role dependency runs.
3. If the role check fails, execution stops.
4. If the role check passes, the route's scope dependency runs.
5. If scope validation fails, execution stops.
6. If all checks pass, the route handler executes.

**Key takeaway:** Authorization is layered. A request must satisfy every applicable authorization requirement.

---

## Lecture 161: Section Review

### 1. Authorization

- Authorization determines whether an authenticated user can perform a particular action.
- Authentication answers: Who are you?
- Authorization answers: What are you allowed to do?
- FastAPI does not force one specific authorization architecture.
- Developers implement authorization using dependencies, custom logic or external libraries.

### 2. Role-Based Access Control (RBAC)

- RBAC grants access based on a user's role.
- Examples: `user`, `admin`, `manager`, `support`.
- The number and meaning of roles depend on the application's requirements.
- Users may have multiple roles in more advanced implementations.

### 3. Reusable Dependencies

- Authorization logic should not be duplicated in every route handler.
- Extract it into reusable dependencies.
- Dependencies can be applied to:
  - An individual route.
  - A router.
  - A route-handler parameter through `Annotated`.
- If a dependency raises an exception, FastAPI stops the request before the route handler executes.

### 4. Callable Class Pattern

- The course implements a reusable `RoleRequired` class.
- `__init__` stores the required role.
- `__call__` makes an instance callable.
- FastAPI can execute the instance as a dependency.
- The class uses `CurrentUser` as another dependency.
- This creates a chain of authorization checks.

### 5. OAuth2 Scopes

- Scopes represent specific permissions.
- They are usually represented as strings.
- Examples:
  - `read users`
  - `write users`
  - `delete users`
- Roles describe a user's category.
- Scopes describe the actions that user can perform.
- Multiple roles can share the same scopes.

### 6. FastAPI Security

- `OAuth2PasswordBearer` declares the OAuth2 bearer-token scheme and available scopes.
- `Security` is used to declare scope requirements.
- `SecurityScopes` provides the required scopes to the dependency.
- The application implements the actual permission validation.
- FastAPI executes the dependency before the route handler.

### 7. Combining Roles and Scopes

- Role checks can provide broad access control.
- Scope checks can provide fine-grained permission control.
- Both can be combined.
- The course protects admin routes with an admin role and then applies different scopes to individual routes.

---

# Additional Backend Knowledge — Important for Production

These concepts extend the course implementation and are important when building real APIs.

## 1. Never Trust Client-Requested Permissions

The course's Swagger demonstration grants the scopes selected by the user.

This is deliberately simplified.

**Unsafe approach:**

```python
granted_scopes = form_data.scopes
```

If a normal user can request `delete users` and the server grants it without checking authorization, the user can escalate privileges.

**Safer approach:**

```python
granted_scopes = get_permissions_for_user(user)
```

- Determine permissions on the server.
- Retrieve them from trusted database records or established business rules.
- Validate the user's role and permissions before generating the JWT.
- Treat client-requested scopes as requests, not authorization decisions.

## 2. Role-Based Access Control vs Attribute-Based Access Control

RBAC is not the only authorization approach.

| Approach           | Decision based on         | Example                                                          |
| ------------------ | ------------------------- | ---------------------------------------------------------------- |
| RBAC               | User's role               | Only admins can delete users                                     |
| Scope-based        | Granted permissions       | User needs `delete users`                                        |
| ABAC               | Attributes and conditions | User can access a resource only if its department matches theirs |
| Resource ownership | Resource owner            | User can edit their own booking                                  |

Real systems often combine these approaches.

## 3. Prevent Privilege Escalation

Privilege escalation occurs when a user obtains permissions they should not have.

Examples:

- A user changes their own role to `admin`.
- A user submits privileged scopes during login.
- A user modifies another user's permissions.
- A public registration endpoint accepts a `role` field without restricting its value.

Protection:

- Assign roles on the backend.
- Do not trust role or permission values supplied by clients.
- Protect administrative operations.
- Validate authorization on every protected request.
- Audit sensitive role and permission changes.

## 4. JWT Permission Changes and Stale Tokens

Consider:

1. An admin receives a JWT containing `delete users`.
2. An administrator removes that permission from the user's database record.
3. The old JWT still contains the original scope.
4. If the application trusts only the JWT until expiration, the old permission may remain usable.

Possible solutions:

- Use short-lived access tokens.
- Rotate and revoke refresh tokens.
- Maintain a token-version or session mechanism.
- Recheck sensitive permissions against the database.
- Use a token blocklist or other revocation mechanism where required.

This is an important trade-off of embedding permissions in stateless JWTs.

## 5. Deny by Default

- Protected resources should be inaccessible unless access is explicitly granted.
- Missing permission data should not be treated as permission.
- Every sensitive endpoint should have an explicit authorization requirement.
- Avoid assuming that authentication alone makes an endpoint safe.

## 6. Separate Authentication From Authorization

Keep responsibilities clear:

```text
Authentication:
- Extract bearer token
- Verify JWT signature
- Check expiration
- Identify token subject
- Retrieve authenticated user

Authorization:
- Check role
- Check scopes
- Check resource ownership
- Apply business-specific access rules
```

This separation makes the application easier to test and maintain.

---

# Practical Exercises

### Exercise 1 — Role-Based Access

- Create a `RoleRequired` class.
- Support `user` and `admin`.
- Protect an endpoint so only admins can access it.
- Test with both roles.

### Exercise 2 — Admin Router

Create:

```text
GET    /admin/users
DELETE /admin/users/{user_id}
GET    /admin/statistics
```

- Apply one router-level admin dependency.
- Verify that regular users cannot access any of these routes.

### Exercise 3 — Scope-Based Permissions

Define:

```text
read:users
write:users
delete:users
```

- Require `read:users` for retrieving users.
- Require `write:users` for creating or updating users.
- Require `delete:users` for deleting users.
- Test each permission independently.

### Exercise 4 — Combine Roles and Scopes

- Require the `admin` role for `/admin`.
- Require `read:users` for the GET endpoint.
- Require `delete:users` for the DELETE endpoint.
- Test an admin without scopes.
- Test an admin with only one scope.
- Test a regular user with all scopes.

### Exercise 5 — Production Security

- Remove the ability for users to grant themselves arbitrary scopes.
- Assign scopes using trusted backend logic.
- Prevent users from changing their own roles.
- Add tests for unauthorized and forbidden requests.

---

# Interview Questions

**1. What is the difference between authentication and authorization?**

- Authentication verifies identity.
- Authorization verifies permissions.

**2. What is RBAC?**

- An access-control model in which permissions are assigned according to a user's role.

**3. What is the difference between a role and a scope?**

- A role is a user designation, such as admin.
- A scope is a specific permission, such as `delete users`.

**4. Why use dependencies for authorization?**

- Reusability, separation of concerns and consistent enforcement before route execution.

**5. What is the purpose of `__call__`?**

- It makes an instance of a Python class callable using parentheses.

**6. What is the difference between `Depends` and `Security`?**

- Both integrate dependencies into FastAPI.
- `Security` additionally supports OAuth2 scope requirements.

**7. What is `SecurityScopes`?**

- A FastAPI object that exposes the scopes required by the current request to a security dependency.

**8. Does defining scopes in `OAuth2PasswordBearer` enforce them automatically?**

- No. The application must implement the actual scope-validation logic.

**9. Why is granting every requested scope dangerous?**

- A client could request permissions it should not have, resulting in privilege escalation.

**10. Can an admin role and scopes be used together?**

- Yes. A router can require an admin role while individual endpoints require different scopes.

**11. What is the difference between 401 and 403?**

- 401: Authentication is missing or invalid.
- 403: Authentication succeeded, but access is forbidden.

**12. What is the risk of storing scopes in JWTs?**

- Permission changes may not take effect until the token expires or the application performs an additional revocation or permission check.

---

# Quick Revision Cheat Sheet

| Concept           | Remember                                         |
| ----------------- | ------------------------------------------------ |
| Authentication    | Who are you?                                     |
| Authorization     | What can you do?                                 |
| RBAC              | Permissions based on roles                       |
| Role              | `user`, `admin`                                  |
| Scope             | `read users`, `delete users`                     |
| `Literal`         | Restricts values to predefined options           |
| `__init__`        | Initializes and stores the required role         |
| `__call__`        | Makes a class instance callable                  |
| `RoleRequired`    | Reusable role-checking dependency                |
| `APIRouter`       | Groups related endpoints                         |
| Router dependency | Protects every route in that router              |
| `Depends`         | General dependency injection                     |
| `Security`        | Dependency integration with security scopes      |
| `SecurityScopes`  | Exposes required scopes                          |
| 401               | Authentication failure                           |
| 403               | Authorization failure                            |
| 404               | Resource not found                               |
| JWT scopes        | Permissions carried in the token                 |
| Production rule   | Never blindly trust client-requested permissions |

**Section 13 complete: Authorization.**
