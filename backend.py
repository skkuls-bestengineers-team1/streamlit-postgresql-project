from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

'''
아래 load_database_config() 주석의 @description 참고하여
꼭 작성 부탁드립니다.

각 함수마다 try-exception 처리 부탁드립니다.
'''

BASE_DIR = Path(__file__).resolve().parent  # 현재 위치
ENV_PATH = BASE_DIR / '.env'

'''
@name : loading database config
@author : choiminjoeng
@date : 2020-07-31
@description : 프로젝트의 .env 파일에서 PostgreSQL 접속 설정을 읽는다.
'''
def load_database_config() -> dict[str, str | int]:

    print('ENV_PATH :', ENV_PATH)
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


def get_database_connection() -> psycopg.Connection | None:

    try:
        config = load_database_config()
        print('PostgreSQL 연결을 시작합니다.')

        return psycopg.connect(
            **config,
            row_factory=dict_row
        )
    except FileNotFoundError as error:
        print(f'설정 파일 오류 : {error}')
        sys.exit(1)


def get_test_data() -> dict[str, Any] | None:
    config = load_database_config()
    print('PostgreSQL 연결을 시작합니다.')

    try:
        with psycopg.connect(
                **config,
                row_factory=dict_row
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select current_time
                    """
                )

                return cursor.fetchone()

    except psycopg.Error as error:
        print(f'[PostgreSQL SQL 오류]: {error}')
        sys.exit(1)


'''
Backend API 테스트 코드
'''
def main():
    df = get_test_data()
    print(df)


if __name__ == '__main__':
    main()



# Frontend용 데이터 API
#  지금은 CSV로 동작 (임시)
#  송주님이 SQL 조회로 교체해주세요!
# frontend.py는 아래 함수명/반환 컬럼만 맞으면 그대로 동작합니다!!

DATA_DIR = BASE_DIR / 'docs'
MONTHLY_CSV = DATA_DIR / 'monthly_boxoffice.csv'
MOVIE_LIST_CSV = DATA_DIR / 'movie_list.csv'


def _normalize_movie_name(value: Any) -> str:
    return re.sub(r'\s+', '', str(value)).strip()


def _to_nation_group(nation: Any) -> str:
    text = str(nation).strip()
    if text == '한국':
        return '한국'
    if text == '미국':
        return '미국'
    return '기타'


def _load_monthly() -> pd.DataFrame:
    df = pd.read_csv(MONTHLY_CSV, encoding='utf-8-sig')
    df['영화명_key'] = df['영화명'].map(_normalize_movie_name)
    return df


def _load_movie_list() -> pd.DataFrame:
    df = pd.read_csv(MOVIE_LIST_CSV, encoding='utf-8-sig')
    df['영화명_key'] = df['영화명'].map(_normalize_movie_name)
    return df[['영화명_key', '장르']].drop_duplicates(subset=['영화명_key'])


def _load_joined() -> pd.DataFrame:
    monthly = _load_monthly()
    movies = _load_movie_list()
    joined = monthly.merge(movies, on='영화명_key', how='left')
    joined['장르'] = joined['장르'].fillna('미분류')
    joined['국가그룹'] = joined['대표국적'].map(_to_nation_group)
    return joined


def _filter_frame(
    df: pd.DataFrame,
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if months:
        filtered = filtered[filtered['월'].isin(months)]


    if genres:
        pattern = '|'.join(map(re.escape, genres))
        filtered = filtered[
            filtered['장르'].astype(str).str.contains(pattern, na=False)
        ]

    return filtered


def get_month_list() -> list[str]:

    df = _load_monthly()
    return sorted(df['월'].dropna().astype(str).unique().tolist())


def get_genre_list() -> list[str]:
    # 복수 장르는 분리했습니다! 예) 장르가 액션 / 스릴러면 하나만 선택해도 표시되게!
    df = _load_movie_list()
    genres: set[str] = set()
    for value in df['장르'].dropna().astype(str):
        for genre in value.split(','):
            genre = genre.strip()
            if genre:
                genres.add(genre)
    return sorted(genres)

#tap1_1
def get_monthly_audience(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:

    df = _filter_frame(_load_joined(), months, genres)
    if df.empty:
        return pd.DataFrame(columns=['월', '관객수'])
    result = (
        df.groupby('월', as_index=False)['관객수']
        .sum()
        .sort_values('월')
    )
    return result

#tap 1_2
def get_scatter_data(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:

    df = _filter_frame(_load_joined(), months, genres)
    columns = ['월', '영화명', '스크린수', '관객수', '매출액', '대표국적', '장르']
    if df.empty:
        return pd.DataFrame(columns=columns)
    return df[columns].copy()

#tap2
def get_nation_audience(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:

    df = _filter_frame(_load_joined(), months, genres)
    if df.empty:
        return pd.DataFrame(columns=['국가그룹', '관객수'])
    result = df.groupby('국가그룹', as_index=False)['관객수'].sum()
    order = pd.Categorical(
        result['국가그룹'],
        categories=['한국', '미국', '기타'],
        ordered=True,
    )
    result['국가그룹'] = order
    return result.sort_values('국가그룹')

#tap3
def get_nation_sales(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:

    df = _filter_frame(_load_joined(), months, genres)
    if df.empty:
        return pd.DataFrame(columns=['국가그룹', '매출액'])
    result = df.groupby('국가그룹', as_index=False)['매출액'].sum()
    order = pd.Categorical(
        result['국가그룹'],
        categories=['한국', '미국', '기타'],
        ordered=True,
    )
    result['국가그룹'] = order
    return result.sort_values('국가그룹')

#tap3_2
def get_genre_sales(
    months: list[str] | None = None,
    genres: list[str] | None = None,
) -> pd.DataFrame:

    df = _filter_frame(_load_joined(), months, genres)
    if df.empty:
        return pd.DataFrame(columns=['장르', '매출액'])

    exploded = df.assign(장르=df['장르'].astype(str).str.split(',')).explode('장르')
    exploded['장르'] = exploded['장르'].astype(str).str.strip()
    exploded = exploded[exploded['장르'].ne('') & exploded['장르'].ne('미분류')]

    if genres:
        exploded = exploded[exploded['장르'].isin(genres)]

    result = (
        exploded.groupby('장르', as_index=False)['매출액']
        .sum()
        .sort_values('매출액', ascending=False)
    )
    return result
