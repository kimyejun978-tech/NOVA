import urllib.error

import nova.updater as updater


def test_check_latest_falls_back_when_github_api_returns_403(monkeypatch):
    def blocked(_url):
        raise urllib.error.HTTPError(_url, 403, "rate limited", {}, None)

    monkeypatch.setattr(updater, "_request_json", blocked)
    monkeypatch.setattr(updater, "_release_version_from_web", lambda: "9.9.9")

    info = updater.check_latest()

    assert info.available
    assert info.version == "9.9.9"
    assert info.download_url.endswith("/releases/download/v9.9.9/NOVA-Source.zip")
    assert info.sha256_url.endswith("/releases/download/v9.9.9/NOVA-Source.zip.sha256")
    assert "fallback" in info.notes.lower()


def test_fallback_uses_raw_version_when_release_redirect_fails(monkeypatch):
    def web_fail():
        raise RuntimeError("blocked")

    monkeypatch.setattr(updater, "_release_version_from_web", web_fail)
    monkeypatch.setattr(updater, "_release_version_from_raw", lambda: "9.9.8")

    info = updater._fallback_update_info("GitHub API HTTP 403")

    assert info.version == "9.9.8"
    assert info.release_url.endswith("/releases/tag/v9.9.8")
    assert info.download_url.endswith("/releases/download/v9.9.8/NOVA-Source.zip")
