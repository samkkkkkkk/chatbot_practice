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

# --- [수정됨] 계층적 도시 데이터 구조 ---
# UI 편의성을 위해 시/도, 구/군으로 분리하고, 각 시/도의 대표 좌표를 '_default'로 지정
HIERARCHICAL_CITY_COORDS = {
    "서울특별시": {
        "_default": {"nx": 60, "ny": 127}, "종로구": {"nx": 60, "ny": 127}, "중구": {"nx": 60, "ny": 127}, "용산구": {"nx": 60, "ny": 126},
        "성동구": {"nx": 61, "ny": 127}, "광진구": {"nx": 62, "ny": 126}, "동대문구": {"nx": 61, "ny": 127},
        "중랑구": {"nx": 62, "ny": 128}, "성북구": {"nx": 61, "ny": 127}, "강북구": {"nx": 61, "ny": 128},
        "도봉구": {"nx": 61, "ny": 129}, "노원구": {"nx": 61, "ny": 129}, "은평구": {"nx": 59, "ny": 127},
        "서대문구": {"nx": 59, "ny": 127}, "마포구": {"nx": 59, "ny": 127}, "양천구": {"nx": 58, "ny": 126},
        "강서구": {"nx": 58, "ny": 126}, "구로구": {"nx": 58, "ny": 125}, "금천구": {"nx": 59, "ny": 124},
        "영등포구": {"nx": 58, "ny": 126}, "동작구": {"nx": 59, "ny": 125}, "관악구": {"nx": 59, "ny": 125},
        "서초구": {"nx": 61, "ny": 125}, "강남구": {"nx": 61, "ny": 126}, "송파구": {"nx": 62, "ny": 126},
        "강동구": {"nx": 62, "ny": 126},
    },
    "부산광역시": {
        "_default": {"nx": 98, "ny": 76}, "중구": {"nx": 98, "ny": 76}, "서구": {"nx": 97, "ny": 76}, "동구": {"nx": 98, "ny": 76},
        "영도구": {"nx": 98, "ny": 75}, "부산진구": {"nx": 98, "ny": 76}, "동래구": {"nx": 98, "ny": 77},
        "남구": {"nx": 98, "ny": 76}, "북구": {"nx": 97, "ny": 77}, "해운대구": {"nx": 99, "ny": 76},
        "사하구": {"nx": 96, "ny": 74}, "금정구": {"nx": 98, "ny": 78}, "강서구": {"nx": 96, "ny": 77},
        "연제구": {"nx": 98, "ny": 77}, "수영구": {"nx": 99, "ny": 76}, "사상구": {"nx": 97, "ny": 76},
        "기장군": {"nx": 100, "ny": 78},
    },
    "대구광역시": {
        "_default": {"nx": 89, "ny": 90}, "중구": {"nx": 89, "ny": 90}, "동구": {"nx": 90, "ny": 91}, "서구": {"nx": 88, "ny": 90},
        "남구": {"nx": 89, "ny": 90}, "북구": {"nx": 89, "ny": 91}, "수성구": {"nx": 89, "ny": 90},
        "달서구": {"nx": 88, "ny": 89}, "달성군": {"nx": 87, "ny": 88}, "군위군": {"nx": 89, "ny": 98},
    },
    "인천광역시": {
        "_default": {"nx": 55, "ny": 124}, "중구": {"nx": 54, "ny": 125}, "동구": {"nx": 55, "ny": 125}, "미추홀구": {"nx": 55, "ny": 124},
        "연수구": {"nx": 55, "ny": 123}, "남동구": {"nx": 56, "ny": 124}, "부평구": {"nx": 55, "ny": 125},
        "계양구": {"nx": 55, "ny": 126}, "서구": {"nx": 54, "ny": 126}, "강화군": {"nx": 51, "ny": 130},
        "옹진군": {"nx": 46, "ny": 122},
    },
    "광주광역시": {
        "_default": {"nx": 60, "ny": 74}, "동구": {"nx": 60, "ny": 74}, "서구": {"nx": 59, "ny": 74}, "남구": {"nx": 60, "ny": 73},
        "북구": {"nx": 60, "ny": 75}, "광산구": {"nx": 57, "ny": 74},
    },
    "대전광역시": {
        "_default": {"nx": 68, "ny": 100}, "동구": {"nx": 68, "ny": 100}, "중구": {"nx": 68, "ny": 100}, "서구": {"nx": 67, "ny": 100},
        "유성구": {"nx": 67, "ny": 101}, "대덕구": {"nx": 68, "ny": 100},
    },
    "울산광역시": {
        "_default": {"nx": 102, "ny": 84}, "중구": {"nx": 102, "ny": 84}, "남구": {"nx": 102, "ny": 84}, "동구": {"nx": 103, "ny": 84},
        "북구": {"nx": 102, "ny": 85}, "울주군": {"nx": 101, "ny": 83},
    },
    "세종특별자치시": {
        "_default": {"nx": 66, "ny": 103},
    },
    "경기도": {
        "_default": {"nx": 60, "ny": 121}, "수원시 장안구": {"nx": 60, "ny": 121}, "수원시 권선구": {"nx": 60, "ny": 120}, "수원시 팔달구": {"nx": 60, "ny": 121},
        "수원시 영통구": {"nx": 61, "ny": 121}, "성남시 수정구": {"nx": 62, "ny": 124}, "성남시 중원구": {"nx": 62, "ny": 123},
        "성남시 분당구": {"nx": 62, "ny": 122}, "의정부시": {"nx": 61, "ny": 130}, "안양시 만안구": {"nx": 59, "ny": 123},
        "안양시 동안구": {"nx": 59, "ny": 123}, "부천시": {"nx": 57, "ny": 125}, "광명시": {"nx": 58, "ny": 125},
        "평택시": {"nx": 61, "ny": 114}, "동두천시": {"nx": 61, "ny": 134}, "안산시 상록구": {"nx": 57, "ny": 122},
        "안산시 단원구": {"nx": 56, "ny": 121}, "고양시 덕양구": {"nx": 57, "ny": 128}, "고양시 일산동구": {"nx": 56, "ny": 129},
        "고양시 일산서구": {"nx": 56, "ny": 129}, "과천시": {"nx": 60, "ny": 124}, "구리시": {"nx": 62, "ny": 127},
        "남양주시": {"nx": 63, "ny": 128}, "오산시": {"nx": 61, "ny": 118}, "시흥시": {"nx": 56, "ny": 122},
        "군포시": {"nx": 59, "ny": 122}, "의왕시": {"nx": 59, "ny": 122}, "하남시": {"nx": 63, "ny": 126},
        "용인시 처인구": {"nx": 62, "ny": 119}, "용인시 기흥구": {"nx": 61, "ny": 120}, "용인시 수지구": {"nx": 61, "ny": 121},
        "파주시": {"nx": 56, "ny": 131}, "이천시": {"nx": 65, "ny": 121}, "안성시": {"nx": 63, "ny": 114},
        "김포시": {"nx": 56, "ny": 128}, "화성시": {"nx": 58, "ny": 119}, "광주시": {"nx": 63, "ny": 124},
        "양주시": {"nx": 61, "ny": 131}, "포천시": {"nx": 63, "ny": 134}, "여주시": {"nx": 68, "ny": 122},
        "연천군": {"nx": 60, "ny": 138}, "가평군": {"nx": 66, "ny": 132}, "양평군": {"nx": 66, "ny": 126},
    },
    "강원특별자치도": {
        "_default": {"nx": 73, "ny": 134}, "춘천시": {"nx": 73, "ny": 134}, "원주시": {"nx": 76, "ny": 122}, "강릉시": {"nx": 92, "ny": 131},
        "동해시": {"nx": 95, "ny": 129}, "태백시": {"nx": 95, "ny": 119}, "속초시": {"nx": 86, "ny": 141},
        "삼척시": {"nx": 97, "ny": 124}, "홍천군": {"nx": 76, "ny": 129}, "횡성군": {"nx": 78, "ny": 126},
        "영월군": {"nx": 84, "ny": 121}, "평창군": {"nx": 85, "ny": 126}, "정선군": {"nx": 89, "ny": 123},
        "철원군": {"nx": 65, "ny": 139}, "화천군": {"nx": 69, "ny": 137}, "양구군": {"nx": 75, "ny": 138},
        "인제군": {"nx": 80, "ny": 138}, "고성군": {"nx": 85, "ny": 144}, "양양군": {"nx": 88, "ny": 138},
    },
    "충청북도": {
        "_default": {"nx": 69, "ny": 107}, "청주시 상당구": {"nx": 69, "ny": 107}, "청주시 서원구": {"nx": 69, "ny": 106}, "청주시 흥덕구": {"nx": 68, "ny": 106},
        "청주시 청원구": {"nx": 69, "ny": 107}, "충주시": {"nx": 75, "ny": 116}, "제천시": {"nx": 80, "ny": 120},
        "보은군": {"nx": 72, "ny": 100}, "옥천군": {"nx": 72, "ny": 96}, "영동군": {"nx": 76, "ny": 93},
        "증평군": {"nx": 71, "ny": 111}, "진천군": {"nx": 68, "ny": 114}, "괴산군": {"nx": 73, "ny": 113},
        "음성군": {"nx": 72, "ny": 116}, "단양군": {"nx": 84, "ny": 118},
    },
    "충청남도": {
        "_default": {"nx": 58, "ny": 104}, "천안시 동남구": {"nx": 63, "ny": 110}, "천안시 서북구": {"nx": 62, "ny": 111}, "공주시": {"nx": 64, "ny": 104},
        "보령시": {"nx": 55, "ny": 100}, "아산시": {"nx": 60, "ny": 110}, "서산시": {"nx": 52, "ny": 108},
        "논산시": {"nx": 62, "ny": 97}, "계룡시": {"nx": 64, "ny": 99}, "당진시": {"nx": 54, "ny": 111},
        "금산군": {"nx": 69, "ny": 95}, "부여군": {"nx": 59, "ny": 100}, "서천군": {"nx": 55, "ny": 95},
        "청양군": {"nx": 58, "ny": 102}, "홍성군": {"nx": 55, "ny": 105}, "예산군": {"nx": 58, "ny": 107},
        "태안군": {"nx": 49, "ny": 108},
    },
    "전북특별자치도": {
        "_default": {"nx": 63, "ny": 89}, "전주시 완산구": {"nx": 63, "ny": 89}, "전주시 덕진구": {"nx": 63, "ny": 89}, "군산시": {"nx": 56, "ny": 90},
        "익산시": {"nx": 60, "ny": 91}, "정읍시": {"nx": 59, "ny": 83}, "남원시": {"nx": 68, "ny": 80},
        "김제시": {"nx": 59, "ny": 88}, "완주군": {"nx": 64, "ny": 90}, "진안군": {"nx": 68, "ny": 88},
        "무주군": {"nx": 73, "ny": 90}, "장수군": {"nx": 71, "ny": 84}, "임실군": {"nx": 66, "ny": 83},
        "순창군": {"nx": 63, "ny": 80}, "고창군": {"nx": 55, "ny": 81}, "부안군": {"nx": 56, "ny": 86},
    },
    "전라남도": {
        "_default": {"nx": 56, "ny": 71}, "목포시": {"nx": 50, "ny": 69}, "여수시": {"nx": 73, "ny": 66}, "순천시": {"nx": 70, "ny": 69},
        "나주시": {"nx": 56, "ny": 71}, "광양시": {"nx": 73, "ny": 70}, "담양군": {"nx": 62, "ny": 78},
        "곡성군": {"nx": 66, "ny": 77}, "구례군": {"nx": 69, "ny": 75}, "고흥군": {"nx": 67, "ny": 64},
        "보성군": {"nx": 63, "ny": 66}, "화순군": {"nx": 62, "ny": 70}, "장흥군": {"nx": 59, "ny": 64},
        "강진군": {"nx": 57, "ny": 63}, "해남군": {"nx": 54, "ny": 61}, "영암군": {"nx": 55, "ny": 66},
        "무안군": {"nx": 51, "ny": 71}, "함평군": {"nx": 52, "ny": 74}, "영광군": {"nx": 52, "ny": 80},
        "장성군": {"nx": 56, "ny": 78}, "완도군": {"nx": 58, "ny": 58}, "진도군": {"nx": 48, "ny": 59},
        "신안군": {"nx": 48, "ny": 66},
    },
    "경상북도": {
        "_default": {"nx": 91, "ny": 106}, "포항시 남구": {"nx": 102, "ny": 94}, "포항시 북구": {"nx": 102, "ny": 95}, "경주시": {"nx": 100, "ny": 91},
        "김천시": {"nx": 84, "ny": 96}, "안동시": {"nx": 91, "ny": 106}, "구미시": {"nx": 86, "ny": 96},
        "영주시": {"nx": 87, "ny": 114}, "영천시": {"nx": 95, "ny": 93}, "상주시": {"nx": 81, "ny": 102},
        "문경시": {"nx": 81, "ny": 109}, "경산시": {"nx": 92, "ny": 91}, "의성군": {"nx": 90, "ny": 103},
        "청송군": {"nx": 96, "ny": 103}, "영양군": {"nx": 98, "ny": 108}, "영덕군": {"nx": 102, "ny": 104},
        "청도군": {"nx": 94, "ny": 86}, "고령군": {"nx": 85, "ny": 88}, "성주군": {"nx": 85, "ny": 91},
        "칠곡군": {"nx": 86, "ny": 93}, "예천군": {"nx": 86, "ny": 109}, "봉화군": {"nx": 90, "ny": 115},
        "울진군": {"nx": 102, "ny": 115}, "울릉군": {"nx": 127, "ny": 127},
    },
    "경상남도": {
        "_default": {"nx": 90, "ny": 77}, "창원시 의창구": {"nx": 90, "ny": 77}, "창원시 성산구": {"nx": 91, "ny": 77}, "창원시 마산합포구": {"nx": 89, "ny": 76},
        "창원시 마산회원구": {"nx": 89, "ny": 76}, "창원시 진해구": {"nx": 93, "ny": 75}, "진주시": {"nx": 82, "ny": 75},
        "통영시": {"nx": 88, "ny": 68}, "사천시": {"nx": 81, "ny": 71}, "김해시": {"nx": 95, "ny": 77},
        "밀양시": {"nx": 95, "ny": 82}, "거제시": {"nx": 90, "ny": 69}, "양산시": {"nx": 97, "ny": 80},
        "의령군": {"nx": 84, "ny": 79}, "함안군": {"nx": 86, "ny": 78}, "창녕군": {"nx": 89, "ny": 84},
        "고성군": {"nx": 86, "ny": 71}, "남해군": {"nx": 79, "ny": 67}, "하동군": {"nx": 76, "ny": 73},
        "산청군": {"nx": 78, "ny": 79}, "함양군": {"nx": 74, "ny": 82}, "거창군": {"nx": 78, "ny": 86},
        "합천군": {"nx": 82, "ny": 85},
    },
    "제주특별자치도": {
        "_default": {"nx": 53, "ny": 38}, "제주시": {"nx": 53, "ny": 38}, "서귀포시": {"nx": 53, "ny": 33}
    },
}

# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    kma_service_key = st.text_input("기상청 API 서비스 키", type="password")
    
    st.divider()

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 자세히 입력할수록 좋습니다.")

    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "sido": "서울특별시", "gungu": "(전체)", "gender": "여성", "age": "20대", "height": "", "weight": "",
            "style_preference": "캐주얼", "tpo": "일상", "personal_color": "모름"
        }

    with st.form("user_info_form"):
        st.subheader("개인 정보")
        
        # --- [수정됨] 2단계 지역 선택 UI ---
        sido_list = list(HIERARCHICAL_CITY_COORDS.keys())
        selected_sido = st.selectbox("시/도", sido_list, index=sido_list.index(st.session_state.user_info["sido"]))
        
        # 1. 구/군 리스트를 가져옵니다.
        gungu_list = [g for g in HIERARCHICAL_CITY_COORDS[selected_sido] if g != "_default"]
        # 2. 리스트를 가나다순으로 정렬합니다. (이 줄 추가)
        gungu_list.sort()

        gungu_options = ["(전체)"] + gungu_list


        # gungu_options = ["(전체)"] + [g for g in HIERARCHICAL_CITY_COORDS[selected_sido] if g != "_default"]
        selected_gungu = st.selectbox("구/군", gungu_options, index=gungu_options.index(st.session_state.user_info["gungu"]) if st.session_state.user_info["gungu"] in gungu_options else 0)

        st.session_state.user_info["sido"] = selected_sido
        st.session_state.user_info["gungu"] = selected_gungu
        
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        
        age_options = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대 이상"]
        st.session_state.user_info["age"] = st.selectbox("나이", age_options, index=age_options.index(st.session_state.user_info["age"]) if st.session_state.user_info["age"] in age_options else 1)
        
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

# --- [수정됨] 좌표를 직접 받는 API 함수 ---
def get_kma_weather_forecast(coords, service_key):
    if not service_key:
        return "오류: 기상청 서비스 키가 입력되지 않았습니다."

    nx, ny = coords["nx"], coords["ny"]
    # ... (이하 날씨 API 함수 로직은 동일)
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
            
            # --- [수정됨] 선택된 지역의 좌표를 결정하는 로직 ---
            sido = st.session_state.user_info["sido"]
            gungu = st.session_state.user_info["gungu"]
            
            if gungu == "(전체)":
                coords_to_use = HIERARCHICAL_CITY_COORDS[sido]["_default"]
                location_name = sido
            else:
                coords_to_use = HIERARCHICAL_CITY_COORDS[sido][gungu]
                location_name = f"{sido} {gungu}"

            weather_info = get_kma_weather_forecast(coords_to_use, kma_service_key)
            
            if "오류" in weather_info:
                st.error(weather_info)
                st.stop()
            
            user_info_text = (
                f"- 지역: {location_name}\n"
                f"- 성별: {st.session_state.user_info.get('gender')}\n- 나이: {st.session_state.user_info.get('age')}\n"
                f"- TPO: {st.session_state.user_info.get('tpo')}\n- 선호 스타일: {st.session_state.user_info.get('style_preference')}\n"
                f"- 퍼스널 컬러: {st.session_state.user_info.get('personal_color')}")
            
            system_prompt = f"""
            당신은 사용자의 개인 정보, TPO, 패션 취향, 퍼스널 컬러와 **내일 날씨**를 종합 분석하여 패션을 추천하는 전문 AI 스타일리스트입니다.

            **[답변 생성 규칙]**
            1.  **답변 시작**: 가장 먼저, 어떤 사용자의 정보를 바탕으로 추천하는지 핵심만 요약해서 알려주세요. 예를 들어, **"20대 여성, 캐주얼 스타일을 선호하시는 여름 쿨톤 사용자님을 위한 맞춤 패션 추천이에요! ✨"** 와 같이 상냥한 말투로 시작해주세요.
            2.  **내일 날씨 정보**: '내일 날씨 정보' 섹션을 만들어 전달받은 날씨 정보를 보여줍니다. 이 정보는 '**{location_name}**' 지역 기준입니다.
            3.  **패션 추천**: '패션 추천' 섹션에서 날씨, TPO, 퍼스널 컬러 등을 모두 고려하여 1~2가지의 완성된 착장을 제안합니다.
            4.  **스타일링 팁**: '스타일링 팁' 섹션에서 추가적인 팁을 제안합니다.
            5.  **우산 안내 (조건부)**: 만약 날씨 정보에 '**비 또는 눈 소식이 있습니다.**' 라는 내용이 포함되어 있다면, '우산 챙기세요! ☔️' 라는 섹션을 추가하고 "내일은 비나 눈이 올 수 있으니, 외출하실 때 작은 우산을 챙기는 걸 잊지 마세요!" 라고 상냥하게 알려주세요. 비 소식이 없다면 이 섹션은 만들지 않습니다.
            6.  **말투**: 모든 답변은 친절하고 전문적인 말투를 사용해주세요.
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
