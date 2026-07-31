import streamlit as st
import altair as alt

from backend import (
    get_month_list,
    get_genre_list,
    get_monthly_audience,
    get_scatter_data,
    get_nation_audience,
    get_nation_sales,
    get_genre_sales,
)


'''
아래 강사님께서 작성해주신 주석 참고하여 작성 부탁드립니다.

데이터 로딩(loading) 시 null or '' or "" 밸리데이션 처리 부탁드립니다.
'''

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



st.sidebar.header('데이터 필터링')

try:
    month_options = get_month_list()
    genre_options = get_genre_list()
except Exception as error:
    st.error(f'필터 데이터를 불러오지 못했습니다: {error}')
    st.stop()

if not month_options:
    st.warning('월 데이터가 없습니다.')
    st.stop()

st.sidebar.info('월 범위 / 장르를 선택하세요')

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


#백엔드 호출
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
            chart_df = monthly_df.rename(columns={'월': 'month', '관객수': 'audience'})
            bar = (
                alt.Chart(chart_df)
                .mark_bar(color='#3b82f6')
                .encode(
                    x=alt.X('month:N', title='월', sort=month_options),
                    y=alt.Y('audience:Q', title='관객수'),
                    tooltip=['month', 'audience'],
                )
                .properties(height=360)
            )
            st.altair_chart(bar, use_container_width=True)
            st.dataframe(monthly_df, use_container_width=True)

    with right:
        st.subheader('산점도 (스크린수 × 관객수)')
        if scatter_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            scatter = (
                alt.Chart(scatter_df)
                .mark_circle(size=80, opacity=0.7)
                .encode(
                    x=alt.X('스크린수:Q', title='스크린수'),
                    y=alt.Y('관객수:Q', title='관객수'),
                    color=alt.Color('대표국적:N', title='대표국적'),
                    tooltip=['영화명', '월', '스크린수', '관객수', '매출액', '대표국적', '장르'],
                )
                .properties(height=360)
            )
            st.altair_chart(scatter, use_container_width=True)
            st.dataframe(
                scatter_df[
                    ['월', '영화명', '스크린수', '관객수', '매출액', '대표국적', '장르']
                ],
                use_container_width=True,
            )



with tab2:
    st.subheader('국가별 관객수')
    if nation_audience_df.empty:
        st.info('선택한 조건에 해당하는 데이터가 없습니다.')
    else:
        col_chart, col_table = st.columns([1.2, 1])
        with col_chart:
            pie = (
                alt.Chart(nation_audience_df)
                .mark_arc(innerRadius=50)
                .encode(
                    theta=alt.Theta('관객수:Q'),
                    color=alt.Color(
                        '국가그룹:N',
                        title='국가그룹',
                        scale=alt.Scale(
                            domain=['한국', '미국', '기타'],
                            range=['#2563eb', '#f59e0b', '#94a3b8'],
                        ),
                    ),
                    tooltip=['국가그룹', '관객수'],
                )
                .properties(height=400)
            )
            st.altair_chart(pie, use_container_width=True)
        with col_table:
            st.dataframe(nation_audience_df, use_container_width=True)



with tab3:
    left, right = st.columns(2)

    with left:
        st.subheader('국가별 매출액')
        if nation_sales_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            nation_chart = (
                alt.Chart(nation_sales_df)
                .mark_bar(color='#3b82f6')
                .encode(
                    x=alt.X(
                        '국가그룹:N',
                        title='국가',
                        sort=['한국', '미국', '기타'],
                    ),
                    y=alt.Y('매출액:Q', title='매출액'),
                    tooltip=['국가그룹', '매출액'],
                )
                .properties(height=360)
            )
            st.altair_chart(nation_chart, use_container_width=True)
            st.dataframe(nation_sales_df, use_container_width=True)

    with right:
        st.subheader('장르별 매출액')
        if genre_sales_df.empty:
            st.info('선택한 조건에 해당하는 데이터가 없습니다.')
        else:
            genre_chart = (
                alt.Chart(genre_sales_df)
                .mark_bar(color='#3b82f6')
                .encode(
                    x=alt.X('장르:N', title='장르', sort='-y'),
                    y=alt.Y('매출액:Q', title='매출액'),
                    tooltip=['장르', '매출액'],
                )
                .properties(height=360)
            )
            st.altair_chart(genre_chart, use_container_width=True)
            st.dataframe(genre_sales_df, use_container_width=True)
