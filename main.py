import streamlit as st
import random
import time

# 1. 페이지 설정
st.set_page_config(
    page_title="당곡고 바카라 & 정직한 광산",
    page_icon="🃏",
    layout="centered"
)

# 2. 바카라 카드 정보 정의 (10, J, Q, K는 바카라 규칙상 0점)
SUITS = ['♠', '♥', '♦', '♣']
RANKS = [
    {'name': 'A', 'bacc_val': 1},
    {'name': '2', 'bacc_val': 2}, {'name': '3', 'bacc_val': 3}, {'name': '4', 'bacc_val': 4},
    {'name': '5', 'bacc_val': 5}, {'name': '6', 'bacc_val': 6}, {'name': '7', 'bacc_val': 7},
    {'name': '8', 'bacc_val': 8}, {'name': '9', 'bacc_val': 9},
    {'name': '10', 'bacc_val': 0}, {'name': 'J', 'bacc_val': 0}, {'name': 'Q', 'bacc_val': 0}, {'name': 'K', 'bacc_val': 0}
]

# 3. 덱 생성 및 셔플
def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({
                "suit": suit,
                "name": rank['name'],
                "bacc_val": rank['bacc_val']
            })
    random.shuffle(deck)
    return deck

# 4. 세션 상태(Session State) 초기화
if 'balance' not in st.session_state:
    st.session_state.balance = 10000  # 시작 금액
if 'deck' not in st.session_state:
    st.session_state.deck = create_deck()
if 'cheated' not in st.session_state:
    st.session_state.cheated = False  # 치트 감지 여부
if 'click_violation_count' not in st.session_state:
    st.session_state.click_violation_count = 0  # 빠른 클릭 의심 누적 수
if 'last_click_time' not in st.session_state:
    st.session_state.last_click_time = 0.0
if 'game_history' not in st.session_state:
    st.session_state.game_history = []

# --- 바카라 규칙 연산 엔진 ---
# 바카라는 플레이어(Player)와 뱅커(Banker)의 카드 합 끝자리가 9에 가까운 쪽이 이기는 게임입니다.
def calculate_score(hand):
    return sum(card['bacc_val'] for card in hand) % 10

def play_baccarat(bet_type, bet_amount):
    # 덱이 부족하면 다시 채웁니다.
    if len(st.session_state.deck) < 10:
        st.session_state.deck = create_deck()

    deck = st.session_state.deck

    # 1단계: 각각 두 장씩 카드를 받습니다.
    p_hand = [deck.pop(), deck.pop()]
    b_hand = [deck.pop(), deck.pop()]

    p_score = calculate_score(p_hand)
    b_score = calculate_score(b_hand)

    p_third = None
    b_third = None

    # 내추럴(Natural) 규칙: 누군가 처음 2장의 합이 8 또는 9이면 즉시 게임 종료
