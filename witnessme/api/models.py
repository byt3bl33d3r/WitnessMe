import ipaddress
import uuid
from typing import Optional, List, Union
from pydantic import BaseModel, AnyUrl


class ScanStats(BaseModel):
    inputs: int
    execs: int
    started: bool = False
    done: bool = False
    pending: int

    class Config:
        orm_mode = True


class ScanConfig(BaseModel):
    target: List[Union[AnyUrl, str]]
    ports: Optional[List[int]] = [80, 8080, 443, 8443]
    threads: Optional[int] = 25
    timeout: Optional[int] = 35


class Scan(BaseModel):
    id: uuid.UUID
    target: List[str]
    ports: List[int]
    threads: int
    timeout: int
    stats: ScanStats
    report_folder: str

    class Config:
        orm_mode = True
