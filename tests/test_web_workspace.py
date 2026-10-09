from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_workspace_lists_uploaded_file(tmp_path, monkeypatch):
    from app.workspace.manager import WorkspaceManager

    monkeypatch.setattr("app.workspace.manager.manager", WorkspaceManager(str(tmp_path / "ws")))

    with TestClient(app) as client:
        up = client.post(
            "/api/v2/web/sessions/s1/upload",
            params={"user_id": "u1"},
            files=[("files", ("doc.md", b"# hi", "text/plain"))],
        )
        assert up.status_code == 200

        ws = client.get("/api/v2/web/workspace", params={"user_id": "u1", "session_id": "s1"})
        assert ws.status_code == 200
        data = ws.json()
        paths = {f["rel_path"] for f in data["files"]}
        assert "data/uploads/doc.md" in paths
        assert data["session_path"].endswith("u1/s1")
        assert data["session_rel"] == "u1/s1"
        assert "session_path_windows" in data
        assert data["upload_count"] >= 1
        assert "hint" in data


def test_workspace_reveal_returns_ok(tmp_path, monkeypatch):
    from app.workspace.manager import WorkspaceManager

    monkeypatch.setattr("app.workspace.manager.manager", WorkspaceManager(str(tmp_path / "ws")))
    monkeypatch.setattr(
        "app.api.web_data._reveal_folder_in_os",
        lambda p: {"opened_with": "mock", "windows_path": r"\\wsl.localhost\Ubuntu\mock"},
    )

    with TestClient(app) as client:
        r = client.post(
            "/api/v2/web/workspace/reveal",
            params={"user_id": "u1", "session_id": "s1"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["opened_with"] == "mock"
    # session_path_windows 是平台感知的:WSL 下为 UNC(\\wsl.localhost\...),
    # macOS/Linux 原生路径直接返回。断言按平台分支,两种合法形态都接受。
    from app.web_store.workspace_info import linux_path_to_windows  # noqa: E402

    if linux_path_to_windows(str(tmp_path.resolve())):  # WSL 环境 → 期望 UNC
        assert "wsl.localhost" in body["session_path_windows"]
    else:  # macOS / 原生 Linux → 期望返回解析后的原生路径
        assert body["session_path_windows"].endswith("/u1/s1")
        assert Path(body["session_path_windows"]).is_absolute()
