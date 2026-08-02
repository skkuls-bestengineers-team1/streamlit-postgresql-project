from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

'''
아래 load_database_config() 주석의 @description 참고하여
꼭 작성 부탁드립니다.

각 함수마다 try-exception 처리 부탁드립니다.
'''

BASE_DIR = Path(__file__).resolve().parent #현재 위치
ENV_PATH = BASE_DIR / '.env'

ANALYSIS_START_MONTH = '2026-01'
ANALYSIS_END_MONTH = '2026-06'

'''
@name : loading database config
@author : choiminjoeng
@date : 2020-07-31
@description : 프로젝트의 .env 파일에서 PostgreSQL 접속 설정을 읽는다.
'''
def load_database_config() -> dict[str, str | int]:


    if not ENV_PATH.exists():
        raise FileNotFoundError(
            '.env 파일이 없습니다.'
        )

    load_dotenv(ENV_PATH)

    required_keys = [
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]

    missing_key = [
        key for key in required_keys if not os.getenv(key)
    ]

    if missing_key:
        missing_text = ','.join(missing_key)

        raise ValueError(
            f'.env 파일에 다음 설정이 없습니다 : {missing_text}'
        )

    return {
        'host': os.environ['DB_HOST'],
        'port': int(os.environ['DB_PORT']),
        'dbname': os.environ['DB_NAME'],
        'user': os.environ['DB_USER'],
        'password': os.environ['DB_PASSWORD'],
        'connect_timeout': 5
    }


def get_database_connection() -> psycopg.Connection:
    """
    PostgreSQL 연결 객체를 생성하여 반환합니다.
    """

    try:
        config = load_database_config()

        return psycopg.connect(
            **config,
            row_factory=dict_row,
        )

    except (FileNotFoundError, ValueError) as error:
        raise RuntimeError(
            f'데이터베이스 설정 오류: {error}'
        ) from error

    except psycopg.Error as error:
        raise RuntimeError(
            f'PostgreSQL 연결 오류: {error}'
        ) from error

def execute_select(
    query: str,
    params: Sequence[Any] | None = None,
) -> pd.DataFrame:
    """
    SELECT 쿼리를 실행하고 결과를 DataFrame으로 반환합니다.
    """

    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)

                rows = cursor.fetchall()

                columns = (
                    [column.name for column in cursor.description]
                    if cursor.description
                    else []
                )

        return pd.DataFrame(rows, columns=columns)

    except psycopg.Error as error:
        raise RuntimeError(
            f'[PostgreSQL 조회 오류]: {error}'
        ) from error

    except Exception as error:
        raise RuntimeError(
            f'[조회 결과 처리 오류]: {error}'
        ) from error        




# Frontend용 데이터 API
#  지금은 CSV로 동작 (임시)
#  송주님이 SQL 조회로 교체해주세요!
# frontend.py는 아래 함수명/반환 컬럼만 맞으면 그대로 동작합니다!!





def get_month_list() -> list[str]:
    """
    분석 기간에 포함되는 월 목록을 반환합니다.
    """

    try:
        query = """
            SELECT DISTINCT
                BTRIM(month) AS "월"
            FROM movie_info.movie_sales
            WHERE month IS NOT NULL
              AND BTRIM(month) <> ''
              AND BTRIM(month) BETWEEN %s AND %s
            ORDER BY "월";
        """

        result = execute_select(
            query,
            [
                ANALYSIS_START_MONTH,
                ANALYSIS_END_MONTH,
            ],
        )

        if result.empty or '월' not in result.columns:
            return []

        months = (
            result['월']
            .dropna()
            .astype(str)
            .str.strip()
        )

        return months[months.ne('')].tolist()

    except Exception as error:
        raise RuntimeError(
            f'월 목록 조회 오류: {error}'
        ) from error

def get_genre_list() -> list[str]:
    """
    분석 기간에 존재하는 영화의 장르 목록을 반환합니다.
    """

    try:
        query = r"""
            SELECT DISTINCT
                BTRIM(genre_table.genre_name) AS "장르"

            FROM movie_info.movie_master AS m

            INNER JOIN movie_info.movie_sales AS s
                ON m.movie_id = s.movie_id

            CROSS JOIN LATERAL regexp_split_to_table(
                regexp_replace(
                    COALESCE(
                        m.genre_production_status,
                        ''
                    ),
                    '\s*/\s*[^/]+$',
                    ''
                ),
                ','
            ) AS genre_table(genre_name)

            WHERE s.month BETWEEN %s AND %s
              AND BTRIM(genre_table.genre_name) <> ''

            ORDER BY "장르";
        """

        result = execute_select(
            query,
            [
                ANALYSIS_START_MONTH,
                ANALYSIS_END_MONTH,
            ],
        )

        if result.empty or '장르' not in result.columns:
            return []

        genres = (
            result['장르']
            .dropna()
            .astype(str)
            .str.strip()
        )

        return genres[genres.ne('')].tolist()

    except Exception as error:
        raise RuntimeError(
            f'장르 목록 조회 오류: {error}'
        ) from error
    
def _clean_filter_values(
    values: list[str] | None,
) -> list[str] | None:
    """
    필터 목록에서 None, 빈 문자열, 공백 문자열을 제거합니다.
    유효한 값이 없으면 None을 반환합니다.
    """

    try:
        if not values:
            return None

        cleaned_values = sorted({
            str(value).strip()
            for value in values
            if value is not None and str(value).strip()
        })

        return cleaned_values or None

    except Exception as error:
        raise ValueError(
            f'필터값 검증 오류: {error}'
        ) from error


def _build_common_filters(
    months: list[str] | None,
    genres: list[str] | None,
) -> tuple[str, list[Any]]:
    """
    movie_sales 별칭 s와 movie_master 별칭 m에 적용할
    월·장르 필터 SQL을 생성합니다.
    """

    try:
        cleaned_months = _clean_filter_values(months)
        cleaned_genres = _clean_filter_values(genres)

        conditions = ['s.month BETWEEN %s AND %s']
        params: list[Any] = [
            ANALYSIS_START_MONTH,
            ANALYSIS_END_MONTH,
            ]

        if cleaned_months:
            conditions.append('s.month = ANY(%s)')
            params.append(cleaned_months)

        if cleaned_genres:
            conditions.append(
                r"""
                EXISTS (
                    SELECT 1
                    FROM regexp_split_to_table(
                        regexp_replace(
                            COALESCE(
                                m.genre_production_status,
                                ''
                            ),
                            '\s*/\s*[^/]+$',
                            ''
                        ),
                        ','
                    ) AS selected_genre(genre_name)
                    WHERE BTRIM(
                        selected_genre.genre_name
                    ) = ANY(%s)
                )
                """
            )
            params.append(cleaned_genres)

        where_sql = ' AND '.join(conditions)

        return where_sql, params

    except (ValueError, TypeError):
        raise

    except Exception as error:
        raise RuntimeError(
            f'SQL 필터 생성 오류: {error}'
        ) from error

#tap1_1
def get_monthly_audience(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    """
    선택한 월과 장르 조건에 따른 월별 관객수 합계를 반환합니다.

    반환 컬럼:
    - 월
    - 관객수
    """

    try:
        where_sql, params = _build_common_filters(
            months,
            genres,
        )

        query = f"""
            SELECT
                s.month AS "월",
                SUM(s.audience_count)::BIGINT AS "관객수"
            FROM movie_info.movie_sales AS s
            INNER JOIN movie_info.movie_master AS m
                ON s.movie_id = m.movie_id
            WHERE {where_sql}
              AND s.month IS NOT NULL
              AND BTRIM(s.month) <> ''
            GROUP BY s.month
            ORDER BY s.month;
        """

        result = execute_select(query, params)

        if result.empty:
            return pd.DataFrame(
                columns=['월', '관객수']
            )

        return result[['월', '관객수']]

    except Exception as error:
        raise RuntimeError(
            f'월별 관객수 조회 오류: {error}'
        ) from error

#tap 1_2
def get_scatter_data(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    """
    선택한 월과 장르 조건에 따른 산점도 데이터를 반환합니다.

    반환 컬럼:
    - 월
    - 영화명
    - 스크린수
    - 관객수
    - 매출액
    - 대표국적
    - 장르
    """

    columns = [
        '월',
        '영화명',
        '스크린수',
        '관객수',
        '매출액',
        '대표국적',
        '장르',
    ]

    try:
        where_sql, params = _build_common_filters(
            months,
            genres,
        )

        query = f"""
            SELECT
                s.month AS "월",

                COALESCE(
                    NULLIF(BTRIM(m.movie_name), ''),
                    '제목 없음'
                ) AS "영화명",

                COALESCE(
                    s.screen_count,
                    0
                )::BIGINT AS "스크린수",

                COALESCE(
                    s.audience_count,
                    0
                )::BIGINT AS "관객수",

                COALESCE(
                    s.sales_amount,
                    0
                )::BIGINT AS "매출액",

                COALESCE(
                    NULLIF(BTRIM(m.main_nation), ''),
                    '미상'
                ) AS "대표국적",

                COALESCE(
                    NULLIF(
                        BTRIM(
                            regexp_replace(
                                m.genre_production_status,
                                '\\s*/\\s*[^/]+$',
                                ''
                            )
                        ),
                        ''
                    ),
                    '미분류'
                ) AS "장르"

            FROM movie_info.movie_sales AS s

            INNER JOIN movie_info.movie_master AS m
                ON s.movie_id = m.movie_id

            WHERE {where_sql}
              AND s.month IS NOT NULL
              AND BTRIM(s.month) <> ''

            ORDER BY
                s.month,
                s.audience_count DESC,
                m.movie_name;
        """

        result = execute_select(query, params)

        if result.empty:
            return pd.DataFrame(columns=columns)

        return result[columns]

    except Exception as error:
        raise RuntimeError(
            f'산점도 데이터 조회 오류: {error}'
        ) from error

#tap2
def get_nation_audience(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    """
    선택한 월과 장르 조건에 따른 국가별 관객수를 반환합니다.

    국가는 한국, 미국, 기타로 구분합니다.

    반환 컬럼:
    - 국가그룹
    - 관객수
    """

    columns = [
        '국가그룹',
        '관객수',
    ]

    try:
        where_sql, params = _build_common_filters(
            months,
            genres,
        )

        query = f"""
            WITH nation_data AS (
                SELECT
                    CASE
                        WHEN BTRIM(m.main_nation) = '한국'
                            THEN '한국'
                        WHEN BTRIM(m.main_nation) = '미국'
                            THEN '미국'
                        ELSE '기타'
                    END AS "국가그룹",

                    SUM(
                        s.audience_count
                    )::BIGINT AS "관객수"

                FROM movie_info.movie_sales AS s

                INNER JOIN movie_info.movie_master AS m
                    ON s.movie_id = m.movie_id

                WHERE {where_sql}

                GROUP BY
                    CASE
                        WHEN BTRIM(m.main_nation) = '한국'
                            THEN '한국'
                        WHEN BTRIM(m.main_nation) = '미국'
                            THEN '미국'
                        ELSE '기타'
                    END
            )

            SELECT
                "국가그룹",
                "관객수"
            FROM nation_data

            ORDER BY
                CASE "국가그룹"
                    WHEN '한국' THEN 1
                    WHEN '미국' THEN 2
                    ELSE 3
                END;
        """

        result = execute_select(query, params)

        if result.empty:
            return pd.DataFrame(columns=columns)

        return result[columns]

    except Exception as error:
        raise RuntimeError(
            f'국가별 관객수 조회 오류: {error}'
        ) from error

#tap3
def get_nation_sales(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    """
    선택한 월과 장르 조건에 따른 국가별 매출액을 반환합니다.

    국가는 한국, 미국, 기타로 구분합니다.

    반환 컬럼:
    - 국가그룹
    - 매출액
    """

    columns = [
        '국가그룹',
        '매출액',
    ]

    try:
        where_sql, params = _build_common_filters(
            months,
            genres,
        )

        query = f"""
            WITH nation_data AS (
                SELECT
                    CASE
                        WHEN BTRIM(m.main_nation) = '한국'
                            THEN '한국'
                        WHEN BTRIM(m.main_nation) = '미국'
                            THEN '미국'
                        ELSE '기타'
                    END AS "국가그룹",

                    SUM(
                        s.sales_amount
                    )::BIGINT AS "매출액"

                FROM movie_info.movie_sales AS s

                INNER JOIN movie_info.movie_master AS m
                    ON s.movie_id = m.movie_id

                WHERE {where_sql}

                GROUP BY
                    CASE
                        WHEN BTRIM(m.main_nation) = '한국'
                            THEN '한국'
                        WHEN BTRIM(m.main_nation) = '미국'
                            THEN '미국'
                        ELSE '기타'
                    END
            )

            SELECT
                "국가그룹",
                "매출액"
            FROM nation_data

            ORDER BY
                CASE "국가그룹"
                    WHEN '한국' THEN 1
                    WHEN '미국' THEN 2
                    ELSE 3
                END;
        """

        result = execute_select(query, params)

        if result.empty:
            return pd.DataFrame(columns=columns)

        return result[columns]

    except Exception as error:
        raise RuntimeError(
            f'국가별 매출액 조회 오류: {error}'
        ) from error

#tap3_2
def get_genre_sales(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    """
    선택한 월과 장르 조건에 따른 장르별 매출액을 반환합니다.

    복수 장르는 쉼표를 기준으로 각각 분리합니다.

    반환 컬럼:
    - 장르
    - 매출액
    """

    columns = [
        '장르',
        '매출액',
    ]

    try:
        cleaned_months = _clean_filter_values(months)
        cleaned_genres = _clean_filter_values(genres)

        conditions = [
            's.month BETWEEN %s AND %s',
            "BTRIM(genre_table.genre_name) <> ''",
            ]
        
        params: list[Any] = [
            ANALYSIS_START_MONTH,
            ANALYSIS_END_MONTH,
            ]

        if cleaned_months:
            conditions.append(
                's.month = ANY(%s)'
            )
            params.append(cleaned_months)

        if cleaned_genres:
            conditions.append(
                'BTRIM(genre_table.genre_name) = ANY(%s)'
            )
            params.append(cleaned_genres)

        where_sql = ' AND '.join(conditions)

        query = rf"""
            SELECT
                BTRIM(
                    genre_table.genre_name
                ) AS "장르",

                SUM(
                    s.sales_amount
                )::BIGINT AS "매출액"

            FROM movie_info.movie_sales AS s

            INNER JOIN movie_info.movie_master AS m
                ON s.movie_id = m.movie_id

            CROSS JOIN LATERAL regexp_split_to_table(
                regexp_replace(
                    COALESCE(
                        m.genre_production_status,
                        ''
                    ),
                    '\s*/\s*[^/]+$',
                    ''
                ),
                ','
            ) AS genre_table(genre_name)

            WHERE {where_sql}

            GROUP BY
                BTRIM(genre_table.genre_name)

            ORDER BY
                "매출액" DESC,
                "장르";
        """

        result = execute_select(
            query,
            params,
        )

        if result.empty:
            return pd.DataFrame(
                columns=columns
            )

        return result[columns]

    except Exception as error:
        raise RuntimeError(
            f'장르별 매출액 조회 오류: {error}'
        ) from error