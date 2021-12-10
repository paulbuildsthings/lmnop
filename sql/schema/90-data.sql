DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_catalog.pg_available_extensions WHERE name = 'pg_partman') THEN
            CREATE SCHEMA partman;
            CREATE EXTENSION pg_partman SCHEMA partman;

            DELETE FROM partman.part_config WHERE parent_table = 'lmnop.log_password';
            DELETE FROM partman.part_config WHERE parent_table = 'lmnop.log_deployment';

            DROP TABLE IF EXISTS partman.template_lmnop_log_password;
            DROP TABLE IF EXISTS partman.template_lmnop_log_deployment;

            SELECT partman.create_parent(
                           p_parent_table := 'lmnop.log_password',
                           p_control := 'timestamp',
                           p_type := 'native',
                           p_interval := 'monthly',
                           p_start_partition := '2020-08-01'
                       );
            SELECT partman.create_parent(
                           p_parent_table := 'lmnop.log_deployment',
                           p_control := 'timestamp',
                           p_type := 'native',
                           p_interval := 'monthly',
                           p_start_partition := '2020-08-01'
                       );

            DROP TABLE lmnop.log_password_default;
            DROP TABLE lmnop.log_deployment_default;

            UPDATE partman.part_config SET retention = '1 year', retention_keep_table = false WHERE parent_table = 'lmnop.log_password';
            UPDATE partman.part_config SET retention = '1 year', retention_keep_table = false WHERE parent_table = 'lmnop.log_deployment';
        ELSE
            CREATE TABLE lmnop.log_password_default PARTITION OF lmnop.log_password DEFAULT;
            CREATE TABLE lmnop.log_deployment_default PARTITION OF lmnop.log_deployment DEFAULT;
        END IF;
    END
$$;

-- username: test
-- password: test
INSERT INTO lmnop.authn (username, password) VALUES ('test', '$2y$05$N.HFY.EySskL2QD6Ma8fCOtgFTnj0KGkocK.JUqgkTOQfJ9zEXeoC');
