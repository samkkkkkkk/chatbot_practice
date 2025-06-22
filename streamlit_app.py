import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 (수정됨: 사이드바 기본 열림) ---
st.set_page_config(
    page_title="AI 패션 스타일리스트",
    page_icon="👗",
    initial_sidebar_state="expanded"
)

# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    kma_service_key = st.text_input("기상청 API 서비스 키", type="password")
    
    st.divider()

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 자세히 입력할수록 좋습니다.")
    
    CITY_COORDS = {
        "서울": {"nx": 60, "ny": 127}, "부산": {"nx": 98, "ny": 76},
        "인천": {"nx": 55, "ny": 124}, "대구": {"nx": 89, "ny": 90},
        "광주": {"nx": 58, "ny": 74}, "대전": {"nx": 67, "ny": 100},
        "제주": {"nx": 52, "ny": 38}, "수원": {"nx": 60, "ny": 121},
    }

    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "city": "서울", "gender": "여성", "age": "20대", "height": "", "weight": "",
            "style_preference": "캐주얼", "tpo": "일상", "preferred_color": "",
            "personal_color": "모름"
        }

    with st.form("user_info_form"):
        st.subheader("개인 정보")
        st.session_state.user_info["city"] = st.selectbox("도시", list(CITY_COORDS.keys()), index=list(CITY_COORDS.keys()).index(st.session_state.user_info["city"]))
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        st.session_state.user_info["age"] = st.text_input("나이 (예: 20대)", value=st.session_state.user_info["age"])
        st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info["height"])
        st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info["weight"])

        st.divider()

        st.subheader("스타일 정보")
        st.session_state.user_info["style_preference"] = st.selectbox("선호 스타일", ["캐주얼", "미니멀", "스트릿", "포멀", "빈티지", "스포티"])
        st.session_state.user_info["tpo"] = st.text_input("TPO (시간, 장소, 상황)", placeholder="예: 주말 데이트", value=st.session_state.user_info["tpo"])
        st.session_state.user_info["personal_color"] = st.selectbox("퍼스널 컬러", ["모름", "봄 웜톤", "여름 쿨톤", "가을 웜톤", "겨울 쿨톤"])

        submitted = st.form_submit_button("정보 저장")
        if submitted:
            st.success("정보가 저장되었습니다!")

# --- 안정성을 개선한 기상청 API 함수 ---
def get_kma_weather_forecast(city, service_key):
    """기상청 단기예보 API로 내일 날씨 정보를 가져옵니다. (안정성 개선 버전)"""
    if not service_key:
        return "오류: 기상청 서비스 키가 입력되지 않았습니다."

    coords = CITY_COORDS[city]
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
    tomorrow_date_str = (now + timedelta(days=1)).strftime("%Y%m%d")
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": service_key, "pageNo": "1", "numOfRows": "1000",
        "dataType": "JSON", "base_date": base_date, "base_time": base_time,
        "nx": str(nx), "ny": str(ny)
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            return f"기상청 API 오류: {header.get('resultMsg', '알 수 없는 오류')}"

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            return "오류: 날씨 정보를 찾을 수 없습니다. (응답 데이터 없음)"

        tomorrow_weather = {}
        for item in items:
            if item.get("fcstDate") == tomorrow_date_str:
                category = item.get("category")
                if category:
                    if category not in tomorrow_weather:
                        tomorrow_weather[category] = []
                    tomorrow_weather[category].append(item.get("fcstValue"))
        
        if not tomorrow_weather: return "오류: 내일 날씨 예보가 아직 없습니다."
            
        tmn = next((val for val in tomorrow_weather.get("TMN", [])), None)
        tmx = next((val for val in tomorrow_weather.get("TMX", [])), None)
        
        sky_codes = {"1": "맑음", "3": "구름 많음", "4": "흐림"}
        sky_values = tomorrow_weather.get("SKY", [])
        main_sky_code = max(set(sky_values), key=sky_values.count) if sky_values else "1"
        main_sky = sky_codes.get(main_sky_code, "정보 없음")

        has_precipitation = any(p != "0" for p in tomorrow_weather.get("PTY", []))
        if not has_precipitation:
             pop_values = [int(p) for p in tomorrow_weather.get("POP", []) if p.isdigit()]
             if any(p > 40 for p in pop_values):
                 has_precipitation = True

        weather_info = (
            f"**날씨**: {main_sky}\n"
            f"**기온**: 최저 {tmn or '-'}°C / 최고 {tmx or '-'}°C\n"
            f"**강수 여부**: {'비 또는 눈 소식이 있습니다.' if has_precipitation else '비/눈 소식은 없습니다.'}"
        )
        return weather_info
    except requests.exceptions.Timeout:
        return "오류: 기상청 서버 응답 시간이 초과되었습니다."
    except Exception as e:
        return f"오류: 날씨 정보 조회 중 알 수 없는 문제가 발생했습니다. ({e})"

# --- 메인 챗봇 화면 ---
st.title("👗 AI 패션 스타일리스트")
st.write("내 정보와 내일 날씨에 맞는 스타일을 손쉽게 추천받아보세요.")

st.subheader("어떤 추천을 원하세요? 👇")
example_questions = ["내일 뭐 입지? 👕", "주말 데이트룩 추천 💖", "소개팅룩 추천해줘 ✨"]
cols = st.columns(len(example_questions))
prompt = None
for i, question in enumerate(example_questions):
    if cols[i].button(question, use_container_width=True):
        prompt = question
        if "데이트" in question: st.session_state.user_info["tpo"] = "주말 데이트"
        elif "소개팅" in question: st.session_state.user_info["tpo"] = "소개팅"
        else: st.session_state.user_info["tpo"] = "일상"
chat_input = st.chat_input("메시지를 입력하세요...")
if chat_input:
    prompt = chat_input
if not openai_api_key or not kma_service_key:
    st.info("사이드바에서 OpenAI API 키와 기상청 서비스 키를 모두 입력해주세요.")
    st.stop()
client = OpenAI(api_key=openai_api_key)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 당신만의 스타일리스트가 되어드릴게요. 어떤 도움이 필요하세요?"}]
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("날씨 정보를 확인하고, 맞춤 스타일을 추천하는 중..."):
            weather_info = get_kma_weather_forecast(st.session_state.user_info["city"], kma_service_key)
            
            if "오류" in weather_info:
                st.error(weather_info)
                st.stop()
            
            user_info_text = (f"- 성별: {st.session_state.user_info.get('gender')}\n- 나이: {st.session_state.user_info.get('age')}\n"
                              f"- TPO: {st.session_state.user_info.get('tpo')}\n- 선호 스타일: {st.session_state.user_info.get('style_preference')}\n"
                              f"- 퍼스널 컬러: {st.session_state.user_info.get('personal_color')}")
            
            # --- 시스템 프롬프트 수정 (우산 안내 조건부로 변경) ---
            system_prompt = f"""
            당신은 사용자의 개인 정보, TPO, 패션 취향, 퍼스널 컬러와 **내일 날씨**를 종합 분석하여 패션을 추천하는 전문 AI 스타일리스트입니다.
            1.  먼저 '내일 날씨 정보' 섹션을 만들어 전달받은 날씨 정보를 보여줍니다.
            2.  '패션 추천' 섹션에서 날씨, TPO, 퍼스널 컬러 등을 모두 고려하여 1~2가지의 완성된 착장을 제안합니다.
            3.  '스타일링 팁' 섹션에서 추가적인 팁을 제안합니다.
            4.  만약 날씨 정보에 '**비 또는 눈 소식이 있습니다.**' 라는 내용이 포함되어 있다면, '우산 챙기세요! ☔️' 라는 섹션을 추가하고 "내일은 비나 눈이 올 수 있으니, 외출하실 때 작은 우산을 챙기는 걸 잊지 마세요!" 라고 상냥하게 알려주세요. 비 소식이 없다면 이 섹션은 만들지 않습니다.
            5.  모든 답변은 친절하고 전문적인 말투를 사용해주세요.
            """
            
            final_prompt = f"""
            아래 날씨와 사용자 정보를 바탕으로, 요청에 맞는 패션을 추천해줘.
            [내일 날씨 정보]
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
                    stream=True,
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
