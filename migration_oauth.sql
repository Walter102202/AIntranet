-- Migration script to add OAuth support to usuarios table
-- Database: mi_database

USE mi_database;

-- Add OAuth-related columns to usuarios table
ALTER TABLE usuarios
    -- OAuth provider (microsoft, google, or NULL for traditional login)
    ADD COLUMN oauth_provider ENUM('microsoft', 'google') NULL DEFAULT NULL AFTER password_hash,
    -- OAuth user ID from the provider
    ADD COLUMN oauth_id VARCHAR(255) NULL DEFAULT NULL AFTER oauth_provider,
    -- Make password_hash nullable for OAuth users
    MODIFY password_hash VARCHAR(255) NULL;

-- Add index for OAuth lookups
ALTER TABLE usuarios
    ADD INDEX idx_oauth (oauth_provider, oauth_id);

-- Add unique constraint for oauth_provider + oauth_id combination
ALTER TABLE usuarios
    ADD CONSTRAINT unique_oauth_user UNIQUE (oauth_provider, oauth_id);
