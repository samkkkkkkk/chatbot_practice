import streamlit as st
from openai import OpenAI
from datetime import datetime

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="AI 패션 스타일리스트", page_icon="👗")

# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 자세히 입력할수록 좋습니다.")
    
    # 세션 상태 초기화 (스타일 정보 및 퍼스널 컬러 추가)
    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "gender": "여성",
            "age": "20대",
            "height": "",
            "weight": "",
            "style_preference": "캐주얼",
            "tpo": "일상",
            "preferred_color": "",
            "personal_color": "모름" # --- 추가된 부분: 퍼스널 컬러 ---
        }

    with st.form("user_info_form"):
        # --- 개인 정보 섹션 ---
        st.subheader("개인 정보")
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        st.session_state.user_info["age"] = st.text_input("나이 (예: 20대, 30대)", value=st.session_state.user_info["age"])
        st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info["height"])
        st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info["weight"])

        st.divider()

        # --- 스타일 정보 섹션 ---
        st.subheader("스타일 정보")
        st.write("더욱 만족스러운 추천을 받아보세요!")
        st.session_state.user_info["style_preference"] = st.selectbox(
            "선호하는 스타일",
            ["캐주얼", "미니멀", "스트릿", "포멀", "빈티지", "스포티"],
            index=["캐주얼", "미니멀", "스트릿", "포멀", "빈티지", "스포티"].index(st.session_state.user_info["style_preference"])
        )
        st.session_state.user_info["tpo"] = st.text_input("TPO (시간, 장소, 상황)", placeholder="예: 주말 데이트, 중요한 회의", value=st.session_state.user_info["tpo"])
        st.session_state.user_info["preferred_color"] = st.text_input("선호/기피 색상", placeholder="예: 파란색 선호, 노란색 기피", value=st.session_state.user_info["preferred_color"])
        
        # --- 추가된 부분: 퍼스널 컬러 입력 필드 ---
        st.session_state.user_info["personal_color"] = st.selectbox(
            "퍼스널 컬러",
            ["모름", "봄 웜톤 (Spring Warm)", "여름 쿨톤 (Summer Cool)", "가을 웜톤 (Autumn Warm)", "겨울 쿨톤 (Winter Cool)"],
            index=["모름", "봄 웜톤 (Spring Warm)", "여름 쿨톤 (Summer Cool)", "가을 웜톤 (Autumn Warm)", "겨울 쿨톤 (Winter Cool)"].index(st.session_state.user_info["personal_color"])
        )

        submitted = st.form_submit_button("정보 저장")
        if submitted:
            st.success("정보가 저장되었습니다!")


# --- 헬퍼 함수: 현재 계절 판단 ---
def get_current_season():
    month = datetime.now().month
    if month in [3, 4, 5]: return "봄"
    elif month in [6, 7, 8]: return "여름"
    elif month in [9, 10, 11]: return "가을"
    else: return "겨울"


# --- 메인 챗봇 화면 ---
st.title("👗 AI 패션 스타일리스트")
st.write("당신의 계절과 스타일에 딱 맞는 패션을 추천해드립니다.")

st.subheader("어떤 추천을 원하세요? 👇")
example_questions = ["오늘 뭐 입지? 👕", "주말 데이트룩 추천 💖", "소개팅룩 추천해줘 ✨"]
cols = st.columns(len(example_questions))

prompt = None
for i, question in enumerate(example_questions):
    if cols[i].button(question, use_container_width=True):
        prompt = question
        # 버튼 클릭 시 해당 TPO를 사이드바에 자동 반영 (기존 로직 유지)
        if "데이트" in question: st.session_state.user_info["tpo"] = "주말 데이트"
        elif "소개팅" in question: st.session_state.user_info["tpo"] = "소개팅"
        else: st.session_state.user_info["tpo"] = "일상"


chat_input = st.chat_input("메시지를 입력하세요...")
if chat_input:
    prompt = chat_input


if not openai_api_key:
    st.info("사이드바에서 OpenAI API 키를 입력해주세요.")
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
        with st.spinner("당신만을 위한 스타일을 추천하는 중..."):
            
            # 사용자 정보 정리 (퍼스널 컬러 포함)
            user_info_text = (
                f"- 성별: {st.session_state.user_info.get('gender') or '정보 없음'}\n"
                f"- 나이: {st.session_state.user_info.get('age') or '정보 없음'}\n"
                f"- 선호 스타일: {st.session_state.user_info.get('style_preference') or '정보 없음'}\n"
                f"- TPO: {st.session_state.user_info.get('tpo') or '정보 없음'}\n"
            )
            if st.session_state.user_info.get('height'):
                user_info_text += f"- 키: {st.session_state.user_info.get('height')}cm\n"
            if st.session_state.user_info.get('weight'):
                user_info_text += f"- 몸무게: {st.session_state.user_info.get('weight')}kg\n"
            if st.session_state.user_info.get('preferred_color'):
                user_info_text += f"- 선호/기피 색상: {st.session_state.user_info.get('preferred_color')}\n"
            # --- 추가된 부분: 퍼스널 컬러 정보 포함 ---
            if st.session_state.user_info.get('personal_color') and st.session_state.user_info['personal_color'] != '모름':
                user_info_text += f"- 퍼스널 컬러: {st.session_state.user_info.get('personal_color')}\n"

            # 시스템 프롬프트 수정 (퍼스널 컬러 고려 지시 추가)
            system_prompt = f"""
            당신은 사용자의 개인 정보, TPO(시간, 장소, 상황), 패션 취향, 그리고 **퍼스널 컬러**를 깊이 이해하고 분석하여 현재 계절에 맞는 패션을 추천하는 전문 AI 스타일리스트입니다.

            1.  주어진 '현재 계절', '사용자 정보', 특히 **퍼스널 컬러**를 최우선으로 고려합니다. 퍼스널 컬러에 맞는 색상 조합을 적극적으로 제안해주세요.
            2.  '패션 추천' 섹션에서 사용자의 TPO와 선호 스타일에 맞춰, 상의, 하의, 겉옷, 액세서리 등을 조합하여 1~2가지의 완성된 착장을 제안합니다. 각 착장의 스타일과 분위기를 설명해주세요.
            3.  '스타일링 팁' 섹션에서 추천한 옷을 더 잘 소화할 수 있는 팁이나, 다른 아이템과 조합하는 방법을 추가로 제안합니다.
            4.  모든 답변은 매우 친절하고, 전문적이며, 사용자의 자신감을 북돋아 주는 긍정적인 말투를 사용해주세요.
            """
            
            # 현재 계절 정보 가져오기
            current_season = get_current_season()
            
            # 최종 프롬프트 구성
            final_prompt = f"""
            현재 계절과 아래 사용자 정보를 바탕으로, 요청에 맞는 패션 스타일을 추천해줘.

            [현재 계절]
            {current_season}

            [사용자 정보]
            {user_info_text}

            [사용자 요청]
            {prompt}
            """
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": final_prompt}
                    ],
                    stream=True,
                )
                
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
