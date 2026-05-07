import streamlit as st
import pandas as pd
from datetime import date
import random

# =========================
# 페이지 설정

st.set_page_config(
    page_title="냉장고 레시피 추천",
    page_icon="🍳",
    layout="centered"
)

# =========================
# CSV 불러오기

@st.cache_data
def load_data():
    return pd.read_csv("recipes.csv")

df = load_data()

# =========================
# 모든 재료 추출

all_ingredients = set()

for _, row in df.iterrows():

    ingredients = row["ingredients"].split(",")

    for ingredient in ingredients:

        all_ingredients.add(
            ingredient.strip()
        )

all_ingredients = sorted(
    list(all_ingredients)
)

# =========================
# session_state 생성

if "fridge" not in st.session_state:

    st.session_state.fridge = []

# =========================
# 제목

st.title("🍳 냉장고 레시피 추천")

st.write(
    "냉장고 재료와 유통기한을 기반으로 "
    "음식을 추천합니다."
)

st.divider()

# =========================
# 재료 추가

st.subheader("재료 추가")

selected_ingredient = st.selectbox(
    "재료 선택",
    all_ingredients
)

expire_date = st.date_input(
    "유통기한",
    min_value=date.today()
)

if st.button("냉장고에 추가"):

    st.session_state.fridge.append({

        "name": selected_ingredient,
        "expire": expire_date

    })

    st.success(
        f"{selected_ingredient} 추가 완료!"
    )

st.divider()

# =========================
# 냉장고 초기화 버튼

if st.button("🗑️ 냉장고 초기화"):

    st.session_state.fridge = []

    st.success(
        "냉장고가 초기화되었습니다!"
    )

    st.rerun()

st.divider()

# =========================
# 현재 냉장고

st.subheader("현재 냉장고")

if len(st.session_state.fridge) == 0:

    st.info(
        "추가된 재료가 없습니다."
    )

else:

    # 임박 재료 개수
    urgent_count = 0

    for item in st.session_state.fridge:

        days_left = (
            item["expire"] - date.today()
        ).days

        if days_left <= 3:

            urgent_count += 1

    # 경고
    if urgent_count > 0:

        st.error(
            f"⚠️ 유통기한이 임박한 재료가 "
            f"{urgent_count}개 있습니다!"
        )

    # 유통기한 순 정렬
    sorted_fridge = sorted(
        st.session_state.fridge,
        key=lambda x: x["expire"]
    )

    remove_index = None

    for idx, item in enumerate(
        sorted_fridge
    ):

        days_left = (
            item["expire"] - date.today()
        ).days

        col1, col2 = st.columns([4, 1])

        with col1:

            # 빨간색 표시
            if days_left <= 3:

                st.markdown(
                    f"""
                    <span style="color:red;">
                    🍱 {item['name']}
                    ({days_left}일 남음)
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.write(
                    f"🍱 {item['name']} "
                    f"({days_left}일 남음)"
                )

        with col2:

            if st.button(
                "삭제",
                key=f"delete_{idx}"
            ):

                for original_idx, original_item in enumerate(
                    st.session_state.fridge
                ):

                    if original_item == item:

                        remove_index = original_idx
                        break

    if remove_index is not None:

        st.session_state.fridge.pop(
            remove_index
        )

        st.rerun()

st.divider()

# =========================
# 추천 옵션

st.subheader("추천 옵션")

easy_only = st.checkbox(
    "쉬운 요리만 보기"
)

fast_only = st.checkbox(
    "10분 이하 요리만 보기"
)

st.divider()

# =========================
# 랜덤 추천

st.subheader("🎲 랜덤 음식 추천")

if st.button("오늘 뭐 먹지?"):

    random_row = df.sample(1).iloc[0]

    st.success(
        f"오늘의 추천 음식은 "
        f"{random_row['name']} 입니다!"
    )

    st.write(
        f"난이도: "
        f"{random_row['difficulty']}"
    )

    st.write(
        f"조리시간: "
        f"{random_row['time']}"
    )

st.divider()

# =========================
# 음식 추천

if st.button("음식 추천받기"):

    fridge_ingredients = [

        item["name"].replace(
            " ",
            ""
        )

        for item in st.session_state.fridge
    ]

    urgent_ingredients = []

    for item in st.session_state.fridge:

        days_left = (
            item["expire"]
            - date.today()
        ).days

        if days_left <= 3:

            urgent_ingredients.append(

                item["name"].replace(
                    " ",
                    ""
                )
            )

    results = []

    # =========================
    # 레시피 비교

    for _, row in df.iterrows():

        recipe_ingredients = [

            ingredient.strip().replace(
                " ",
                ""
            )

            for ingredient in row[
                "ingredients"
            ].split(",")
        ]

        # 난이도 필터
        if (
            easy_only
            and row["difficulty"]
            != "쉬움"
        ):
            continue

        # 시간 필터
        cooking_time = int(
            row["time"].replace(
                "분",
                ""
            )
        )

        if (
            fast_only
            and cooking_time > 10
        ):
            continue

        match_count = 0
        urgent_match = []
        missing = []

        for ingredient in recipe_ingredients:

            if ingredient in fridge_ingredients:

                match_count += 1

                if ingredient in urgent_ingredients:

                    urgent_match.append(
                        ingredient
                    )

            else:

                missing.append(
                    ingredient
                )

        # 점수 계산
        score = (
            (
                match_count
                / len(recipe_ingredients)
            ) * 70
            + len(urgent_match) * 15
        )

        # 추천 이유
        if len(urgent_match) > 0:

            reason = (
                f"유통기한 임박 재료인 "
                f"{', '.join(urgent_match)}"
                f"를 활용할 수 있어요."
            )

        else:

            reason = (
                f"보유 재료가 "
                f"{match_count}개 포함되어 있어요."
            )

        # 추천 등급
        if score >= 80:

            badge = "🔥 매우 추천"

        elif score >= 50:

            badge = "👍 추천"

        else:

            badge = "🙂 가능"

        results.append({

            "name": row["name"],
            "match": match_count,
            "total": len(
                recipe_ingredients
            ),
            "difficulty": row[
                "difficulty"
            ],
            "time": row["time"],
            "score": score,
            "reason": reason,
            "missing": missing,
            "badge": badge

        })

    # =========================
    # 점수순 정렬

    results = sorted(

        results,
        key=lambda x: x["score"],
        reverse=True

    )

    st.subheader("추천 결과")

    if len(results) == 0:

        st.warning(
            "조건에 맞는 음식이 없습니다."
        )

    else:

        for food in results:

            if food["match"] > 0:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### 🍳 "
                        f"{food['name']}"
                    )

                    st.write(
                        food["badge"]
                    )

                    st.write(
                        f"재료 일치: "
                        f"{food['match']} / "
                        f"{food['total']}"
                    )

                    st.write(
                        f"난이도: "
                        f"{food['difficulty']}"
                    )

                    st.write(
                        f"조리시간: "
                        f"{food['time']}"
                    )

                    st.info(
                        food["reason"]
                    )

                    # 부족한 재료 표시
                    if len(food["missing"]) > 0:

                        st.warning(
                            "부족한 재료: "
                            + ", ".join(
                                food["missing"]
                            )
                        )

                    progress = min(
                        food["score"] / 100,
                        1.0
                    )

                    st.progress(
                        progress
                    )