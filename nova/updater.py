from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.error
import urllib.request
import zipfile

from .config import APP_VERSION, UPDATE_ASSET_EXE, UPDATE_ASSET_SOURCE, UPDATE_DIR, UPDATE_OWNER, UPDATE_REPO


@dataclass
class UpdateInfo:
    available: bool
    version: str
    current_version: str
    title: str
    notes: str
    download_url: str | None
    sha256_url: str | None
    api_digest: str | None
    release_url: str | None
    asset_name: str


def _version_tuple(text: str) -> tuple[int, ...]:
    cleaned = text.strip().lower().lstrip("v")
    core = cleaned.split("-", 1)[0]
    out: list[int] = []
    for part in core.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits or 0))
    return tuple((out + [0, 0, 0])[:3])


def _request_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"NOVA/{APP_VERSION}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def check_latest() -> UpdateInfo:
    url = f"https://api.github.com/repos/{UPDATE_OWNER}/{UPDATE_REPO}/releases/latest"
    try:
        payload = _request_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(
                f"업데이트 저장소 {UPDATE_OWNER}/{UPDATE_REPO} 또는 Release를 찾을 수 없습니다. "
                "GitHub 저장소를 만든 뒤 Release를 게시하면 자동 업데이트가 활성화됩니다."
            ) from e
        raise RuntimeError(f"업데이트 확인 HTTP 오류: {e.code}") from e
    except Exception as e:
        raise RuntimeError(f"업데이트 확인 실패: {e}") from e

    tag = str(payload.get("tag_name") or "0.0.0")
    latest_version = tag.lstrip("vV")
    assets = payload.get("assets") or []
    asset_name = UPDATE_ASSET_EXE if bool(getattr(sys, "frozen", False)) else UPDATE_ASSET_SOURCE
    asset = next((a for a in assets if a.get("name") == asset_name), None)
    sha_asset = next((a for a in assets if a.get("name") == asset_name + ".sha256"), None)

    available = _version_tuple(latest_version) > _version_tuple(APP_VERSION)
    return UpdateInfo(
        available=available,
        version=latest_version,
        current_version=APP_VERSION,
        title=str(payload.get("name") or tag),
        notes=str(payload.get("body") or ""),
        download_url=asset.get("browser_download_url") if asset else None,
        sha256_url=sha_asset.get("browser_download_url") if sha_asset else None,
        api_digest=asset.get("digest") if asset else None,
        release_url=payload.get("html_url"),
        asset_name=asset_name,
    )


def _download(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": f"NOVA/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=60) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _expected_hash(info: UpdateInfo) -> str | None:
    if info.api_digest and str(info.api_digest).startswith("sha256:"):
        return str(info.api_digest).split(":", 1)[1].strip().lower()
    if info.sha256_url:
        tmp = UPDATE_DIR / f"{info.asset_name}.sha256.download"
        _download(info.sha256_url, tmp)
        try:
            text = tmp.read_text(encoding="utf-8", errors="replace").strip()
            return text.split()[0].lower() if text else None
        finally:
            tmp.unlink(missing_ok=True)
    return None


def _safe_extract(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            if destination != target and destination not in target.parents:
                raise RuntimeError("업데이트 ZIP에 허용되지 않은 경로가 포함되어 있습니다.")
        zf.extractall(destination)


def stage_update(info: UpdateInfo) -> Path:
    if not info.available:
        raise RuntimeError("설치할 새 버전이 없습니다.")
    if not info.download_url:
        raise RuntimeError(f"Release에 {info.asset_name} 파일이 없습니다.")

    version_dir = UPDATE_DIR / info.version
    if version_dir.exists():
        shutil.rmtree(version_dir, ignore_errors=True)
    version_dir.mkdir(parents=True, exist_ok=True)
    archive = version_dir / info.asset_name
    payload_dir = version_dir / "payload"
    payload_dir.mkdir(parents=True, exist_ok=True)

    _download(info.download_url, archive)
    expected = _expected_hash(info)
    if not expected:
        raise RuntimeError(
            "업데이트 파일의 SHA-256을 확인할 수 없어 자동 설치를 중지했습니다. "
            f"Release에 {info.asset_name}.sha256을 함께 올려주세요."
        )
    actual = _sha256(archive)
    if actual.lower() != expected.lower():
        raise RuntimeError("업데이트 SHA-256 검증에 실패했습니다. 파일을 적용하지 않습니다.")

    _safe_extract(archive, payload_dir)
    children = [p for p in payload_dir.iterdir()]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return payload_dir
