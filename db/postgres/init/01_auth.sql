-- Schema auth: platform users (Market staff), roles and service accounts. Owned by auth_svc.
CREATE SCHEMA auth AUTHORIZATION auth_svc;
SET search_path = auth;

CREATE TABLE users (
    id             serial PRIMARY KEY,
    email          text NOT NULL UNIQUE,
    password_hash  text NOT NULL,                 -- bcrypt, never plain text
    is_active      boolean NOT NULL DEFAULT true,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE roles (
    id           serial PRIMARY KEY,
    name         text NOT NULL UNIQUE,
    description  text
);

CREATE TABLE user_roles (
    user_id  integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id  integer NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    PRIMARY KEY (user_id, role_id)
);

-- Refresh tokens are stored hashed so a database leak does not leak sessions
CREATE TABLE refresh_tokens (
    id          bigserial PRIMARY KEY,
    user_id     integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  text NOT NULL UNIQUE,
    expires_at  timestamptz NOT NULL,
    revoked     boolean NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Technical accounts for service-to-service calls (role service_account)
CREATE TABLE service_accounts (
    id          serial PRIMARY KEY,
    name        text NOT NULL UNIQUE,              -- e.g. orders-service
    api_key_hash text NOT NULL,
    role_id     integer NOT NULL REFERENCES roles(id),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Audit of refused calls (401 / 403), useful for the defense
CREATE TABLE access_log (
    id          bigserial PRIMARY KEY,
    at          timestamptz NOT NULL DEFAULT now(),
    subject     text,
    action      text NOT NULL,
    status_code smallint NOT NULL CHECK (status_code IN (401, 403))
);

INSERT INTO roles (name, description) VALUES
  ('admin',           'Platform owner: read and write everything, manage users'),
  ('catalog_manager', 'Catalog team: create and edit products and prices'),
  ('analyst',         'BI and marketing: read only'),
  ('logistics',       'Logistics team: read orders, update stock and warehouses'),
  ('service_account', 'Technical account used by another service');

ALTER TABLE users OWNER TO auth_svc;
ALTER TABLE roles OWNER TO auth_svc;
ALTER TABLE user_roles OWNER TO auth_svc;
ALTER TABLE refresh_tokens OWNER TO auth_svc;
ALTER TABLE service_accounts OWNER TO auth_svc;
ALTER TABLE access_log OWNER TO auth_svc;
ALTER ROLE auth_svc SET search_path = auth;
