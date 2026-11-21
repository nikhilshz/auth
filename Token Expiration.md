# Token Expiration

A JWT contains an `exp` claim that defines when the token becomes invalid.

## Default expiration

```python
from app.core.security import create_access_token

token = create_access_token({"sub": "nik@example.com"})
```

Without `expires_delta`, the token expires after 10 minutes.

## Custom expiration

```python
from datetime import timedelta
from app.core.security import create_access_token

token = create_access_token(
    {"sub": "nik@example.com"},
    expires_delta=timedelta(seconds=10),
)
```

The payload contains Unix timestamps:

```python
{"sub": "nik@example.com", "iat": 1795083088, "exp": 1795083098}
```

- `iat`: issued-at time
- `exp`: expiration time
- Here, the token lasts 10 seconds

## Decoding

```python
from app.core.config import settings
from app.core.security import ACCESS_TOKEN_ALGORITHM

jwt.decode(
    token,
    settings.JWT_SECRET_KEY,
    algorithms=[ACCESS_TOKEN_ALGORITHM],
)
```

If the token expires before decoding, PyJWT raises:

```text
jwt.exceptions.ExpiredSignatureError: Signature has expired
```

This means the token's signature may be valid, but its `exp` value is earlier than the current time. Expired tokens are rejected.
