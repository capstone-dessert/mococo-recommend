import random
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from utils.util import get_all_clothes

router = APIRouter()


class RecommendationRequest(BaseModel):
    min_temperature: int
    max_temperature: int
    schedule: str


class RecommendationResponse(BaseModel):
    ids: List[int]


style_compatibility = {
    "캐주얼": ["스트릿", "댄디", "스포티", "페미닌"],
    "스트릿": ["캐주얼", "스포티"],
    "댄디": ["캐주얼", "포멀"],
    "스포티": ["캐주얼", "스트릿"],
    "페미닌": ["캐주얼"],
    "포멀": ["댄디"],
}

# 색상 보색 정의
complementary_color = {
    "빨강": ["파랑", "보라", "카키", "초록", "민트"],
    "핑크": ["네이비", "하늘", "카키", "초록", "노랑", "주황"],
    "네이비": ["핑크", "노랑", "주황"],
    "파랑": ["빨강", "노랑", "주황"],
    "하늘": ["핑크", "초록", "노랑", "주황"],
    "보라": ["빨강", "카키", "초록", "노랑"],
    "카키": ["빨강", "핑크", "보라", "하늘", "노랑", "주황"],
    "초록": ["빨강", "핑크", "카키", "하늘", "노랑"],
    "민트": ["빨강", "노랑", "주황"],
    "노랑": ["핑크", "파랑", "네이비", "하늘", "보라", "카키", "초록", "민트"],
    "주황": ["핑크", "파랑", "네이비", "하늘", "카키", "노랑"],
}


def filter_by_weather(clothes_list, min_temp=None, max_temp=None):
    filtered_clothes = list(clothes_list)
    if min_temp is not None and max_temp is not None:
        if min_temp >= 10:
            filtered_clothes = [item for item in filtered_clothes if
                                item["subcategory"] not in ["코트", "패딩", "점퍼", "무스탕"]]
            if min_temp >= 15:
                filtered_clothes = [item for item in filtered_clothes if
                                    item["subcategory"] not in ["후드 티셔츠", "맨투맨", "니트"]]
                if min_temp >= 20:
                    filtered_clothes = [item for item in filtered_clothes if item["category"] != ["아우터"]]

        if max_temp <= 23:
            filtered_clothes = [item for item in filtered_clothes if item["subcategory"] != "민소매 티셔츠"]
            if max_temp <= 10:
                filtered_clothes = [item for item in filtered_clothes if not (
                        (item["category"] == "상의" and item["subcategory"] in ["민소매 티셔츠", "반소매 티셔츠"]) or
                        (item["category"] == "하의" and item["subcategory"] == "반바지")
                )]

    return filtered_clothes


def filter_by_occasion(clothes_list, occasion=None):
    filtered_clothes = list(clothes_list)
    if occasion is not None:
        if occasion in ["결혼", "면접", "출근"]:
            filtered_clothes = [item for item in filtered_clothes if
                                item["subcategory"] not in ["민소매 티셔츠", "후드 티셔츠", "스포츠 상의", "반바지", "트레이닝팬츠", "레깅스"]]
        elif occasion == "발표":
            filtered_clothes = [item for item in filtered_clothes if
                                item["subcategory"] not in ["민소매 티셔츠", "후드 티셔츠", "반바지", "트레이닝팬츠", "레깅스"]]
        elif occasion == "운동":
            filtered_clothes = [item for item in filtered_clothes if item["subcategory"] not in ["셔츠/블라우스", "니트", "슬랙스",
                                                                                                 "치마"] and item[
                                    "category"] != "원피스"]
    return filtered_clothes


def filter_clothes(clothes_list, min_temp=None, max_temp=None, occasion=None):
    weather_filtered_clothes = filter_by_weather(clothes_list, min_temp, max_temp)

    final_filtered_clothes = filter_by_occasion(weather_filtered_clothes, occasion)

    return final_filtered_clothes


def get_random_parent_item(clothes_list):
    parent_items = [item for item in clothes_list if item["category"] in ["상의", "하의", "원피스"]]
    if parent_items:
        return random.choice(parent_items)
    return None


def get_child_items(clothes_list, parent_item, max_temperature):
    if not parent_item:
        return []

    child_items = []
    all_primary_categories = {item["category"] for item in clothes_list}
    all_primary_categories.discard(parent_item["category"])  # 중복 제거

    primary_categories = list(all_primary_categories)

    if parent_item["category"] == "원피스":
        primary_categories = [category for category in primary_categories if category not in ["상의", "하의"]]
    elif parent_item["category"] == "상의":
        primary_categories = ["하의"]
    elif parent_item["category"] == "하의":
        primary_categories = ["상의"]

    parent_colors = parent_item["colors"] if parent_item["colors"] else []

    category_total_scores = {}

    for item in clothes_list:
        if item["category"] in primary_categories:
            style_score = 0
            for parent_style in parent_item["styles"]:
                for style in item["styles"]:
                    if parent_style == style:
                        style_score += 15
                    elif style in style_compatibility.get(parent_style, []):
                        style_score += 5
                    else:
                        style_score -= 5

            if any(parent_color in complementary_color and item_color in complementary_color[parent_color]
                   for parent_color in parent_colors for item_color in item["colors"]):
                color_score = -5  # 부모와 자식의 보색인 경우 점수를 낮게 함
            elif any(parent_color == item_color for parent_color in parent_colors for item_color in item["colors"] if
                     parent_color != '블랙'):
                color_score = -5  # 부모와 같은 색상인 경우 (블랙 제외) 점수를 낮게 함
            else:
                color_score = 0

            total_score = style_score + color_score + 10  # 기본 점수 10 추가

            item['score'] = total_score

            category_total_scores.setdefault(item["category"], 0)
            category_total_scores[item["category"]] += total_score

    for category in primary_categories:
        category_items = [item for item in clothes_list if item['category'] == category]
        if category_items:
            random_value = random.random() * 0.3  # 0부터 0.3 사이의 랜덤 실수 값 생성
            selected_item = None
            for item in category_items:
                item_score = item['score']
                item_probability = item_score / category_total_scores[category]  # 아이템 선택 확률 계산
                if random_value < item_probability:
                    selected_item = item
                    break

            if selected_item:
                child_items.append(selected_item)
                if max_temperature is not None and 10 <= max_temperature <= 23 and (
                        parent_item["subcategory"] == "반소매 티셔츠" or selected_item["subcategory"] == "반소매 티셔츠"):
                    outerwear_items = [item for item in clothes_list if item["category"] == "아우터"]
                    if outerwear_items and not any(item["category"] == "아우터" for item in child_items):
                        outerwear_total_score = sum(outer['score'] for outer in outerwear_items)
                        outer_random_value = random.random() * 0.3  # 0부터 0.3 사이의 랜덤 실수 값 생성
                        outer_added = False
                        for outerwear in outerwear_items:
                            if outerwear not in child_items:
                                outer_score = outerwear['score']
                                outer_probability = outer_score / outerwear_total_score
                                if outer_random_value < outer_probability:
                                    child_items.append(outerwear)
                                    outer_added = True
                                    break
                        if not outer_added:
                            highest_score_outerwear = max(outerwear_items, key=lambda x: x['score'])
                            if highest_score_outerwear not in child_items:
                                child_items.append(highest_score_outerwear)
            else:
                # 선택되지 않은 경우, 해당 카테고리 내에서 가장 높은 점수를 가진 아이템 선택
                highest_score_item = max(category_items, key=lambda x: x['score'])
                child_items.append(highest_score_item)

    return child_items


def generate_recommendation(request):
    min_temperature = request.min_temperature
    max_temperature = request.max_temperature
    schedule = request.schedule

    clothes = get_all_clothes()

    # 날씨, 약속 종류 필터링
    filtered_clothes = filter_clothes(clothes, min_temperature, max_temperature, schedule)

    # 부모 아이템 선택
    parent_item = get_random_parent_item(filtered_clothes)

    # 자식 아이템 선택
    child_items = get_child_items(filtered_clothes, parent_item, max_temperature)

    # 코디 추천
    recommended_outfit = []
    if parent_item:
        recommended_outfit.append(parent_item["id"])

    for child_item in child_items:
        recommended_outfit.append(child_item["id"])

    return recommended_outfit


@router.post("/recommend")
async def recommend(request: RecommendationRequest):
    recommendation = generate_recommendation(request)

    return {"ids": recommendation}
