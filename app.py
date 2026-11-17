from google import genai
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="상황 맞춤형 챗봇", page_icon="🎭")

st.title("🎭 나만의 상황극 챗봇 메이커")
st.markdown("원하는 **상황과 페르소나**를 설정하고 AI와 대화를 시작해보세요!")

# 사이드바: 상황 설정 영역
with st.sidebar:
  st.header("⚙️ 챗봇 설정")
  api_key = st.text_input(
      "Gemini API Key를 입력하세요", type="password"
  )

  default_situation = (
      "너는 지금 좀비 바이러스가 퍼진 도시의 버려진 마트 안에서 홀로 버티고"
      " 있는 생존자야. 조금 예민하고 경계심이 많지만, 동료가 생기면"
      " 의지하려고 해."
  )

  situation_input = st.text_area(
      "AI의 상황 및 성격을 설정하세요 (System Prompt)",
      value=default_situation,
      height=150,
  )

  apply_btn = st.button("설정 적용 및 대화 초기화")

if not api_key:
  st.warning(
      "👈 사이드바에 Google Gemini API Key를 입력해주세요! (구글 AI Studio에서"
      " 무료로 발급 가능합니다)"
  )
  st.stop()

# 클라이언트 저장
if (
    "client" not in st.session_state
    or "current_api_key" not in st.session_state
    or st.session_state.current_api_key != api_key
):
  st.session_state.client = genai.Client(api_key=api_key)
  st.session_state.current_api_key = api_key
  st.session_state.chat_session = None

if (
    "chat_session" not in st.session_state
    or st.session_state.chat_session is None
    or apply_btn
):
  config = {"system_instruction": situation_input}
  st.session_state.chat_session = st.session_state.client.chats.create(
      model="gemini-3.8-flash", config=config
  )
  st.session_state.messages = []
  st.success("새로운 상황이 적용되었습니다! 아래에서 대화를 시작해보세요.")

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if user_prompt := st.chat_input(
    "상황에 맞는 말을 건네보세요... (예: 저기요, 안에 누구 없어요?)"
):
  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.markdown(user_prompt)

  try:
    with st.chat_message("assistant"):
      with st.spinner("생각 중..."):
        # [오류 해결] 안정적인 일반 전송 방식으로 변경
        response = st.session_state.chat_session.send_message(user_prompt)
        ai_response = response.text
        st.markdown(ai_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": ai_response}
    )
  except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")