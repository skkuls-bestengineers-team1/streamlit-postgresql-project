from __future__ import annotations

import os
import sys
from pathlib import Path

from typing import Any
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
'''
아래 load_database_config() 주석의 @description 참고하여
꼭 작성 부탁드립니다.

각 함수마다 try-exception 처리 부탁드립니다.


'''
BASE_DIR = Path(__file__).resolve().parent # 현재 위치
ENV_PATH = BASE_DIR / ".env"

'''
@name : loading database config
@author : choiminjoeng
@date : 2020-07-31
@description : 프로젝트의 .env 파일에서 PostgreSQL 접속 설정을 읽는다.
'''
def load_database_config() -> dict[str, str | int]:

    print("ENV_PATH :", ENV_PATH)
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
        missing_text= ','.join(missing_key)
      
        raise ValueError(
            f'.env 파일에 다음 설정이 없습니다 : {missing_text}'
        )

    return {
        'host' : os.environ['DB_HOST'],
        'port' : int(os.environ['DB_PORT']),
        'dbname' : os.environ['DB_NAME'],
        'user' : os.environ['DB_USER'],
        'password' : os.environ['DB_PASSWORD'],
        'connect_timeout' : 5
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
                # print(testData)

                return testData

    except psycopg.Error as error:
        print(f'[PostgreSQL SQL 오류]: {error}')
        sys.exit(1)

'''
Backend API 테스트 코드
'''
# def main():
#     df = getTestData()
#     print(df)
#
#
# if __name__ == "__main__":
#     main()