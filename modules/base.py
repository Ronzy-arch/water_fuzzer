# modules/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseModule(ABC):
    """
    Kelas abstrak induk (Interface Contract) V10.1 Komersial.
    Mendisiplinkan seluruh agen detektif lapangan agar seragam mengadopsi
    penerimaan instans auditor pusat serta penanganan pipa audit asinkronus.
    """
    def __init__(self, auditor_instance: Any) -> None:
        self.auditor: Any = auditor_instance

    @abstractmethod
    async def run_audit(self, session: Any) -> bool:
        pass
