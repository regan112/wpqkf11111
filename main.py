import streamlit as st
import random

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(
    page_title="당곡고 Up-Down-Pair 카드게임",
    page_icon="🃏",
    layout="centered"
)

# 2. 트럼프 카드 상수의 구성
SUITS = ['♠', '♥', '♦', '♣']
RANKS = [
    {'name': '2', 'value': 2}, {'name': '3', 'value': 3}, {'name': '4', 'value': 4},
    {'name': '5', 'value': 5}, {'name': '6', 'value': 6}, {'name': '7', 'value': 7},
    {'name': '8', 'value': 8}, {'name': '9', 'value': 9}, {'name': '10', 'value': 10},
    {'name': 'J', 'value': 11}, {'name': 'Q', 'value': 12}, {'name': 'K', 'value': 13},
    {'name': 'A', 'value': 14}
]

# 3. 덱 생성 및 셔플 함수
def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({
                "suit": suit,
                "name": rank['name'],
                "value": rank['value']
            })
    random.shuffle(deck)
    return deck

# 4. 세션 상태(Session State) 초기화 (스트림릿의 상태 유지 메커니즘)
if 'balance' not in st.session_state:
    st.session_state.balance = 10000  # 기본 자금 설정
if 'deck' not in st.session_state:
    st.session_state.deck = create_deck()
if 'current_card' not in st.session_state:
    st.session_state.current_card = st.session_state.deck.pop()
if 'next_card' not in st.session_state:
    st.session_state.next_card = None
if 'game_stage' not in st.session_state:
    st.session_state.game_stage = "betting"  # "betting" 또는 "result"
if 'last_result' not in st.session_state:
    st.session_state.last_result = {}
if 'history' not in st.session_state:
    st.session_state.history = []
if 'bet_preset' not in st.session_state:
    st.session_state.bet_preset = 1000

# 5. 실시간 확률 기반 유동 배율 계산 알고리즘 (수학적 탐구 요소)
def calculate_odds():
    cur_val = st.session_state.current_card['value']
    deck = st.session_state.deck
    total = len(deck)
    
    if total == 0:
        return 0.0, 0.0, 0.0

    # 남은 카드 수 카운팅
    up_count = sum(1 for c in deck if c['value'] > cur_val)
    down_count = sum(1 for c in deck if c['value'] < cur_val)
    pair_count = sum(1 for c in deck if c['value'] == cur_val)

    # 하우스 마진(수수료) 4%를 적용한 공정 배율 계산 공식: (1 - 0.04) / 확률
    margin = 0.96
    odds_up = round(margin / (up_count / total), 2) if up_count > 0 else 0.0
    odds_down = round(margin / (down_count / total), 2) if down_count > 0 else 0.0
    odds_pair = round(margin / (pair_count / total), 2) if pair_count > 0 else 0.0

    return odds_up, odds_down, odds_pair

# 6. 카드 그래픽 렌더링 함수 (HTML/CSS 스타일링)
def render_card(card, title="카드"):
    if not card:
        # 카드 뒷면 디자인
        return f"""
        <div style="text-align: center;">
            <div style="color: #666; margin-bottom: 5px; font-weight: bold;">{title}</div>
            <div style="
                width: 130px; 
                height: 190px; 
                background: linear-gradient(135deg, #1e3799, #0c2461); 
                border: 3px solid white; 
                border-radius: 10px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
                margin: 0 auto;
            ">
                <span style="font-size: 36px; color: white;">🃏</span>
            </div>
        </div>
        """
    
    # 빨간색/검은색 무늬 구분
    color = "#eb2f06" if card['suit'] in ['♥', '♦'] else "#1e272e"
    return f"""
    <div style="text-align: center;">
        <div style="color: #444; margin-bottom: 5px; font-weight: bold;">{title}</div>
        <div style="
            width: 130px; 
            height: 190px; 
            background: white; 
            border: 2px solid #ddd; 
            border-radius: 10px; 
            display: flex; 
            flex-direction: column; 
            justify-content: space-between; 
            padding: 12px; 
            box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
            color: {color};
            margin: 0 auto;
        ">
            <div style="text-align: left; font-size: 20px; font-weight: bold; line-height: 1;">
                {card['name']}<br>{card['suit']}
            </div>
            <div style="text-align: center; font-size: 50px;">
                {card['suit']}
            </div>
            <div style="text-align: right; font-size: 20px; font-weight: bold; line-height: 1; transform: rotate(180deg);">
                {card['name']}<br>{card['suit']}
            </div>
        </div>
    </div>
    """

# --- 게임 내부 로직 처리 함수 ---
def play_turn(choice, bet_amount, odds):
    if len(st.session_state.deck) == 0:
        st.session_state.deck = create_deck()
        
    next_card = st.session_state.deck.pop()
    st.session_state.next_card = next_card
    st.session_state.balance -= bet_amount

    cur_val = st.session_state.current_card['value']
    nxt_val = next_card['value']

    if nxt_val > cur_val:
        actual = "UP"
    elif nxt_val < cur_val:
        actual = "DOWN"
    else:
        actual = "PAIR"

    win = (choice == actual)
    multiplier = odds[choice]

    if win:
        winnings = int(bet_amount * multiplier)
        st.session_state.balance += winnings
        result_msg = f"🎉 예측 성공! **{winnings:,} G**를 획득했습니다! ({multiplier}배)"
        is_success = True
    else:
        winnings = 0
        result_msg = f"😢 예측 실패... **{bet_amount:,} G**를 잃었습니다."
        is_success = False

    # 결과 기록 저장
    st.session_state.last_result = {
        "is_success": is_success,
        "msg": result_msg,
        "choice": choice,
        "actual": actual,
        "bet": bet_amount,
        "prev_card": st.session_state.current_card,
        "next_card": next_card
    }

    st.session_state.history.insert(0, {
        "round": f"{st.session_state.current_card['suit']}{st.session_state.current_card['name']} ➔ {next_card['suit']}{next_card['name']}",
        "choice": choice,
        "actual": actual,
        "bet": f"{bet_amount:,} G",
        "profit": f"+{winnings:,} G" if win else f"-{bet_amount:,} G",
        "win": win
    })

    st.session_state.game_stage = "result"

def next_round():
    st.session_state.current_card = st.session_state.next_card
    st.session_state.next_card = None
    st.session_state.game_stage = "betting"

def reset_game():
    st.session_state.balance = 10000
    st.session_state.deck = create_deck()
    st.session_state.current_card = st.session_state.deck.pop()
    st.session_state.next_card = None
    st.session_state.game_stage = "betting"
    st.session_state.last_result = {}
    st.session_state.history = []

# --- 7. 화면 UI 배치 시작 ---
st.title("🃏 실시간 확률형 Up-Down-Pair 게임")
st.caption("당곡고등학교 웹 앱 프로그래밍 실습 예제")

# 대시보드 레이아웃
col_bal, col_deck = st.columns(2)
with col_bal:
    st.metric(label="💰 나의 현재 자금", value=f"{st.session_state.balance:,} G")
with col_deck:
    st.metric(label="🎴 덱에 남은 카드", value=f"{len(st.session_state.deck)} 장")

st.markdown("---")

# 실시간 배율 계산
odds_up, odds_down, odds_pair = calculate_odds()
odds_dict = {"UP": odds_up, "DOWN": odds_down, "PAIR": odds_pair}

# 카드 레이아웃 배치
col_card1, col_card2 = st.columns(2)
with col_card1:
    st.markdown(render_card(st.session_state.current_card, "기준 카드 (오픈됨)"), unsafe_allow_html=True)
with col_card2:
    st.markdown(render_card(st.session_state.next_card, "새로 뽑을 카드"), unsafe_allow_html=True)

st.write("")

# 8. 게임 플레이 단계 분기 처리
if st.session_state.game_stage == "betting":
    
    # 베팅 자금 설정 영역
    st.subheader("💳 베팅 설정")
    bet_amount = st.number_input(
        "거실 판돈을 입력하세요 (최소 100 G)", 
        min_value=100, 
        max_value=max(100, st.session_state.balance), 
        value=min(st.session_state.bet_preset, st.session_state.balance),
        step=100
    )
    st.session_state.bet_preset = bet_amount

    # 베팅 단축 버튼
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        if st.button("최소 (100 G)"):
            st.session_state.bet_preset = 100
            st.rerun()
    with col_p2:
        if st.button("절반 (1/2)"):
            st.session_state.bet_preset = max(100, st.session_state.balance // 2)
            st.rerun()
    with col_p3:
        if st.button("2배"):
            st.session_state.bet_preset = min(st.session_state.balance, bet_amount * 2)
            st.rerun()
    with col_p4:
        if st.button("올인 💥"):
            st.session_state.bet_preset = st.session_state.balance
            st.rerun()

    st.markdown("---")
    st.subheader("🎯 예측 선택하기")
    
    # 3가지 행동 버튼 (UP, PAIR, DOWN)
    col_up, col_pair, col_down = st.columns(3)
    
    with col_up:
        is_up_disabled = (odds_up == 0.0) or (st.session_state.balance < bet_amount)
        label_up = f"UP ▲ ({odds_up}배)" if odds_up > 0 else "UP (불가능)"
        if st.button(label_up, use_container_width=True, type="primary", disabled=is_up_disabled):
            play_turn("UP", bet_amount, odds_dict)
            st.rerun()
            
    with col_pair:
        is_pair_disabled = (odds_pair == 0.0) or (st.session_state.balance < bet_amount)
        label_pair = f"PAIR ＝ ({odds_pair}배)" if odds_pair > 0 else "PAIR (불가능)"
        if st.button(label_pair, use_container_width=True, disabled=is_pair_disabled):
            play_turn("PAIR", bet_amount, odds_dict)
            st.rerun()
            
    with col_down:
        is_down_disabled = (odds_down == 0.0) or (st.session_state.balance < bet_amount)
        label_down = f"DOWN ▼ ({odds_down}배)" if odds_down > 0 else "DOWN (불가능)"
        if st.button(label_down, use_container_width=True, type="primary", disabled=is_down_disabled):
            play_turn("DOWN", bet_amount, odds_dict)
            st.rerun()

elif st.session_state.game_stage == "result":
    # 결과 화면 출력
    res = st.session_state.last_result
    st.markdown("---")
    
    if res["is_success"]:
        st.success(res["msg"])
    else:
        st.error(res["msg"])
        
    if st.button("다음 라운드 진행 ➔", use_container_width=True, type="primary"):
        next_round()
        st.rerun()

# 9. 파산 구제 시스템 및 초기화 버튼
st.markdown("---")
if st.session_state.balance < 100 and st.session_state.game_stage == "betting":
    st.warning("⚠️ 자금이 부족하여 베팅할 수 없습니다!")
    if st.button("💸 무료 자금 수령하기 (10,000 G)", use_container_width=True):
        st.session_state.balance = 10000
        st.rerun()

# 10. 기록(History) 및 리셋 버튼 배치
col_foot1, col_foot2 = st.columns([4, 1])
with col_foot1:
    with st.expander("📝 최근 게임 기록 보기"):
        if st.session_state.history:
            st.table(st.session_state.history)
        else:
            st.write("진행한 라운드가 아직 없습니다.")
with col_foot2:
    if st.button("🔄 게임 리셋", use_container_width=True):
        reset_game()
        st.rerun()
