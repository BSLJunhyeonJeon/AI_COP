"""HTTP Range 요청으로 원격 zip 안의 파일 몇 개만 꺼내는 도구 (표준 라이브러리만 사용).

zip 전체(예: NuInsSeg 1.6 GB)를 받지 않고, 끝부분의 목차와 필요한 파일 구간만 내려받는다.
서버가 Range 요청(HTTP 206)을 지원해야 한다 — Zenodo 는 지원한다(2026-10-22 확인).
"""
import io
import urllib.request


class HttpRangeFile(io.RawIOBase):
    def __init__(self, url, block=1 << 20):
        self.url, self.block, self.pos = url, block, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
        self._cache = {}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def _get_block(self, i):
        if i not in self._cache:
            start = i * self.block
            end = min(start + self.block, self.size) - 1
            req = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status != 206:
                    raise IOError(f"서버가 부분 다운로드를 지원하지 않습니다 (HTTP {r.status})")
                self._cache[i] = r.read()
            if len(self._cache) > 64:  # 메모리 보호
                self._cache.pop(next(iter(self._cache)))
        return self._cache[i]

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        out = bytearray()
        while n > 0:
            i, o = divmod(self.pos, self.block)
            chunk = self._get_block(i)[o:o + n]
            out += chunk
            self.pos += len(chunk)
            n -= len(chunk)
        return bytes(out)

    def readinto(self, b):
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)
