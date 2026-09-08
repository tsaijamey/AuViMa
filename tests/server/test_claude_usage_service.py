"""订阅额度探测：读的是 Claude Code 说给人听的那几行字。

这里钉的是解析本身。风险不在我们的代码会变，而在对方的措辞会变——`/usage` 的输出是给
人读的正文，不是接口。所以三档各钉一条：型号那一档的名字跟着账号走（Fable / Opus /
…），不能写死；用 API key 而不是订阅的机器根本不报百分比，那种情况必须落到「答不出」，
而不是画三根空条子。
"""

from __future__ import annotations

from frago.server.services.claude_usage_service import ClaudeUsageService

SUBSCRIPTION_OUTPUT = """You are currently using your subscription to power your Claude Code usage

Current session: 8% used · resets Sep 8 at 9:50pm (Asia/Shanghai)
Current week (all models): 62% used · resets Sep 12 at 8pm (Asia/Shanghai)
Current week (Fable): 94% used · resets Sep 12 at 8pm (Asia/Shanghai)

What's contributing to your limits usage?
Last 24h · 2526 requests · 72 sessions
"""


def test_parses_three_buckets() -> None:
    usage = ClaudeUsageService._parse(SUBSCRIPTION_OUTPUT)

    assert usage["available"] is True
    assert usage["session"] == {
        "percent": 8,
        "resets_at": "Sep 8 at 9:50pm (Asia/Shanghai)",
    }
    assert usage["week_all"]["percent"] == 62
    assert usage["week_model"] == {
        "label": "Fable",
        "percent": 94,
        "resets_at": "Sep 12 at 8pm (Asia/Shanghai)",
    }
    assert usage["error"] is None


def test_model_bucket_keeps_whatever_model_the_account_is_on() -> None:
    usage = ClaudeUsageService._parse("Current week (Opus): 3% used")

    assert usage["week_model"] == {"label": "Opus", "percent": 3, "resets_at": None}
    # 「all models」那一行不许被型号这条规则吃掉，否则两档会打架。
    assert usage["week_all"] is None


def test_api_key_machine_reports_unavailable() -> None:
    usage = ClaudeUsageService._parse("Total cost: $0.0000\nTotal duration (API): 0s")

    assert usage["available"] is False
    assert usage["error"] == "no-subscription-usage"
    assert usage["session"] is None


def test_a_percentage_without_a_reset_time_still_counts() -> None:
    usage = ClaudeUsageService._parse("Current session: 41% used")

    assert usage["available"] is True
    assert usage["session"] == {"percent": 41, "resets_at": None}
