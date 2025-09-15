from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import List
from app.models.stepik import *
from app.services import encoder, qdrant, run_blocking
from qdrant_client import models

import logging
import random

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["stepik"])

w1 = 20
w2 = 0
w3 = 1
w4 = 0
w5 = 1


class SliderData(BaseModel):
    sliderId: str
    value: int

@router.post("/update-weights")
async def update_slider(data: SliderData):
    global w1, w2, w3, w4, w5
    print(f"Received {data.sliderId} with value {data.value}")
    match data.sliderId:
        case "slider1":
            w1 = data.value/25
        case "slider2":
            w2 = data.value/25
        case "slider3":
            w3 = data.value/25
        case "slider4":
            w4 = data.value/25  
        case "slider5":
            w5 = data.value/25      
    return JSONResponse(content={"message": "Weight value updated successfully!"})

@router.get("/search-results")
async def search_results(
    is_popular: bool = Query(False),
    is_public: bool = Query(False),
    order: List[str] = Query(...),
    difficulty: Optional[List[str]] = Query(None, alias="difficulty[]"),
    page: int = Query(...),
    query: str = Query(...),
    type: str = Query(...),
    price__gte: int = Query(0),
    price__lte: int = Query(999999),
    promo_price__gte: Optional[int] = Query(None),
    with_certificate: Optional[bool] = Query(None),
    is_specialization: Optional[bool] = Query(None),
    is_paid: Optional[bool] = Query(None),
    language: Optional[str] = Query(None),
):
    if type != "course":
        return "{}"
    vector = await encoder.vectorize(query)
    limit = 20
    must = []
    must_not = []
    # boolean conditions
    must.append(models.FieldCondition(
        key="is_popular",
        match=models.MatchValue(value=is_popular)
    ))
    must.append(models.FieldCondition(
        key="is_public",
        match=models.MatchValue(value=is_public)
    ))

    if promo_price__gte == 1:
        must_not.append(models.IsNullCondition(is_null=models.PayloadField(key="default_promo_code_name")))

    if with_certificate != None:
        must.append(models.FieldCondition(
            key="with_certificate",
            match=models.MatchValue(value=with_certificate)
        ))

    # Difficulty
    if difficulty != None:
        must.append(models.FieldCondition(
            key="difficulty",
            match=models.MatchAny(any=difficulty)
        ))

    # Price
    if is_paid != None and is_paid == True:
        price__gte = 1
    must.append(models.FieldCondition(
        key="price",
        range=models.Range(
            gte=price__gte,
            lte=price__lte
        ),
    ))

    if language != None:
        must.append(models.FieldCondition(
            key="language",
            match=models.MatchValue(value=language)
        ))
    if is_specialization != None:
        if is_specialization:
            must.append(models.FieldCondition(
                key="child_courses_count",
                match=models.MatchExcept(**{"except": [0]})
            ))
        else:
            must.append(models.FieldCondition(
                key="child_courses_count",
                match=models.MatchValue(value=0)
            ))
        

    search_results = []

    if qdrant.client != None:

        result = await run_blocking(
            qdrant.client.query_points,
            collection_name="courses",
            query=vector,
            limit=limit * 10,
            offset=0,
            query_filter=models.Filter(
                must=must,
                must_not=must_not
            ),
        )
        print(f"Result: {len(result.points)}", flush=True)
        max_learners_count = 1
        max_price = 1
        if result.points:
            for point in result.points:
                payload = point.payload
                if max_learners_count < payload['pupils_num']:
                    max_learners_count = payload['pupils_num']
                if max_price < payload['price']:
                    max_price = payload['price']
        if result.points:
            for point in result.points:
                payload = point.payload
                score_components = [
                    point.score * w1,  # Base search score
                    payload['rating'] / 5 * w2,  # Rating component
                    payload['pupils_num'] / max_learners_count * w3 if max_learners_count > 0 else 0,
                    # Popularity component
                    int(payload['with_certificate']) * w4,  # Certificate component
                    payload['price'] / max_price * w5 if max_price > 0 else 0  # Price component
                ]
                search_results.append(CourseInSearch(
                    id=random.randint(10, 10000000),
                    position=0,  # Initial position, will be updated later
                    score=sum(score_components),
                    target_id=payload['id'],
                    target_type="course",
                    course=payload['id'],
                    course_owner=payload.get('owner', 0),
                    course_authors=payload.get('stepik_authors', [0]),
                    course_title=payload['title'],
                    course_slug=payload.get('slug', payload['title']),
                    course_cover=payload['cover_url'] if payload['cover_url'] is not None else "",
                    lesson=None,
                    lesson_owner=None,
                    lesson_title=None,
                    lesson_slug=None,
                    lesson_cover_url=None,
                    step=None,
                    step_position=None,
                    comment=None,
                    comment_parent=None,
                    comment_user=None,
                    comment_text=None
                ))

        search_results.sort(key=lambda x: x.score, reverse=True)

        search_results = search_results[(page-1)*limit:limit*page]

        for index, course in enumerate(search_results):
            course.position = index
    response = SearchResultsResponse(
        meta=Meta(page=page, has_next=True, has_previous=False, count=200),
        search_results=search_results
    )
    return response