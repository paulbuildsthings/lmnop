CREATE TABLE lmnop.log_password (
    timestamp timestamp with time zone DEFAULT statement_timestamp() NOT NULL,
    username text NOT NULL,
    ip inet,
    useragent text
)
PARTITION BY RANGE (timestamp);

CREATE TABLE lmnop.log_deployment (
    timestamp timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    authn_username text NOT NULL,
    function_name text NOT NULL,
    function_size bigint,
    timer float NOT NULL default 0.0,
    configuration jsonb NOT NULL,
    errors text
)
PARTITION BY RANGE (timestamp);

CREATE TABLE lmnop.authn (
    id int GENERATED ALWAYS AS IDENTITY,
    username text NOT NULL UNIQUE,
    password text,
    enabled boolean NOT NULL DEFAULT TRUE,
    created_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (id)
);
CREATE TABLE lmnop.authn_history (deleted boolean NOT NULL DEFAULT FALSE, LIKE lmnop.authn, UNIQUE (id, updated_at));

CREATE TABLE lmnop.function (
    id int GENERATED ALWAYS AS IDENTITY,
    name text NOT NULL UNIQUE,
    size bigint NOT NULL,
    configuration jsonb NOT NULL,
    marked_for_delete boolean NOT NULL DEFAULT FALSE,
    created_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (id)
);
CREATE TABLE lmnop.function_history (deleted boolean NOT NULL DEFAULT FALSE, LIKE lmnop.function, UNIQUE (id, updated_at));
