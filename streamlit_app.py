import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 패션 스타일리스트",
    page_icon="👗",
    initial_sidebar_state="expanded"
)

# --- 계층적 도시 데이터 구조 (locations.py 파일에서 불러왔다고 가정) ---
# 이 데이터는 별도의 locations.py 파일에 저장되어 있어야 합니다.
from locations import HIERARCHICAL_CITY_COORDS


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    kma_service_key = st.text_input("기상청 API 서비스 키", type="password")
    
    st.divider()

    st.header("사용자 정보 🤵‍♀️")
    st.info("정보는 실시간으로 저장됩니다.")

    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "sido": "서울특별시", "gungu": "(전체)", "date": datetime.now().date(),
            "gender": "여성", "age": "20대", "height": "", "weight": "",
            "style_preference": "캐주얼", "tpo": "일상", "personal_color": "모름"
        }

    st.subheader("지역 및 날짜 선택")
    
    selected_date = st.date_input(
        "날짜 선택",
        value=st.session_state.user_info.get("date", datetime.now().date()),
        min_value=datetime.now().date(),
        max_value=datetime.now().date() + timedelta(days=5),
        help="오늘부터 최대 5일 후까지의 날씨를 조회할 수 있습니다."
    )
    st.session_state.user_info["date"] = selected_date
    
    sido_list = list(HIERARCHICAL_CITY_COORDS.keys())
    selected_sido = st.selectbox(
        "시/도", sido_list,
        index=sido_list.index(st.session_state.user_info.get("sido", "서울특별시"))
    )

    if selected_sido != st.session_state.user_info.get("sido"):
        st.session_state.user_info["sido"] = selected_sido
        st.session_state.user_info["gungu"] = "(전체)"
        st.rerun()
    
    gungu_list = [g for g in HIERARCHICAL_CITY_COORDS[st.session_state.user_info["sido"]] if g != "_default"]
    gungu_list.sort()
    gungu_options = ["(전체)"] + gungu_list
    
    selected_gungu = st.selectbox(
        "구/군", gungu_options,
        index=gungu_options.index(st.session_state.user_info.get("gungu", "(전체)"))
    )
    st.session_state.user_info["gungu"] = selected_gungu

    st.divider()

    st.subheader("개인 정보")
    st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info.get("gender", "여성")))
    
    age_options = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대 이상"]
    st.session_state.user_info["age"] = st.selectbox("나이", age_options, index=age_options.index(st.session_state.user_info.get("age", "20대")))
    
    st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info.get("height", ""))
    st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info.get("weight", ""))

    st.divider()

    st.subheader("스타일 정보")
    st.session_state.user_info["style_preference"] = st.selectbox("선호 스타일", ["캐주얼", "미니멀", "스트릿", "포멀", "빈티지", "스포티"])
    st.session_state.user_info["tpo"] = st.text_input("TPO (시간, 장소, 상황)", placeholder="예: 주말 데이트", value=st.session_state.user_info.get("tpo", "일상"))
    st.session_state.user_info["personal_color"] = st.selectbox("퍼스널 컬러", ["모름", "봄 웜톤", "여름 쿨톤", "가을 웜톤", "겨울 쿨톤"])


# --- 날씨 API 함수 ---
def get_kma_weather_forecast(coords, service_key, target_date):
    if not service_key:
        return "오류: 기상청 서비스 키가 입력되지 않았습니다."
    nx, ny = coords["nx"], coords["ny"]
    now = datetime.now()
    publication_times = [2, 5, 8, 11, 14, 17, 20, 23]
    valid_times = [t for t in publication_times if t <= now.hour]
    if not valid_times:
        base_day = now - timedelta(days=1)
        base_time_hour = 23
    else:
        base_day = now
        base_time_hour = max(valid_times)
    base_date = base_day.strftime("%Y%m%d")
    base_time = f"{base_time_hour:02d}00"
    target_date_str = target_date.strftime("%Y%m%d")
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {"serviceKey": service_key, "pageNo": "1", "numOfRows": "1000",
              "dataType": "JSON", "base_date": base_date, "base_time": base_time,
              "nx": str(nx), "ny": str(ny)}

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            return f"기상청 API 오류: {header.get('resultMsg', '알 수 없는 오류')}"
        
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items: return "오류: 날씨 정보를 찾을 수 없습니다. (응답 데이터 없음)"

        is_today = (target_date == datetime.now().date())
        
        target_day_weather = {}
        for item in items:
            if item.get("fcstDate") == target_date_str:
                category = item.get("category")
                if category:
                    if category not in target_day_weather: target_day_weather[category] = []
                    target_day_weather[category].append(item.get("fcstValue"))

        if not target_day_weather: return f"오류: {target_date.strftime('%Y년 %m월 %d일')}의 예보가 아직 없습니다."
        
        if not is_today:
            tmn = next((val for val in target_day_weather.get("TMN", [])), None)
            tmx = next((val for val in target_day_weather.get("TMX", [])), None)
            weather_info = f"**기온**: 최저 {tmn or '-'}°C / 최고 {tmx or '-'}°C\n"
        else:
            current_hour_str = now.strftime("%H00")
            current_t1h = None
            for i, time in enumerate(target_day_weather.get("fcstTime", [])):
                if time == current_hour_str:
                    current_t1h = target_day_weather.get("T1H", [])[i]
                    break
            weather_info = f"**현재 기온**: {current_t1h or '-'}°C\n"

        sky_values = target_day_weather.get("SKY", [])
        sky_codes = {"1": "맑음", "3": "구름 많음", "4": "흐림"}
        main_sky_code = max(set(sky_values), key=sky_values.count) if sky_values else "1"
        main_sky = sky_codes.get(main_sky_code, "정보 없음")
        
        has_precipitation = any(p != "0" for p in target_day_weather.get("PTY", []))
        weather_info += (f"**날씨**: {main_sky}\n"
                         f"**강수 여부**: {'비 또는 눈 소식이 있습니다.' if has_precipitation else '비/눈 소식은 없습니다.'}")
        return weather_info
        
    except Exception as e:
        return f"오류: 날씨 정보 조회 중 알 수 없는 문제가 발생했습니다. ({e})"


# --- 메인 챗봇 화면 ---
st.title("👗 AI 패션 스타일리스트")
st.write("내 정보와 원하는 날짜의 날씨에 맞는 스타일을 추천받아보세요.")

# 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 당신만의 스타일리스트가 되어드릴게요. 어떤 도움이 필요하세요?"}]

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- [수정됨] 대표 질문 버튼을 표시하는 함수 ---
def display_action_buttons():
    st.subheader("어떤 추천을 원하세요? 👇")
    example_questions = ["패션 추천받기 👕", "데이트룩 추천 💖", "소개팅룩 추천해줘 ✨"]
    cols = st.columns(len(example_questions))
    
    for i, question in enumerate(example_questions):
        if cols[i].button(question, use_container_width=True, key=f"action_btn_{i}"):
            if "데이트" in question: st.session_state.user_info["tpo"] = "주말 데이트"
            elif "소개팅" in question: st.session_state.user_info["tpo"] = "소개팅"
            else: st.session_state.user_info["tpo"] = "일상"
            return question
    return None

# --- AI 응답 처리 로직 ---
# 프롬프트가 있을 경우에만 실행
prompt = st.chat_input("메시지를 입력하세요...") or display_action_buttons()

if prompt:
    # API 키 확인
    if not openai_api_key or not kma_service_key:
        st.error("사이드바에서 OpenAI API 키와 기상청 서비스 키를 모두 입력해주세요.")
        st.stop()
    
    client = OpenAI(api_key=openai_api_key)

    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성 및 표시
    with st.chat_message("assistant"):
        with st.spinner("선택하신 날짜의 날씨를 확인하고, 맞춤 스타일을 추천하는 중..."):
            sido = st.session_state.user_info["sido"]
            gungu = st.session_state.user_info["gungu"]
            target_date = st.session_state.user_info["date"]
            
            coords_to_use = HIERARCHICAL_CITY_COORDS[sido].get(gungu if gungu != "(전체)" else "_default")
            location_name = f"{sido} {gungu}" if gungu != "(전체)" else sido
            
            weather_info = get_kma_weather_forecast(coords_to_use, kma_service_key, target_date)
            
            if "오류" in weather_info:
                st.error(weather_info)
                st.stop()

            user_info_text = (
                f"- 지역: {location_name}\n- 날짜: {target_date.strftime('%Y년 %m월 %d일')}\n"
                f"- 성별: {st.session_state.user_info.get('gender')}\n- 나이: {st.session_state.user_info.get('age')}\n"
                f"- TPO: {st.session_state.user_info.get('tpo')}\n- 선호 스타일: {st.session_state.user_info.get('style_preference')}\n"
                f"- 퍼스널 컬러: {st.session_state.user_info.get('personal_color')}"
            )
            
            system_prompt = f"""
            당신은 사용자의 개인 정보, TPO, 패션 취향, 퍼스널 컬러와 **선택된 날짜의 날씨**를 종합 분석하여 패션을 추천하는 전문 AI 스타일리스트입니다.
            **[답변 생성 규칙]**
            1.  **답변 시작**: 가장 먼저, 어떤 사용자의 정보를 바탕으로 추천하는지 핵심만 요약해서 알려주세요.
            2.  **날씨 정보**: '**{location_name}**의 **{target_date.strftime('%Y년 %m월 %d일')}** 날씨 정보'라는 제목으로 섹션을 만들고, 그 아래에 전달받은 날씨 데이터를 보여주세요.
            3.  **패션 추천**: '패션 추천' 섹션에서 날씨, TPO, 퍼스널 컬러 등을 모두 고려하여 1~2가지의 완성된 착장을 제안합니다.
            4.  **스타일링 팁**: '스타일링 팁' 섹션에서 추가적인 팁을 제안합니다.
            5.  **우산 안내 (조건부)**: 만약 날씨 정보에 '**비 또는 눈 소식이 있습니다.**' 라는 내용이 포함되어 있다면, '우산 챙기세요! ☔️' 라는 섹션을 추가하고 상냥하게 알려주세요.
            6.  **말투**: 모든 답변은 친절하고 전문적인 말투를 사용해주세요.
            """
            
            final_prompt = f"""
            아래 날씨와 사용자 정보를 바탕으로, 요청에 맞는 패션을 추천해줘.
            [선택한 날짜의 날씨 정보]
            {weather_info}
            [사용자 정보]
            {user_info_text}
            [사용자 요청]
            {prompt}
            """
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": final_prompt}],
                    stream=True
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # --- [수정됨] 응답 후 버튼을 다시 표시하기 위해 스크립트 재실행 ---
                st.rerun()

            except Exception as e:
                st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
