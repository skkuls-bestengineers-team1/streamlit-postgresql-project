-- 1. 데이터베이스 생성
-- [주의] postgres database에서 실행할 것!!!
CREATE DATABASE movie_database
	WITH OWNER = 'postgres' ENCODING = 'UTF8' TEMPLATE = template0;

-- 2. 스키마 생성
-- [주의] 1번에서 생성한 movie_info 데이터베이스에서 생성할 것!!!
CREATE SCHEMA movie_info;

-- MOVIE_CODE
CREATE TABLE movie_info.movie_code (
	movie_id VARCHAR(20) NOT NULL
	,movie_name VARCHAR(300) NOT NULL
	,영화 데이터베이스 정리 2 release_date DATE
	,created_at TAMP
	,updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMES TIMESTAMP NOT NULL DEFAULT CURRENT_TIMES TAMP
	,CONSTRAINT pk_movie_code PRIMARY KEY (movie_id)
	);

-- MOVIE_MASTER
CREATE TABLE movie_info.movie_master (
	movie_id VARCHAR(20) NOT NULL
	,movie_name VARCHAR(300) NOT NULL
	,movie_name_en VARCHAR(300)
	,release_date DATE
	,production_year SMALLINT
	,movie_type VARCHAR(50)
	,genre_production_status VARCHAR(100)
	,main_nation VARCHAR(100)
	,nations VARCHAR(300)
	,created_at URRENT_TIMESTAMP
	,created_by VARCHAR(100)
	,updated_at URRENT_TIMESTAMP
	,updated_by VARCHAR(100)
	,TIMESTAMP NOT NULL DEFAULT C TIMESTAMP NOT NULL DEFAULT C CONSTRAINT pk_movie_master PRIMARY KEY (movie_id)
	,CONSTRAINT fk_movie_master_movie_code FOREIGN KEY (movie_id) REFERENCES movie_info.movie_code(movie_id) ON UPDATE CASCADE 영화 데이터베이스 정리 3 ON DELETE RESTRICT
	,CONSTRAINT chk_movie_master_production_year CHECK (
		production_year IS NULL
		OR production_year BETWEEN 1800
			AND 2100
		)
	);

-- MOVIE_DISTRIBUTION
-- 1:N이므로 PK는 movie_id, distributor
CREATE TABLE movie_info.movie_distribution (
	movie_id VARCHAR(20) NOT NULL
	,movie_name VARCHAR(300) NOT NULL
	,distributor VARCHAR(300) NOT NULL
	,created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMES TAMP
	,created_by VARCHAR(100)
	,updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMES TAMP
	,updated_by VARCHAR(100)
	,CONSTRAINT pk_movie_distribution PRIMARY KEY (
		movie_id
		,distributor
		)
	,CONSTRAINT fk_movie_distribution_movie FOREIGN KEY (movie_id) REFERENCES movie_info.movie_master(movie_id) ON UPDATE CASCADE ON DELETE CASCADE
	);

-- MOIVE_PRODUCTION
CREATE TABLE movie_info.movie_production (
	movie_id VARCHAR(20) NOT NULL
	,movie_name VARCHAR(300) NOT NULL
	,production_year SMALLINT
	,영화 데이터베이스 정리 4 production_status VARCHAR(100)
	,director VARCHAR(300)
	,production_company VARCHAR(500)
	,created_at TIMESTAMP NOT NULL DEFAULT CURREN T_TIMESTAMP
	,created_by VARCHAR(100)
	,updated_at TIMESTAMP NOT NULL DEFAULT CURREN T_TIMESTAMP
	,updated_by VARCHAR(100)
	,CONSTRAINT pk_movie_production PRIMARY KEY (movie_id)
	,CONSTRAINT fk_movie_production_movie FOREIGN KEY (movie_id) REFERENCES movie_info.movie_master(movie_id) ON UPDATE CASCADE ON DELETE CASCADE
	,CONSTRAINT chk_movie_production_year CHECK (
		production_year IS NULL
		OR production_year BETWEEN 1800
			AND 2100
		)
	);

-- MOVIE_SALES
CREATE TABLE movie_info.movie_sales (
	movie_id VARCHAR(20) NOT NULL
	,movie_name VARCHAR(300) NOT NULL
	,sales_amount sales_share BIGINT NOT NULL DEFAULT 0
	,NUMERIC(7, 4) NOT NULL DEFA ULT 0
	,cumulative_sales_amount BIGINT NOT NULL DEFAULT 0
	,audience_count BIGINT NOT NULL DEFAULT 0
	,영화 데이터베이스 정리 5 cumulative_audience_count BIGINT NOT NULL DEFAULT 0
	,screen_count screening_count INTEGER NOT NULL DEFAULT 0
	,BIGINT NOT NULL DEFAULT 0
	,created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	,created_by VARCHAR(100)
	,updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	,updated_by VARCHAR(100)
	,CONSTRAINT pk_movie_sales PRIMARY KEY (
		movie_id
		,month
		)
	,< --- month 추가 필요
	CONSTRAINT fk_movie_sales_movie FOREIGN KEY (movie_id) REFERENCES movie_info.movie_master(movie_id) ON UPDATE CASCADE ON DELETE CASCADE
	,CONSTRAINT chk_movie_sales_amount CHECK (sales_amount >= 0)
	,CONSTRAINT chk_movie_sales_share CHECK (
		sales_share BETWEEN 0
			AND 100
		)
	,CONSTRAINT chk_movie_cumulative_sales CHECK (cumulative_sales_amount >= 0)
	,CONSTRAINT chk_movie_audience CHECK (
		audience_count >= 0
		AND cumulative_audience_count >= 0
		)
	,CONSTRAINT chk_movie_screen CHECK (
		영화 데이터베이스 정리 6 screen_count >= 0
		AND screening_count >= 0
		)
	);[변경사항 2026-07-30]

/* 불필요한 제약조건 및 삭제 */
ALTER TABLE movie_info.movie_sales

DROP CONSTRAINT fk_movie_sales_movie;

ALTER TABLE movie_info.movie_sales

DROP CONSTRAINT chk_movie_audience;

ALTER TABLE movie_info.movie_sales

DROP CONSTRAINT chk_movie_cumulative_sales;

ALTER TABLE movie_info.movie_sales

DROP CONSTRAINT chk_movie_sales_amount;

/* movie_name이 200자가 넘어가는 영화가 있으므로 alter column
*/
ALTER TABLE movie_info.movie_code

ALTER COLUMN movie_name TYPE TEXT;

ALTER TABLE movie_info.movie_master

ALTER COLUMN movie_name TYPE TEXT;

ALTER TABLE movie_info.movie_distribution

ALTER COLUMN movie_name TYPE TEXT;

ALTER TABLE movie_info.movie_production

ALTER COLUMN movie_name TYPE TEXT;

ALTER TABLE movie_info.movie_sales

ALTER COLUMN movie_name TYPE TEXT;[변경사항 2026-08-01]

-- 1) month 컬럼 추가
ALTER TABLE movie_info.movie_sales ADD COLUMN month VARCHAR(7);-- '2026-07' 형태로 저장

영화 데이터베이스 정리 7

-- 2) 기존 PK(movie_id) 제약 삭제
ALTER TABLE movie_info.movie_sales

DROP CONSTRAINT pk_movie_sales;

-- 3) 새 복합 PK로 재설정 (movie_id, month)
ALTER TABLE movie_info.movie_sales ADD CONSTRAINT pk_movie_sales PRIMARY KEY (
	movie_id
	,month
	);