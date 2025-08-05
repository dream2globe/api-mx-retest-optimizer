import asyncio
from typing import List

from db.redis_config import get_defect_key, get_redis_instance
from fastapi import APIRouter, Body, status
from loguru import logger
from models.defect_model import (
    BulkCreateRecordRequest,
    BulkInspectionRequest,
    BulkInspectionResponse,
    CreateRecordRequest,
    CreateResponse,
    InspectionRequest,
    InspectionResponse,
)

router = APIRouter(prefix="/api/v1/inspection/bulk")


async def process_single_check_request(request: InspectionRequest) -> InspectionResponse:
    """단일 조회 요청을 처리하는 내부 헬퍼 함수"""
    custom_pk = f"{request.factory_code}:{request.process_code}:{request.product_model}:{request.defect_item}"
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()

    try:
        data = await redis.hgetall(key_name)
        if not data:
            return InspectionResponse(
                retest_needed=False,
                reproducibility_rate=0.0,
                alarm_history="0/0",
                request_data=request,
            )

        reproducibility_rate = float(data["reproducibility_rate"])
        total_inspections = int(data["total_inspections"])
        reproduced_count = int(data["reproduced_count"])

        is_reproducible_enough = reproducibility_rate >= request.reproducibility_criteria
        has_enough_data = total_inspections >= request.min_inspection_criteria
        retest_needed_flag = not (is_reproducible_enough and has_enough_data)

        return InspectionResponse(
            retest_needed=not retest_needed_flag,
            reproducibility_rate=reproducibility_rate,
            alarm_history=f"{reproduced_count}/{total_inspections}",
            request_data=request,
        )
    except Exception as e:
        logger.error(f"벌크 조회 중 개별 항목 에러 (PK: {custom_pk}): {e}")
        # 오류 발생 시에도 기본 응답 포맷을 따름
        return InspectionResponse(
            retest_needed=False,
            reproducibility_rate=0.0,
            alarm_history="error",
            request_data=request,
        )


@router.post(
    "/check",
    response_model=BulkInspectionResponse,
    summary="여러 불량 항목 재검사 여부 동시 조회",
)
async def check_bulk_items(bulk_request: BulkInspectionRequest = Body(...)):
    logger.info(f"벌크 조회 요청 수신: {len(bulk_request.requests)}개 항목")
    tasks = [process_single_check_request(req) for req in bulk_request.requests]
    results = await asyncio.gather(*tasks)
    logger.success(f"벌크 조회 처리 완료: {len(results)}개 항목")
    return BulkInspectionResponse(results=results)


async def process_single_create_record(record: CreateRecordRequest) -> CreateResponse:
    """단일 레코드 저장을 처리하는 내부 헬퍼 함수"""
    custom_pk = (
        f"{record.factory_code}:{record.process_code}:{record.product_model}:{record.defect_item}"
    )
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()
    try:
        await redis.hset(key_name, mapping=record.dict())
        return CreateResponse(pk=custom_pk, status="created_or_updated")
    except Exception as e:
        logger.error(f"벌크 저장 중 개별 항목 에러 (PK: {custom_pk}): {e}")
        return CreateResponse(pk=custom_pk, status=f"error: {e}")


@router.post(
    "/records",
    response_model=List[CreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="여러 불량 데이터 동시 생성/업데이트",
)
async def create_or_update_bulk_records(bulk_record: BulkCreateRecordRequest = Body(...)):
    logger.info(f"벌크 레코드 생성/업데이트 요청: {len(bulk_record.records)}개 항목")
    tasks = [process_single_create_record(rec) for rec in bulk_record.records]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if "error" not in r.status)
    logger.success(f"벌크 레코드 처리 완료. 성공: {success_count}/{len(results)}")
    return results
