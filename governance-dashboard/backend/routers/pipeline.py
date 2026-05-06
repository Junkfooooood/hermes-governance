"""GET /api/pipeline/stages — pipeline stage definitions."""

from fastapi import APIRouter

router = APIRouter()

PIPELINE_STAGES = [
    {"id": "interview", "label": "Deep Interview", "agent": "zhongshu"},
    {"id": "plan", "label": "规划", "agent": "zhongshu"},
    {"id": "review_spec", "label": "Spec 审核", "agent": "menxia"},
    {"id": "review_quality", "label": "质量审核", "agent": "menxia"},
    {"id": "decompose", "label": "任务分解", "agent": "shangshu"},
    {"id": "dispatch", "label": "派发", "agent": "shangshu"},
    {"id": "execute", "label": "执行", "agent": "六部"},
    {"id": "verify", "label": "验证", "agent": "xingbu"},
    {"id": "integrate", "label": "整合", "agent": "shangshu"},
]


def init():
    pass


@router.get("/api/pipeline/stages")
async def get_pipeline_stages():
    return {"stages": PIPELINE_STAGES}
