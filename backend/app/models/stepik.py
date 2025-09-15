from typing import List, Optional
from pydantic import BaseModel

class CourseInSearch(BaseModel):
    id: int
    position: int
    score: float
    target_id: int
    target_type: str
    course: int
    course_owner: int
    course_authors: List[int]
    course_title: str
    course_slug: str
    course_cover: str
    lesson: Optional[str] = None
    lesson_owner: Optional[int] = None
    lesson_title: Optional[str] = None
    lesson_slug: Optional[str] = None
    lesson_cover_url: Optional[str] = None
    step: Optional[str] = None
    step_position: Optional[int] = None
    comment: Optional[str] = None
    comment_parent: Optional[int] = None
    comment_user: Optional[int] = None
    comment_text: Optional[str] = None

class Meta(BaseModel):
    page: int
    has_next: bool
    has_previous: bool
    count: int

class SearchResultsResponse(BaseModel):
    meta: Meta
    search_results: List[CourseInSearch]