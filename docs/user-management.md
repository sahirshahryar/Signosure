## APIs for user management
**Note**: In theory, it should be possible to substitute in a third-party authentication service (i.e., use OAuth 2.0) so that users don't have to create dedicated accounts to use the platform.

```
User {
  username: utf8
  email: utf8
  confirmation_token: utf8?    # null if email confirmed
  oauth: bool                  # true if using OAuth account
  password_hash: utf8?         # null if oauth
  password_salt: utf8?         # null if oauth
  permissions: utf8[]          # array of permission strings
}
```


`POST api/v1/users/create`
```
CreateUserStandardRequest {
  username: utf8
  password: utf8
}

CreateUserOAuthRequest {

}

CreateUserResponse {

}
```
