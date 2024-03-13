from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel

import model
from api.utils import exception_handler
from database import get_db
from config import RoomStatus
import uuid
router = APIRouter()
occupied = RoomStatus.Occupied.value
booked = RoomStatus.Booked.value

class ReserveRecv(BaseModel):
    name: str
    tel: str
    age: int
    scheduled_date: str
    check_in_date: str
    hospital_for_childbirth: str
    contact_name: str
    contact_tel: str
    meal_plan_id: int
    recovery_plan_id: Optional[int] = None
    mode_of_delivery: str
    assigned_baby_nurse: int
    room: str

    class Config:
        orm_mode = True


class ReserveResp(BaseModel):
    status: str
    details: str


# 只新增client，不新增Baby
@exception_handler
def update_client_and_room(db, reserve_recv: ReserveRecv):
    db_client = model.Client(**reserve_recv.dict())
    # db_client = model.Client(
    #     meal_plan_id=reserve_recv.meal_plan_id,
    #     recovery_plan_id=reserve_recv.recovery_plan_id,
    #     assigned_baby_nurse=reserve_recv.assigned_baby_nurse,
    #     name=reserve_recv.name,
    #     tel=reserve_recv.tel,
    #     age=reserve_recv.age,
    #     scheduled_date=reserve_recv.scheduled_date,
    #     check_in_date=reserve_recv.check_in_date,
    #     hospital_for_childbirth=reserve_recv.hospital_for_childbirth,
    #     contact_name=reserve_recv.contact_name,
    #     contact_tel=reserve_recv.contact_tel,
    #     mode_of_delivery=reserve_recv.mode_of_delivery,
    #     room=reserve_recv.room,
    # )
    create_client_sql = text(
        """
        INSERT INTO client (id, name, tel, age, scheduled_date, check_in_date, hospital_for_childbirth, contact_name, contact_tel, mode_of_delivery, room)
        VALUES (:id, :name, :tel, :age, :scheduled_date, :check_in_date, :hospital_for_childbirth, :contact_name, :contact_tel, :mode_of_delivery, :room)
        """
    )
    update_room_sql = text(
        """
        UPDATE room SET status = :booked WHERE room_number = :room;
        UPDATE room SET client_id = (SELECT id FROM client WHERE name = :name) WHERE room_number = :room;
        """
    )
    try:
        with db.begin():
            client_data = dict(reserve_recv)
            client_id = uuid.uuid4()  # 生成新的客户ID
            client_data["id"] = client_id
            db.execute(create_client_sql, client_data)


            db.execute(update_room_sql,
                       {"name": client_data.get("name"),  # 这里假设你从client_data中可以获取到name
                        "room": client_data.get("room"),
                        "booked": booked,
                        "client_id": client_id  # 使用第一个操作生成的client_id
                        }
                       )
            # 如果以上操作都成功执行，事务会自动提交
    except SQLAlchemyError as e:
        print("发生错误，事务回滚:", e)
        raise e

@router.post("/reserve")
async def reserve_room(reserve_recv: ReserveRecv, db: Session = Depends(get_db)):
    try:
        update_client_and_room(db, reserve_recv)
        return ReserveResp(status="success", details="预定成功")
    except Exception as e:
        return ReserveResp(status="error", details=str(e))
'''
the logic of reserve:
1. about room table: update room.status = booked, update room.client_id
2. about client table: add client
3. do not add baby in reservation
4. return ReserveResp
'''