INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> 000000000001, initial schema
-- Running upgrade  -> 000000000001

CREATE TABLE empresa (
    id UUID NOT NULL, 
    nombre_comercial VARCHAR NOT NULL, 
    razon_social VARCHAR, 
    cuit VARCHAR, 
    domicilio VARCHAR, 
    telefono VARCHAR, 
    email VARCHAR, 
    logo_url VARCHAR, 
    datos_fiscales JSON, 
    configuracion_general JSON, 
    parametros_operativos JSON, 
    activa BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_empresa_cuit ON empresa (cuit);

CREATE TABLE rol (
    id UUID NOT NULL, 
    nombre VARCHAR NOT NULL, 
    permisos JSON, 
    empresa_id UUID, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(empresa_id) REFERENCES empresa (id)
);

CREATE INDEX ix_rol_empresa_id ON rol (empresa_id);

CREATE TABLE usuario (
    id UUID NOT NULL, 
    empresa_id UUID, 
    email VARCHAR NOT NULL, 
    contrasena_hash VARCHAR NOT NULL, 
    nombre VARCHAR, 
    apellido VARCHAR, 
    rol_id UUID NOT NULL, 
    activo BOOLEAN NOT NULL, 
    ultimo_acceso TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(empresa_id) REFERENCES empresa (id), 
    FOREIGN KEY(rol_id) REFERENCES rol (id), 
    UNIQUE (email)
);

CREATE UNIQUE INDEX ix_usuario_email ON usuario (email);

CREATE INDEX ix_usuario_empresa_id ON usuario (empresa_id);

INSERT INTO alembic_version (version_num) VALUES ('000000000001') RETURNING alembic_version.version_num;

COMMIT;

