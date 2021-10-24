CREATE OR REPLACE FUNCTION standard.distinct() RETURNS trigger
    LANGUAGE plpgsql
AS $$
/*
    Function:     standard.distinct_modified()
    Description:  Trigger function that will drop an update that does not
                  modify any column on the row. This will prevent the creation
                  of additional history records.
    Affects:      makes no changes to data
    Arguments:    none
    Returns:      If there are no changes NULL is returned which ends the
                  processing of the update on that specific row. Otherwise NEW
                  is returned (the updated row).

CREATE TRIGGER t40_distinct_updated
    BEFORE UPDATE ON {schema.table}
    FOR EACH ROW
    EXECUTE PROCEDURE standard.distinct_updated();
*/
DECLARE
BEGIN
    -- set old updated_at field to the new value
    old.updated_at := new.updated_at;

    -- don't perform update if the row has not been updated
    IF row(old.*) IS NOT DISTINCT FROM row(new.*) THEN
        RETURN NULL;
    END IF;

    -- update
    RETURN new;
END;
$$;

CREATE OR REPLACE FUNCTION standard.updated() RETURNS trigger
    LANGUAGE plpgsql
AS $$
/*
    Function:     updated()
    Description:  Trigger function for updates and inserts that sets the
                  updated_at to statement_timestamp().
    Affects:      Modifies the NEW row as described above
    Arguments:    none
    Returns:      The NEW row.

CREATE TRIGGER t50_updated
   BEFORE INSERT OR UPDATE ON {schema.table}
   FOR EACH ROW
   EXECUTE PROCEDURE standard.updated();

*/
DECLARE
BEGIN
    -- always set updated
    NEW.updated_at := statement_timestamp();

    -- only set created if we are inserting
    IF TG_OP = 'INSERT' THEN
        NEW.created_at := statement_timestamp();
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION standard.history() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
AS $$
/*  Function:     history_trigger()
    Description:  History trigger function which will take the values from an
                  INSERT, UPDATE, or DELETE and insert into the appropriate
                  history table. This function requires:

                  * the base table have the following columns:
                      - "id integer" (or int or bigint) that is the primary key
                      - "updated_at timestamp without time zone"
                  * the history table must
                      - have the same name as the base table
                      - be in the schema "{base table schema}_history"
                      - have its first column be "deleted boolean DEFAULT FALSE"
                      - and then its remaining columns must be the same as the
                        base table in the same order

                  See the example below.
    Affects:      Inserts row into the history table ({schema}_history.{table})
                  for the table on which the trigger is placed.
    Arguments:    none
    Returns:      NEW row on INSERT/UPDATE, OLD row on DELETE

CREATE TABLE public.foo (
    id         bigint GENERATED ALWAYS AS IDENTITY,
    foo        text NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamp without time zone NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (id)
);

CREATE TABLE public_history.foo (
    deleted boolean NOT NULL DEFAULT FALSE,
    LIKE public.foo,
    UNIQUE (id, updated_at)
);

CREATE TRIGGER t90_history
   AFTER INSERT OR UPDATE OR DELETE ON public.foo
   FOR EACH ROW
   EXECUTE PROCEDURE standard.history();
*/
DECLARE
    _parent_table varchar;
    _history_table varchar;
BEGIN
    _parent_table := TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME;
    _history_table := TG_TABLE_SCHEMA||'_history.'||TG_TABLE_NAME;
    IF TG_OP = 'DELETE' THEN
        OLD.updated_at := statement_timestamp();
        EXECUTE 'DELETE FROM '||_history_table||' WHERE id = '||quote_literal(OLD.id)||' AND updated_at = '||quote_literal(statement_timestamp());
        EXECUTE 'INSERT INTO '||_history_table||' VALUES (true, ('||quote_literal(OLD)||'::'||_parent_table||').*)';
        RETURN OLD;
    ELSE
        EXECUTE 'DELETE FROM '||_history_table||' WHERE id = '||quote_literal(NEW.id)||' AND updated_at = '||quote_literal(statement_timestamp());
        EXECUTE 'INSERT INTO '|| _history_table||' VALUES (false, ('||quote_literal(NEW)||'::'||_parent_table||').*)';
        RETURN NEW;
    END IF;
END;
$$;
