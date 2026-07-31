-- 1. 데이터베이스 생성
-- [주의] postgres database에서 실행할 것!!!
CREATE DATABASE movie_database
	WITH
	OWNER = 'postgres'
	ENCODING = 'UTF8'
	TEMPLATE = template0;

-- 2. 스키마 생성
-- [주의] 1번에서 생성한 movie_info 데이터베이스에서 생성할 것!!!
CREATE SCHEMA movie_info;


-- MOVIE_CODE
CREATE TABLE movie_info.movie_code (
    movie_id       VARCHAR(20)  NOT NULL,
    movie_name     VARCHAR(300) NOT NULL,
    release_date   DATE,

    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movie_code
        PRIMARY KEY (movie_id)
);


-- MOVIE_MASTER
CREATE TABLE movie_info.movie_master (
    movie_id                   VARCHAR(20)  NOT NULL,
    movie_name                 VARCHAR(300) NOT NULL,
    movie_name_en              VARCHAR(300),
    release_date               DATE,
    production_year            SMALLINT,
    movie_type                 VARCHAR(50),
    genre_production_status    VARCHAR(100),
    main_nation                VARCHAR(100),
    nations                    VARCHAR(300),

    created_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                 VARCHAR(100),
    updated_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by                 VARCHAR(100),

    CONSTRAINT pk_movie_master
        PRIMARY KEY (movie_id),

    CONSTRAINT fk_movie_master_movie_code
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_code (movie_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_movie_master_production_year
        CHECK (
            production_year IS NULL
            OR production_year BETWEEN 1800 AND 2100
        )
);

-- MOVIE_DISTRIBUTION
-- 1:N이므로 PK는 movie_id, distributor
CREATE TABLE movie_info.movie_distribution (
    movie_id       VARCHAR(20)  NOT NULL,
    movie_name     VARCHAR(300) NOT NULL,
    distributor    VARCHAR(300) NOT NULL,

    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by     VARCHAR(100),
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by     VARCHAR(100),

    CONSTRAINT pk_movie_distribution
        PRIMARY KEY (movie_id, distributor),

    CONSTRAINT fk_movie_distribution_movie
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_master (movie_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- MOIVE_PRODUCTION
CREATE TABLE movie_info.movie_production (
    movie_id             VARCHAR(20)  NOT NULL,
    movie_name           VARCHAR(300) NOT NULL,
    production_year      SMALLINT,
    production_status    VARCHAR(100),
    director              VARCHAR(300),
    production_company    VARCHAR(500),

    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(100),
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by            VARCHAR(100),

    CONSTRAINT pk_movie_production
        PRIMARY KEY (movie_id),

    CONSTRAINT fk_movie_production_movie
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_master (movie_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_movie_production_year
        CHECK (
            production_year IS NULL
            OR production_year BETWEEN 1800 AND 2100
        )
);

-- MOVIE_SALES
CREATE TABLE movie_info.movie_sales (
    movie_id                    VARCHAR(20) NOT NULL,
    movie_name                  VARCHAR(300) NOT NULL,

    sales_amount                BIGINT NOT NULL DEFAULT 0,
    sales_share                 NUMERIC(7, 4) NOT NULL DEFAULT 0,
    cumulative_sales_amount     BIGINT NOT NULL DEFAULT 0,

    audience_count              BIGINT NOT NULL DEFAULT 0,
    cumulative_audience_count   BIGINT NOT NULL DEFAULT 0,

    screen_count                INTEGER NOT NULL DEFAULT 0,
    screening_count             BIGINT NOT NULL DEFAULT 0,

    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                  VARCHAR(100),
    updated_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by                  VARCHAR(100),

    CONSTRAINT pk_movie_sales
        PRIMARY KEY (movie_id),

    CONSTRAINT fk_movie_sales_movie
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_master (movie_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_movie_sales_amount
        CHECK (sales_amount >= 0),

    CONSTRAINT chk_movie_sales_share
        CHECK (sales_share BETWEEN 0 AND 100),

    CONSTRAINT chk_movie_cumulative_sales
        CHECK (cumulative_sales_amount >= 0),

    CONSTRAINT chk_movie_audience
        CHECK (
            audience_count >= 0
            AND cumulative_audience_count >= 0
        ),

    CONSTRAINT chk_movie_screen
        CHECK (
            screen_count >= 0
            AND screening_count >= 0
        )
);

/* 불필요한 제약조건 및 삭제 */
ALTER TABLE movie_info.movie_sales
DROP CONSTRAINT fk_movie_sales_movie;

ALTER TABLE movie_info.movie_sales
DROP CONSTRAINT chk_movie_audience;

ALTER TABLE movie_info.movie_sales
DROP CONSTRAINT chk_movie_cumulative_sales;

ALTER TABLE movie_info.movie_sales
DROP CONSTRAINT chk_movie_sales_amount;

/* movie_name이 200자가 넘어가는 영화가 있으므로 alter  column */
ALTER TABLE movie_info.movie_code
    ALTER COLUMN movie_name TYPE TEXT;
ALTER TABLE movie_info.movie_master
    ALTER COLUMN movie_name TYPE TEXT;
ALTER TABLE movie_info.movie_distribution
    ALTER COLUMN movie_name TYPE TEXT; 
ALTER TABLE movie_info.movie_production
    ALTER COLUMN movie_name TYPE TEXT;
ALTER TABLE movie_info.movie_sales
    ALTER COLUMN movie_name TYPE TEXT;

