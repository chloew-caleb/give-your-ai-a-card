"""钥匙投递口 · 卡片那三格（最小示例）

用法：把 put_card() 挂到你自己后端的一个 POST 接口上，**接口必须在登录之后**。
人类在网页上一格一格贴：card_number / card_exp / card_cvv。
- 只往里写，不提供读接口
- 文件权限 600，只有 AI 那一侧的进程能读
- 回执只报尾四位；不写日志、不打印、不进任何命令行参数
"""
import json
import os
import re
from datetime import datetime

CARD = os.path.expanduser("~/secrets/card.json")   # 改成你自己的路径


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
    return total % 10 == 0


def _write_600(path, obj):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def put_card(name: str, value: str) -> dict:
    v = re.sub(r"[\s-]+", "", str(value or ""))
    if name == "card_number":
        if not re.fullmatch(r"\d{15,16}", v) or not _luhn(v):
            return {"ok": False, "error": "卡号对不上，再对一遍"}
        key, note = "number", f"卡号放好了（尾号 {v[-4:]}）"
    elif name == "card_exp":
        m = re.fullmatch(r"(\d{1,2})/?(\d{2}|\d{4})", v)
        if not m or not 1 <= int(m.group(1)) <= 12:
            return {"ok": False, "error": "有效期写成 MM/YY"}
        v, key, note = f"{int(m.group(1)):02d}/{m.group(2)[-2:]}", "exp", "有效期放好了"
    elif name == "card_cvv":
        if not re.fullmatch(r"\d{3,4}", v):
            return {"ok": False, "error": "背面那串是 3 位数字"}
        key, note = "cvv", "背面三位放好了"
    else:
        return {"ok": False, "error": "没有这一格"}
    try:
        card = json.load(open(CARD, encoding="utf-8"))
    except Exception:
        card = {}
    card[key] = v
    card["updated"] = datetime.now().isoformat(timespec="seconds")
    _write_600(CARD, card)
    return {"ok": True, "note": note}


if __name__ == "__main__":
    # 自测（测试卡号，不是真卡）
    CARD = "/tmp/card_selftest.json"
    print(put_card("card_number", "4111 1111 1111 1111"))
    print(put_card("card_number", "1234"))
    print(put_card("card_exp", "9/2030"))
    print(put_card("card_cvv", "123"))
    os.remove(CARD)
