## ADDED Requirements

### Requirement: Login page renders and submits credentials
The system SHALL display a login page at `/login` with email and password fields. Upon submission, it SHALL call `POST /auth/login` and, on success, store the access token in `localStorage`, update `authStore`, and redirect to `/`.

#### Scenario: Successful login
- **WHEN** a user enters a valid email and password and submits the login form
- **THEN** the system sends `POST /auth/login` with `{ email, password }`
- **AND** on 200 OK stores `access_token` in `localStorage`
- **AND** calls `authStore.setToken` and `authStore.setUser` with the response data
- **AND** redirects the user to `/`

#### Scenario: Invalid credentials
- **WHEN** a user submits the login form with invalid credentials
- **THEN** the system displays an error message without revealing whether the email exists
- **AND** the user remains on `/login`

#### Scenario: Inactive account
- **WHEN** a user submits the login form and the account is inactive
- **THEN** the system displays a message indicating the account is disabled
- **AND** the user remains on `/login`

#### Scenario: Navigation to password recovery
- **WHEN** a user clicks "¿Olvidaste tu contraseña?"
- **THEN** the system navigates to `/recuperar-contrasena`

### Requirement: Password recovery request page
The system SHALL display a password recovery page at `/recuperar-contrasena` with an email field. Upon submission, it SHALL call `POST /auth/recover` and display a success or error message.

#### Scenario: Successful recovery request
- **WHEN** a user enters a valid email and submits the recovery form
- **THEN** the system sends `POST /auth/recover` with `{ email }`
- **AND** displays a success message indicating an email was sent (without revealing if the email exists in the system)

#### Scenario: Invalid email format
- **WHEN** a user submits the recovery form with an invalid email format
- **THEN** the system shows a validation error before calling the API

#### Scenario: Navigation back to login
- **WHEN** a user clicks the link back to login
- **THEN** the system navigates to `/login`

### Requirement: Password reset page
The system SHALL display a password reset page at `/restablecer-contrasena` that reads `?token=` from the URL. It SHALL contain fields for new password and confirmation. Upon submission, it SHALL call `POST /auth/reset` with the token and new password. On success, it SHALL redirect to `/login`.

#### Scenario: Successful password reset
- **WHEN** a user accesses `/restablecer-contrasena?token=valid_token`, enters a matching new password and confirmation, and submits
- **THEN** the system sends `POST /auth/reset` with `{ token, new_password }`
- **AND** on success redirects to `/login`

#### Scenario: Password mismatch
- **WHEN** a user enters a new password and a different confirmation password
- **THEN** the system shows a validation error and does not submit

#### Scenario: Weak password
- **WHEN** a user enters a new password with fewer than 8 characters
- **THEN** the system shows a validation error and does not submit

#### Scenario: Expired or invalid token
- **WHEN** the system sends `POST /auth/reset` with an expired or invalid token
- **THEN** it displays an error message indicating the link is invalid or expired
- **AND** offers a link to request a new recovery
