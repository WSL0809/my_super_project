from typing import Union, List, Dict, Optional

from fastapi import Depends, APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_active_user
from auth_schema import User
from database import get_db
from model import Client
from schema import ClientBase
import re

router = APIRouter()


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class GetAllClientsResp(BaseModel):
    status: Union[str, int]
    details: str
    clients: List[ClientBase]
    pagination: Pagination


def clean_input(input_string):
    # 去除首尾空格
    cleaned = input_string.strip()
    # 去除内部多余的空格（将一个或多个连续的空白字符替换为单个空格）
    cleaned = re.sub(r'\s+', '', cleaned)
    # 去除换行符和制表符
    cleaned = cleaned.replace('\n', '').replace('\t', '').replace('%20', ' ')
    return cleaned


def get_clients(db: Session, name: Optional[str], page: int, limit: int):
    # 计算起始记录

    offset = (page - 1) * limit

    query = db.query(Client)
    if name:
        name = clean_input(name)
        query = query.filter(Client.name.ilike(f"%{name}%"))

    # 查询客户数据
    clients = query.offset(offset).limit(limit).all()

    clients_data = [ClientBase.from_orm(client) for client in clients]

    # 计算总记录数
    total = query.count()

    return total, clients_data


@router.get("/get_clients", response_model=GetAllClientsResp)
def get_clients_by_name(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
                        name: Optional[str] = Query(None), page: int = 1, limit: int = 10):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")

    total, clients = get_clients(db, name, page, limit)
    if not clients:
        raise HTTPException(status_code=404, detail="Clients not found")

    pagination = {
        "page": page,
        "limit": limit,
        "total": total
    }

    return {
        "status": "success",
        "details": "Clients fetched successfully.",
        "clients": clients,
        "pagination": pagination
    }