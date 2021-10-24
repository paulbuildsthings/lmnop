DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lmnop') THEN
            CREATE ROLE lmnop WITH LOGIN PASSWORD 'lmnop';
        END IF;
    END
$$;
