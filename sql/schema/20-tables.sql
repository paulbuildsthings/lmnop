CREATE TABLE lmnop.authn (
    id int GENERATED ALWAYS AS IDENTITY,
    name text NOT NULL UNIQUE,
    password text,
    enabled boolean NOT NULL DEFAULT TRUE,
    created_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (id)
);
CREATE TABLE lmnop_history.authn (deleted boolean NOT NULL DEFAULT FALSE, LIKE lmnop.authn, UNIQUE (id, updated_at));

CREATE TABLE lmnop.project (
    id int GENERATED ALWAYS AS IDENTITY,
    name text NOT NULL UNIQUE,
    size bigint NOT NULL,
    configuration jsonb NOT NULL,
    marked_for_delete boolean NOT NULL DEFAULT FALSE,
    created_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (id)
);
CREATE TABLE lmnop_history.project (deleted boolean NOT NULL DEFAULT FALSE, LIKE lmnop.project, UNIQUE (id, updated_at));

CREATE TABLE lmnop.deployment (
    id int GENERATED ALWAYS AS IDENTITY,
    deployed_at timestamp with time zone NOT NULL DEFAULT statement_timestamp(),
    authn_name text NOT NULL,
    project_name text NOT NULL,
    project_size bigint,
    timer float NOT NULL default 0.0,
    configuration jsonb NOT NULL,
    errors text,
    PRIMARY KEY (id)
);
