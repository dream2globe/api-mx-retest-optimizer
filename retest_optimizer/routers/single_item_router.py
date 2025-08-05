from db.redis_config import get_defect_key, get_redis_instance
from fastapi import APIRouter, Body, HTTPException, status
from loguru import logger
from models.defect_model import (
    CreateRecordRequest,
    CreateResponse,
    InspectionRequest,
    InspectionResponse,
)

router = APIRouter(prefix="/api/v1/inspection/single")


@router.post(
    "/check",
    response_model=InspectionResponse,
    summary="단일 불량 항목 재검사 여부 조회",
    description="주어진 조건에 따라 특정 불량 항목의 재검사 필요 여부를 판단하여 반환합니다.",
)
async def check_single_item(request: InspectionRequest = Body(...)):
    logger.info(f"단일 항목 조회 요청 수신: {request.dict()}")

    # 커스텀 PK 생성
    custom_pk = f"{request.factory_code}:{request.process_code}:{request.product_model}:{request.defect_item}"
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()

    try:
        data = await redis.hgetall(key_name)

        # --- 키가 없는 경우의 처리 ---
        if not data:
            logger.warning(f"데이터를 찾을 수 없음 (PK: {custom_pk}). 검사 이력 없음으로 간주.")
            return InspectionResponse(
                retest_needed=False,  # 재검사 필요
                reproducibility_rate=0.0,
                alarm_history="0/0",
                request_data=request,
            )

        # --- 키가 있는 경우의 처리 ---
        # Redis는 모든 값을 문자열로 저장하므로, 숫자 타입으로 변환
        reproducibility_rate = float(data["reproducibility_rate"])
        total_inspections = int(data["total_inspections"])
        reproduced_count = int(data["reproduced_count"])

        # 재검사 필요 여부 판단 로직
        is_reproducible_enough = reproducibility_rate >= request.reproducibility_criteria
        has_enough_data = total_inspections >= request.min_inspection_criteria
        retest_needed_flag = not (is_reproducible_enough and has_enough_data)

        logger.info(
            f"판단 결과 (PK: {custom_pk}): 재검사 필요? {'아니오' if not retest_needed_flag else '예'}"
        )

        return InspectionResponse(
            retest_needed=not retest_needed_flag,
            reproducibility_rate=reproducibility_rate,
            alarm_history=f"{reproduced_count}/{total_inspections}",
            request_data=request,
        )

    except Exception as e:
        logger.error(f"Redis 조회 또는 데이터 처리 중 에러 발생 (PK: {custom_pk}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


@router.post(
    "/record",
    response_model=CreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="단일 불량 데이터 생성/업데이트",
    description="커스텀 PK를 사용하여 불량 데이터를 Redis에 저장(생성 또는 덮어쓰기)합니다.",
)
async def create_or_update_record(record: CreateRecordRequest = Body(...)):
    logger.info(f"단일 레코드 생성/업데이트 요청: {record.dict()}")

    custom_pk = (
        f"{record.factory_code}:{record.process_code}:{record.product_model}:{record.defect_item}"
    )
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()

    try:
        # Pydantic 모델을 dict로 변환하여 저장
        await redis.hset(key_name, mapping=record.dict())

        logger.success(f"레코드 저장 완료. PK: {custom_pk}")
        return CreateResponse(pk=custom_pk, status="created_or_updated")
    except Exception as e:
        logger.error(f"레코드 저장 중 에러 발생 (PK: {custom_pk}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )
