import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv


# 현재 파이썬 파일이 있는 폴더
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

# 현재 파이썬 파일과 같은 위치에 있는 .env 파일 경로
ENV_PATH = BASE_DIR / ".env"

# .env 파일의 환경변수를 불러옴
load_dotenv(dotenv_path=ENV_PATH)


# .env 파일에서 KOBIS_API_KEY 값을 가져옴
API_KEY = os.getenv("KOBIS_API_KEY")

API_URL = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

START_DATE = "20260101"

# 2026080은 날짜 형식이 아니므로 20260801로 설정
END_DATE = "20260730"

# CSV 파일도 현재 파이썬 파일과 같은 폴더에 저장
OUTPUT_FILE = BASE_DIR / "kobis_movies_20260101_20260801.csv"


def validate_settings() -> None:
    """
    API 키와 날짜 설정이 올바른지 검사한다.
    """

    if not ENV_PATH.exists():
        raise FileNotFoundError(
            f".env 파일을 찾을 수 없습니다.\n"
            f"확인할 경로: {ENV_PATH}"
        )

    if not API_KEY:
        raise ValueError(
            ".env 파일에 KOBIS_API_KEY가 설정되어 있지 않습니다.\n"
            "예시: KOBIS_API_KEY=본인의_API_KEY"
        )

    try:
        start_date = datetime.strptime(START_DATE, "%Y%m%d")
        end_date = datetime.strptime(END_DATE, "%Y%m%d")

    except ValueError as error:
        raise ValueError(
            "날짜는 YYYYMMDD 형식으로 입력해야 합니다."
        ) from error

    if start_date > end_date:
        raise ValueError(
            "시작일은 종료일보다 늦을 수 없습니다."
        )


def get_daily_boxoffice(target_date: str) -> list[dict]:
    """
    특정 날짜의 일별 박스오피스 정보를 KOBIS API에서 조회한다.

    Parameters
    ----------
    target_date
        조회 날짜. YYYYMMDD 형식.

    Returns
    -------
    list[dict]
        해당 날짜의 일별 박스오피스 영화 목록.
    """

    params = {
        "key": API_KEY,
        "targetDt": target_date,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=15,
    )

    # 400, 404, 500 등의 HTTP 오류가 발생하면 예외 발생
    response.raise_for_status()

    data = response.json()

    # KOBIS API가 오류 내용을 JSON 형태로 반환하는 경우
    if "faultInfo" in data:
        fault_info = data["faultInfo"]

        error_message = fault_info.get(
            "message",
            "KOBIS API 오류가 발생했습니다.",
        )

        raise RuntimeError(error_message)

    boxoffice_result = data.get("boxOfficeResult")

    if boxoffice_result is None:
        raise KeyError(
            "응답 데이터에 boxOfficeResult가 없습니다."
        )

    return boxoffice_result.get(
        "dailyBoxOfficeList",
        [],
    )


def collect_movies(
    start_date_text: str,
    end_date_text: str,
) -> list[dict]:
    """
    시작일부터 종료일까지 일별 박스오피스를 조회한다.

    같은 영화는 여러 날짜의 박스오피스에 포함될 수 있으므로
    movieCd를 기준으로 중복을 제거한다.
    """

    start_date = datetime.strptime(
        start_date_text,
        "%Y%m%d",
    )

    end_date = datetime.strptime(
        end_date_text,
        "%Y%m%d",
    )

    # 미래 날짜를 조회하지 않도록 어제 날짜를 계산
    yesterday = datetime.now() - timedelta(days=1)

    if end_date > yesterday:
        actual_end_date = yesterday

        print(
            f"입력한 종료일 {end_date_text}은 아직 조회할 수 없는 날짜입니다."
        )
        print(
            "조회 가능한 최근 날짜인 "
            f"{actual_end_date.strftime('%Y%m%d')}까지만 조회합니다."
        )
        print()

    else:
        actual_end_date = end_date

    # key: 영화코드, value: 영화 정보
    movies_by_code: dict[str, dict] = {}

    current_date = start_date
    total_request_count = 0

    while current_date <= actual_end_date:
        target_date = current_date.strftime("%Y%m%d")

        try:
            daily_movies = get_daily_boxoffice(target_date)

            total_request_count += 1

            print(
                f"[{target_date}] "
                f"{len(daily_movies)}건 조회"
            )

            for movie in daily_movies:
                movie_code = movie.get("movieCd")
                movie_name = movie.get("movieNm")

                if not movie_code or not movie_name:
                    continue

                # 같은 영화코드가 아직 저장되지 않은 경우만 추가
                if movie_code not in movies_by_code:
                    movies_by_code[movie_code] = {
                        "movieCd": movie_code,
                        "movieNm": movie_name,
                        "openDt": movie.get("openDt", ""),
                        "firstCollectedDt": target_date,
                    }

        except requests.Timeout:
            print(
                f"[{target_date}] "
                "요청 시간이 초과되었습니다."
            )

        except requests.HTTPError as error:
            print(
                f"[{target_date}] "
                f"HTTP 오류가 발생했습니다: {error}"
            )

        except requests.RequestException as error:
            print(
                f"[{target_date}] "
                f"API 요청 중 오류가 발생했습니다: {error}"
            )

        except (KeyError, ValueError, RuntimeError) as error:
            print(
                f"[{target_date}] "
                f"데이터 처리 중 오류가 발생했습니다: {error}"
            )

        # API 서버에 요청이 너무 빠르게 반복되지 않도록 잠시 대기
        time.sleep(0.2)

        # 다음 날짜로 이동
        current_date += timedelta(days=1)

    print()
    print(f"총 API 요청 횟수: {total_request_count}")

    return list(movies_by_code.values())


def save_to_csv(
    movies: list[dict],
    output_file: Path,
) -> None:
    """
    영화 목록을 CSV 파일로 저장한다.
    """

    fieldnames = [
        "movieCd",
        "movieNm",
        "openDt",
        "firstCollectedDt",
    ]

    with output_file.open(
        mode="w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(movies)


def main() -> None:
    """
    프로그램 실행 시작점.
    """

    try:
        validate_settings()

        print("KOBIS 영화 데이터 수집을 시작합니다.")
        print(f"시작일: {START_DATE}")
        print(f"종료일: {END_DATE}")
        print()

        movies = collect_movies(
            start_date_text=START_DATE,
            end_date_text=END_DATE,
        )

        # 영화코드를 기준으로 오름차순 정렬
        movies.sort(
            key=lambda movie: movie["movieCd"]
        )

        save_to_csv(
            movies=movies,
            output_file=OUTPUT_FILE,
        )

        print()
        print(f"중복 제거 후 영화 수: {len(movies)}")
        print(f"CSV 저장 경로: {OUTPUT_FILE}")

    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        print(f"설정 오류: {error}")

    except Exception as error:
        print(f"예상하지 못한 오류가 발생했습니다: {error}")


if __name__ == "__main__":
    main()