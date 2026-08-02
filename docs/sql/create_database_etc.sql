-- ============================================================
-- 1. 데이터베이스 생성
-- ============================================================

-- [주의] postgres database에서 실행할 것!!!
-- postgres 데이터베이스의 Query Tool에서 이 구문만 실행
-- [수정] 이미 movie_database가 존재하면 아래 CREATE DATABASE는 실행 x

CREATE DATABASE movie_database
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    TEMPLATE = template0;

/*
[중요]
위 CREATE DATABASE 실행 후 현재 Query Tool을 닫고,
movie_database를 선택하여 새로운 Query Tool을 연 뒤
아래 CREATE SCHEMA부터 실행할 것
*/

-- ============================================================
-- 2. 스키마 생성
-- ============================================================

-- [주의] 1번에서 생성한 movie_database에 다시 접속한 뒤
-- 아래 CREATE SCHEMA부터 실행할 것!!!
-- [수정] 기존 주석의 'movie_info 데이터베이스' -> 'movie_database'로 정정

CREATE SCHEMA movie_info;

-- ============================================================
-- MOVIE_CODE
-- ============================================================

-- [수정]
-- pdf 문구가 컬럼 정의에 섞인 부분 제거
-- created_at, updated_at 컬럼의 TIMESTAMP 구문 복원
-- movie_name은 300자를 초과하는 데이터가 있어 TEXT로 정의

CREATE TABLE movie_info.movie_code (
    movie_id VARCHAR(20) NOT NULL,
    movie_name TEXT NOT NULL,
    release_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movie_code
        PRIMARY KEY (movie_id)
);


-- ============================================================
-- MOVIE_MASTER
-- ============================================================

-- [수정]
-- created_at, updated_at 컬럼의 깨진 TIMESTAMP 구문 복원
-- movie_name은 ALTER TABLE 없이 처음부터 TEXT로 정의

CREATE TABLE movie_info.movie_master (
    movie_id VARCHAR(20) NOT NULL,
    movie_name TEXT NOT NULL,
    movie_name_en VARCHAR(300),
    release_date DATE,
    production_year SMALLINT,
    movie_type VARCHAR(50),
    genre_production_status VARCHAR(100),
    main_nation VARCHAR(100),
    nations VARCHAR(300),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),

    CONSTRAINT pk_movie_master
        PRIMARY KEY (movie_id),

    CONSTRAINT fk_movie_master_movie_code
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_code(movie_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_movie_master_production_year
        CHECK (
            production_year IS NULL
            OR production_year BETWEEN 1800 AND 2100
        )
);


-- ============================================================
-- MOVIE_DISTRIBUTION
-- ============================================================

-- 1:N이므로 PK는 movie_id, distributor
-- [수정]
-- created_at, updated_at 컬럼의 깨진 TIMESTAMP 구문 복원
-- movie_name은 ALTER TABLE 없이 처음부터 TEXT로 정의

CREATE TABLE movie_info.movie_distribution (
    movie_id VARCHAR(20) NOT NULL,
    movie_name TEXT NOT NULL,
    distributor VARCHAR(300) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),

    CONSTRAINT pk_movie_distribution
        PRIMARY KEY (
            movie_id,
            distributor
        ),

    CONSTRAINT fk_movie_distribution_movie
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_master(movie_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- MOVIE_PRODUCTION
-- ============================================================

-- [수정]
-- 기존 'MOIVE_PRODUCTION' 오타를 'MOVIE_PRODUCTION'으로 정정
-- production_status 앞에 섞인 pdf 문구 제거
-- created_at, updated_at 컬럼의 깨진 TIMESTAMP 구문 복원

CREATE TABLE movie_info.movie_production (
    movie_id VARCHAR(20) NOT NULL,
    movie_name TEXT NOT NULL,
    production_year SMALLINT,
    production_status VARCHAR(100),
    director VARCHAR(300),
    production_company VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),

    CONSTRAINT pk_movie_production
        PRIMARY KEY (movie_id),

    CONSTRAINT fk_movie_production_movie
        FOREIGN KEY (movie_id)
        REFERENCES movie_info.movie_master(movie_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_movie_production_year
        CHECK (
            production_year IS NULL
            OR production_year BETWEEN 1800 AND 2100
        )
);


-- ============================================================
-- MOVIE_SALES
-- ============================================================

-- [수정 2026-07-30]
-- 불필요한 외래키 및 금액·관객수 관련 제약조건은 최종 CREATE TABLE 정의에서 제외했습니다.

-- [수정 2026-08-01]
-- movie_name은 ALTER TABLE 없이 처음부터 TEXT로 정의
-- month 컬럼을 CREATE TABLE에 직접 추가
-- 동일 영화가 월별로 저장되므로 기본키를 (movie_id, month) 복합 기본키로 정의

CREATE TABLE movie_info.movie_sales (
    movie_id VARCHAR(20) NOT NULL,
    movie_name TEXT NOT NULL,
    month VARCHAR(7) NOT NULL, -- '2026-07' 형태로 저장
    sales_amount BIGINT NOT NULL DEFAULT 0,
    sales_share NUMERIC(7, 4) NOT NULL DEFAULT 0,
    cumulative_sales_amount BIGINT NOT NULL DEFAULT 0,
    audience_count BIGINT NOT NULL DEFAULT 0,
    cumulative_audience_count BIGINT NOT NULL DEFAULT 0,
    screen_count INTEGER NOT NULL DEFAULT 0,
    screening_count BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),

    CONSTRAINT pk_movie_sales
        PRIMARY KEY (
            movie_id,
            month
        ),

    CONSTRAINT chk_movie_sales_share
        CHECK (
            sales_share BETWEEN 0 AND 100
        ),

    CONSTRAINT chk_movie_screen
        CHECK (
            screen_count >= 0
            AND screening_count >= 0
        )
);


/*
============================================================
기존 변경사항 정리
============================================================

[변경사항 2026-07-30]

불필요한 제약조건 및 삭제:
- fk_movie_sales_movie
- chk_movie_audience
- chk_movie_cumulative_sales
- chk_movie_sales_amount

위 제약조건은 최종 CREATE TABLE 정의에서 제외했으므로
별도의 DROP CONSTRAINT 구문을 실행하지 않습니다.


[변경사항 2026-08-01]

movie_name의 길이가 기존 VARCHAR 범위를 초과하는 데이터가 있으므로
다음 테이블의 movie_name 컬럼을 TEXT로 정의했습니다.

- movie_code
- movie_master
- movie_distribution
- movie_production
- movie_sales

또한 movie_sales에 month 컬럼을 추가하고
기존 movie_id 단일 기본키를
(movie_id, month) 복합 기본키로 변경했습니다.

최종 CREATE TABLE 정의에 이미 반영되어 있으므로
별도의 ALTER TABLE 구문을 실행하지 않습니다.
*/