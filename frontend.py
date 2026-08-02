import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from backend import (
    get_month_list,
    get_genre_list,
    get_monthly_audience,
    get_scatter_data,
    get_nation_audience,
    get_nation_sales,
    get_genre_sales,
)


# 한글 폰트 설정 (맥 기본)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------
# st.set_page_config()는 Streamlit 페이지의 기본 설정을 지정한다.
# page_title: 브라우저 탭에 표시되는 제목
# layout="wide": 화면을 넓게 사용
# ------------------------------------------------------------
st.set_page_config(
    page_title='영화 박스오피스 대시보드',
    layout='wide',
)

st.title('영화 박스오피스 대시보드')
st.caption('월별 관객 · 국가별 관객 · 국가/장르별 매출 시각화')


st.sidebar.header('월 범위와 장르를 선택하세요')

try:
    month_options = get_month_list()
    genre_options = get_genre_list()
except Exception as error:
    st.error(f'필터 데이터를 불러오지 못했습니다: {error}')
    st.stop()

if not month_options:
    st.warning('월 데이터가 없습니다.')
    st.stop()


start_month, end_month = st.sidebar.select_slider(
    '월 범위 선택',
    options=month_options,
    value=(month_options[0], month_options[-1]),
)
selected_months = [
    month for month in month_options if start_month <= month <= end_month
]

selected_genres = st.sidebar.multiselect(
    '장르 선택',
    options=genre_options,
    default=genre_options,
    help='비우면 전체 장르로 조회합니다.',
)


# 백엔드 호출
try:
    monthly_df = get_monthly_audience(selected_months, selected_genres)
    scatter_df = get_scatter_data(selected_months, selected_genres)
    nation_audience_df = get_nation_audience(selected_months, selected_genres)
    nation_sales_df = get_nation_sales(selected_months, selected_genres)
    genre_sales_df = get_genre_sales(selected_months, selected_genres)
except Exception as error:
    st.error(f'차트 데이터를 불러오지 못했습니다: {error}')
    st.stop()


total_audience = int(monthly_df['관객수'].sum()) if not monthly_df.empty else 0
movie_count = int(scatter_df['영화명'].nunique()) if not scatter_df.empty else 0
top_movie = (
    scatter_df.sort_values('관객수', ascending=False).iloc[0]['영화명']
    if not scatter_df.empty
    else '-'
)
avg_sales = int(scatter_df['매출액'].mean()) if not scatter_df.empty else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric('선택된 영화 수', f'{movie_count:,} 편')
kpi2.metric('기간 내 관객 1위', top_movie)
kpi3.metric('총 관객수', f'{total_audience:,} 명')
kpi4.metric('평균 매출액', f'{avg_sales:,.0f} 원')


tab1, tab2, tab3 = st.tabs(
    [
        'Tab1. 월별 관객수 / 산점도',
        'Tab2. 국가별 관객수',
        'Tab3. 국가·장르별 매출',
    ]
)


with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader('월별 영화 관객수')
        if monthly_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            plot_df = monthly_df.copy()
            plot_df['월'] = plot_df['월'].astype(str)
            ordered_months = [m for m in month_options if m in set(plot_df['월'])]
            plot_df = plot_df.set_index('월').reindex(ordered_months).reset_index()
            plot_df['관객수_만'] = plot_df['관객수'] / 1e4  # 1만 명

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(plot_df['월'].astype(str), plot_df['관객수_만'], color='#3b82f6')
            ax.set_xlabel('월')
            ax.set_ylabel('관객수 (만 명)')
            ax.tick_params(axis='x', rotation=0)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.dataframe(monthly_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader('산점도 (스크린수 × 관객수)')
        if scatter_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            fig, ax = plt.subplots(figsize=(7, 4))
            nation_colors = {
                '한국': '#2563eb',
                '미국': '#f59e0b',
            }
            for nation, group in scatter_df.groupby('대표국적'):
                ax.scatter(
                    group['스크린수'],
                    group['관객수'] / 1e4,  # 만 명
                    s=80,
                    alpha=0.7,
                    label=str(nation),
                    color=nation_colors.get(str(nation), '#94a3b8'),
                )
            ax.set_xlabel('스크린수')
            ax.set_ylabel('관객수 (만 명)')
            ax.legend(title='대표국적', fontsize=8)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.dataframe(
                scatter_df[
                    ['월', '영화명', '스크린수', '관객수', '매출액', '대표국적', '장르']
                ],
                use_container_width=True,
                hide_index=True,
            )


with tab2:
    st.subheader('국가별 관객수')
    if nation_audience_df.empty:
        st.info('선택한 조건에 해당하는 데이터가 없습니다.')
    else:
        col_chart, col_table = st.columns([1.2, 1])
        with col_chart:
            pie_df = nation_audience_df.copy()
            pie_df['국가그룹'] = pie_df['국가그룹'].astype(str)
            pie_df['관객수'] = pd.to_numeric(pie_df['관객수'], errors='coerce').fillna(0)
            pie_df = pie_df[pie_df['관객수'] > 0].copy()

            order = ['한국', '미국', '기타']
            pie_df['국가그룹'] = pd.Categorical(
                pie_df['국가그룹'],
                categories=order,
                ordered=True,
            )
            pie_df = pie_df.sort_values('국가그룹')

            if pie_df.empty or pie_df['관객수'].sum() <= 0:
                st.info('선택한 조건에 해당하는 데이터가 없습니다.')
            else:
                color_map = {
                    '한국': '#2563eb',
                    '미국': '#f59e0b',
                    '기타': '#94a3b8',
                }
                colors = [
                    color_map.get(str(name), '#94a3b8')
                    for name in pie_df['국가그룹']
                ]

                def _format_pct(value: float) -> str:
                    # 값이 있어도 항상 퍼센트 표시
                    return f'{value:.1f}%'

                fig, ax = plt.subplots(figsize=(6, 5))
                wedges, texts, autotexts = ax.pie(
                    pie_df['관객수'],
                    labels=pie_df['국가그룹'].astype(str),
                    autopct=_format_pct,
                    colors=colors,
                    startangle=90,
                    pctdistance=0.55,
                    labeldistance=1.05,
                )
                # 배경색과 대비되도록 퍼센트는 검정으로 표시
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontsize(11)
                    autotext.set_fontweight('bold')
                ax.axis('equal')
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        with col_table:
            st.dataframe(nation_audience_df, use_container_width=True, hide_index=True)


with tab3:
    left, right = st.columns(2)

    with left:
        st.subheader('국가별 매출액')
        if nation_sales_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            sales_df = nation_sales_df.copy()
            order = ['한국', '미국', '기타']
            sales_df['국가그룹'] = sales_df['국가그룹'].astype(str)
            sales_df = sales_df.set_index('국가그룹').reindex(order).dropna().reset_index()
            sales_df['매출액_억'] = sales_df['매출액'] / 1e8

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(sales_df['국가그룹'], sales_df['매출액_억'], color='#3b82f6')
            ax.set_xlabel('국가')
            ax.set_ylabel('매출액 (억 원)')
            ax.tick_params(axis='x', rotation=0)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.dataframe(nation_sales_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader('장르별 매출액')
        if genre_sales_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            genre_df = genre_sales_df.sort_values('매출액', ascending=False).copy()
            genre_df['매출액_억'] = genre_df['매출액'] / 1e8

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(genre_df['장르'].astype(str), genre_df['매출액_억'], color='#3b82f6')
            ax.set_xlabel('장르')
            ax.set_ylabel('매출액 (억 원)')
            ax.tick_params(axis='x', rotation=45)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.dataframe(genre_sales_df, use_container_width=True, hide_index=True)
