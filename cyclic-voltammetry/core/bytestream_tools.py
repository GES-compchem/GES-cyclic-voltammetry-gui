from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO, TextIOWrapper
from typing import List

@dataclass
class BytesStreamManager:
    name: str
    __stream: BytesIO

    @property
    def filename(self):
        return self.name

    @property
    def bytestream(self) -> BytesIO:
        self.__stream.seek(0)
        return self.__stream

    def __iter__(self):
        text_stream = TextIOWrapper(self.bytestream, encoding="utf-8")
        for line in text_stream:
            yield line
        text_stream.detach()

    def __iadd__(self, obj: BytesStreamManager) -> BytesStreamManager:
        lines: List[str] = []
        for line in self:
            lines.append(line)
        if not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        for line in obj:
            lines.append(line)
        buffer = "".join(lines)
        self.__stream = BytesIO(buffer.encode("utf-8"))
        return self