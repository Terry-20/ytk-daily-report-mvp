"""粤通卡日报网页 MVP（概念验证）。

启动：
    python app.py
监听 127.0.0.1:5055。

特性：
- 静态口令登录（读环境变量 MVP_PASSWORD，缺省 unitoll），非持久 session cookie，关浏览器即失效。
- 工作台：逐文件上传 材料1.xlsx / 材料2.xlsx（文件名大小写不敏感，扩展名须为 .xlsx）。
- 校验：缺一 / 错名 / 多无关文件 -> 中文报错，不生成。
- 计算：货款 = 产品数量 × 单价，生成 结果.xlsx（单 sheet，表头仅「货款」）。
- 按钮：开始生成 | 清空本次上传 | 下载成品（无成品时禁用）。
- 会话隔离：每个登录生成 session id，上传与成品存于 uploads/<sid>/；退出或重新登录时清理旧上传。
"""

import os
import shutil
import uuid

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from mvp_core import build_result, compute_payment

app = Flask(__name__)
app.secret_key = os.environ.get("MVP_SECRET", "dev-secret-change-me")
PASSWORD = os.environ.get("MVP_PASSWORD", "unitoll")

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE, "uploads")

# 期望的文件名（小写比较）-> 表头关键字
EXPECTED = {
    "材料1.xlsx": "产品数量",
    "材料2.xlsx": "单价",
}


def _session_dir():
    sid = session.get("sid")
    if not sid:
        return None
    return os.path.join(UPLOAD_ROOT, sid)


def _ensure_session_dir():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    d = _session_dir()
    os.makedirs(d, exist_ok=True)
    return d


def _clean_all_uploads():
    if os.path.isdir(UPLOAD_ROOT):
        for name in os.listdir(UPLOAD_ROOT):
            p = os.path.join(UPLOAD_ROOT, name)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)


@app.route("/")
def index():
    if not session.get("authed"):
        return redirect(url_for("login"))
    d = _ensure_session_dir()
    files = sorted(os.listdir(d)) if os.path.isdir(d) else []
    result_exists = os.path.exists(os.path.join(d, "结果.xlsx"))
    return render_template("workbench.html", files=files, result_exists=result_exists)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw != PASSWORD:
            return render_template("login.html", error="口令错误")
        # 新会话：清理旧上传，避免残留
        _clean_all_uploads()
        session.clear()
        session["authed"] = True
        session["sid"] = uuid.uuid4().hex
        os.makedirs(os.path.join(UPLOAD_ROOT, session["sid"]), exist_ok=True)
        return redirect(url_for("index"))
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    d = _session_dir()
    if d:
        shutil.rmtree(d, ignore_errors=True)
    session.clear()
    return redirect(url_for("login"))


@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("authed"):
        return redirect(url_for("login"))
    d = _ensure_session_dir()
    f = request.files.get("file")
    if not f or f.filename == "":
        flash("未选择文件")
        return redirect(url_for("index"))

    base = f.filename.lower()
    if not base.endswith(".xlsx"):
        flash("仅接受 .xlsx 文件")
        return redirect(url_for("index"))
    if base not in EXPECTED:
        flash("文件名不符，仅接受 材料1.xlsx 与 材料2.xlsx")
        return redirect(url_for("index"))

    target = os.path.join(d, base)  # 归一化为规范文件名
    f.save(target)
    flash(f"已上传：{f.filename}")
    return redirect(url_for("index"))


@app.route("/generate", methods=["POST"])
def generate():
    if not session.get("authed"):
        return redirect(url_for("login"))
    d = _ensure_session_dir()
    m1 = os.path.join(d, "材料1.xlsx")
    m2 = os.path.join(d, "材料2.xlsx")
    if not (os.path.exists(m1) and os.path.exists(m2)):
        flash("需上传 材料1.xlsx 与 材料2.xlsx 两个文件后才能生成")
        return redirect(url_for("index"))
    try:
        value = compute_payment(m1, m2)
    except ValueError as e:
        flash(f"生成失败：{e}")
        return redirect(url_for("index"))
    except Exception as e:  # noqa: BLE001
        flash(f"生成失败：{e}")
        return redirect(url_for("index"))
    build_result(os.path.join(d, "结果.xlsx"), value)
    flash(f"生成成功，货款 = {value}")
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    if not session.get("authed"):
        return redirect(url_for("login"))
    d = _ensure_session_dir()
    if os.path.isdir(d):
        for fn in os.listdir(d):
            try:
                os.remove(os.path.join(d, fn))
            except OSError:
                pass
    flash("已清空本次上传与成品")
    return redirect(url_for("index"))


@app.route("/download")
def download():
    if not session.get("authed"):
        return redirect(url_for("login"))
    d = _session_dir()
    path = os.path.join(d, "结果.xlsx") if d else None
    if not path or not os.path.exists(path):
        flash("暂无成品可下载")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name="结果.xlsx")


if __name__ == "__main__":
    # Render/云托管用 PORT；本地默认 5000。0.0.0.0 便于隧道与托管探活。
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="0.0.0.0", port=port)
