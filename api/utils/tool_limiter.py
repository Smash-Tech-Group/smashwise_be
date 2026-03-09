from typing import Callable
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from functools import wraps
from datetime import timedelta

from api.db.database import get_db
from api.utils.helpers import get_ip_address
from api.v1.services.user import user_service
from api.v1.services.usage import usage_store_service
from api.v1.services.user_usage import user_usage_store_service
from api.v1.services.billing_plan import billing_plan_service
from api.v1.models.user import User
from api.utils.settings import settings

ACCESS_LIMIT = 3
TIME_WINDOW = timedelta(days=1)


# Usage
# add decorator on top of function not route
# @track_tool_usage(current_tool="example_tool")
# then add these arguments into the route function
# request: Request,
# db: Session = Depends(get_db),
# user: User = Depends(user_service.get_current_user_optional)


def track_tool_usage(current_tool: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            db: Session = kwargs.get("db", Depends(get_db))
            user: User | None = kwargs.get(
                "user", Depends(user_service.get_current_user_optional)
            )
            if settings.ACTIVATE_TOOL_TRACKING:
                if user:
                    tracking_record = user_usage_store_service.fetch_by_user(
                        db, user.id
                    )
                    if tracking_record:
                        tool_count = user_usage_store_service.get_or_create_tool_value(
                            db, tracking_record.id, current_tool
                        )
                        if tracking_record.is_access_count_exceeded(
                            user.subscription.billing_plan.access_limit
                        ):
                            if billing_plan_service.confirm_user_is_on_plan(
                                db, user, "Free"
                            ):
                                if tracking_record.is_last_accessed_old(24):
                                    hours, minutes, seconds = (
                                        tracking_record.time_until(2)
                                    )
                                    message = f"{hours} hours, {minutes} minutes, {seconds} seconds"
                                    raise HTTPException(
                                        status_code=status.HTTP_403_FORBIDDEN,
                                        detail=f"Please to get more access to out tools wait for {message} to gain access.",
                                    )
                                else:
                                    user_usage_store_service.update_tool_access_count_by_id(
                                        db, tracking_record.id, 1
                                    )
                                    user_usage_store_service.update_tool_usage(
                                        db,
                                        tracking_record.id,
                                        current_tool,
                                        tool_count + 1,
                                    )
                                    return await func(*args, **kwargs)
                            else:
                                if user.subscription.is_active():
                                    if billing_plan_service.confirm_user_is_on_plan(
                                        db, user, "premium_monthly"
                                    ):
                                        if tracking_record.is_last_accessed_old(2):
                                            hours, minutes, seconds = (
                                                tracking_record.time_until(2)
                                            )
                                            message = f"{hours} hours, {minutes} minutes, {seconds} seconds"
                                        else:
                                            user_usage_store_service.update_tool_access_count_by_id(
                                                db, tracking_record.id, 1
                                            )
                                            user_usage_store_service.update_tool_usage(
                                                db,
                                                tracking_record.id,
                                                current_tool,
                                                tool_count + 1,
                                            )
                                            return await func(*args, **kwargs)
                                    else:
                                        if tracking_record.is_last_accessed_old(1):
                                            hours, minutes, seconds = (
                                                tracking_record.time_until(1)
                                            )
                                            message = f"{hours} hours, {minutes} minutes, {seconds} seconds"
                                        else:
                                            user_usage_store_service.update_tool_access_count_by_id(
                                                db, tracking_record.id, 1
                                            )
                                            user_usage_store_service.update_tool_usage(
                                                db,
                                                tracking_record.id,
                                                current_tool,
                                                tool_count + 1,
                                            )
                                            return await func(*args, **kwargs)
                                    raise HTTPException(
                                        status_code=status.HTTP_403_FORBIDDEN,
                                        detail=f"Please to get more access to out tools wait for {message} to gain access.",
                                    )
                                else:
                                    billing_plan_service.subscribe_user_to_free_plan(
                                        db, user
                                    )
                                    user_usage_store_service.update_tool_access_count_by_id(
                                        db, tracking_record.id, 1
                                    )
                                    user_usage_store_service.update_tool_usage(
                                        db,
                                        tracking_record.id,
                                        current_tool,
                                        tool_count + 1,
                                    )
                        else:
                            user_usage_store_service.add_tool_access_count_by_user(
                                db, user.id, 1
                            )
                            user_usage_store_service.update_tool_usage(
                                db, tracking_record.id, current_tool, tool_count + 1
                            )
                    else:
                        tracking_record = (
                            user_usage_store_service.create_usage_store_and_assign_tool(
                                db, user.id, current_tool, 1, 1
                            )
                        )
                    return await func(*args, **kwargs)

                client_ip = get_ip_address(request)
                tracking_record = usage_store_service.fetch_by_user(db, client_ip)
                if tracking_record:
                    if tracking_record.is_access_count_exceeded(ACCESS_LIMIT):
                        if tracking_record.is_last_accessed_old(24):
                            usage_store_service.update_store_access_count(
                                db, client_ip, 1
                            )
                        else:
                            hours, minutes, seconds = tracking_record.time_until(24)
                            message = (
                                f"{hours} hours, {minutes} minutes, {seconds} seconds"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Please log in to continue using our tools or wait for {message}.",
                            )
                    else:
                        usage_store_service.add_tool_access_count_by_user(
                            db, client_ip, 1
                        )
                        usage_store_service.add_tool_count_by_id(
                            db, tracking_record.id, current_tool, 1
                        )
                else:
                    usage_store_service.create_usage_store_and_assign_tool(
                        db, client_ip, current_tool, 1, 1
                    )

                return await func(*args, **kwargs)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
