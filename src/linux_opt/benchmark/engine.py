"""Minimal CPU/memory/disk/network micro-benchmarks producing a baseline (FR-011).

These are intentionally small and dependency-free first passes -- enough to
produce comparable numbers run-to-run, not a replacement for fio/sysbench/iperf.
A --safe flag isn't needed here since nothing here touches persistent state
outside a throwaway temp file.
"""

from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    name: str
    value: float
    unit: str


def benchmark_cpu(duration_s: float = 0.5) -> BenchmarkResult:
    """Counts how many times a small pure-Python loop completes in duration_s."""
    end = time.monotonic() + duration_s
    iterations = 0
    x = 0
    while time.monotonic() < end:
        for _ in range(10_000):
            x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        iterations += 1
    return BenchmarkResult("cpu", iterations / duration_s, "iterations/sec")


def benchmark_memory(size_mb: int = 64) -> BenchmarkResult:
    """Times a large bytearray allocate + sequential write."""
    size = size_mb * 1024 * 1024
    start = time.monotonic()
    buf = bytearray(size)
    for i in range(0, size, 4096):
        buf[i] = 1
    elapsed = time.monotonic() - start
    throughput_mb_s = size_mb / elapsed if elapsed > 0 else float("inf")
    return BenchmarkResult("memory", throughput_mb_s, "MB/sec")


def benchmark_disk(size_mb: int = 32) -> BenchmarkResult:
    """Times a sequential write + fsync of a throwaway temp file."""
    size = size_mb * 1024 * 1024
    chunk = b"\0" * (1024 * 1024)
    fd, path = tempfile.mkstemp(prefix="linux_opt_bench_")
    try:
        start = time.monotonic()
        with os.fdopen(fd, "wb") as f:
            written = 0
            while written < size:
                f.write(chunk)
                written += len(chunk)
            f.flush()
            os.fsync(f.fileno())
        elapsed = time.monotonic() - start
    finally:
        os.remove(path)
    throughput_mb_s = size_mb / elapsed if elapsed > 0 else float("inf")
    return BenchmarkResult("disk", throughput_mb_s, "MB/sec")


def benchmark_network(size_mb: int = 16) -> BenchmarkResult:
    """Loopback-socket throughput; the closest thing to a network test with zero external dependencies."""
    import socket
    import threading

    size = size_mb * 1024 * 1024
    chunk = b"\0" * (256 * 1024)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    received = {"bytes": 0}

    def _receiver() -> None:
        conn, _ = server.accept()
        with conn:
            while received["bytes"] < size:
                data = conn.recv(len(chunk))
                if not data:
                    break
                received["bytes"] += len(data)

    thread = threading.Thread(target=_receiver, daemon=True)
    thread.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    start = time.monotonic()
    sent = 0
    while sent < size:
        client.sendall(chunk)
        sent += len(chunk)
    client.close()
    thread.join(timeout=5)
    elapsed = time.monotonic() - start
    server.close()

    throughput_mb_s = size_mb / elapsed if elapsed > 0 else float("inf")
    return BenchmarkResult("network", throughput_mb_s, "MB/sec")


def run_all() -> list[BenchmarkResult]:
    return [benchmark_cpu(), benchmark_memory(), benchmark_disk(), benchmark_network()]
