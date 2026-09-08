# stop-signals-authoring

分类: 偏好（BETTER）

一轮活结束时，frago 要判断这一轮该不该就这么结束。判断分两层：先过一道不花钱的本地闸门，命中了才去问 LightAgent。闸门看什么，写在 `~/.frago/hook/stop-signals.json`，改完下一轮生效，不用重建引擎。

## 闸门在干什么

问一次模型要三到六秒，而这个等待落在你已经读完回答之后，是看得见的空转。所以绝大多数轮次必须零成本放行：实测这台机器上两千多轮真实对话，七成的轮次连工具都没调，再两成调了但闸门什么都没看见，只有约 8% 会走到模型那一步。

闸门只决定「这一轮值不值得问」，永远不自己拦人。误判一次的代价只是多问一次模型；而漏掉一类信号，那类轮次就永远到不了模型面前——今天想加的判据如果在闸门里没有对应信号，写进说明书也是白写。

## 一条信号长什么样

```json
{
  "name": "admitted",
  "describe": "收尾时自陈有东西没验证",
  "closing_text_regex": "没跑过|未验证|只跑了"
}
```

| 字段 | 作用 |
|---|---|
| `name` | 信号名，出现在诊断输出里 |
| `describe` | 命中后交给模型的那句话。模型看的是这句，不是正则 |
| `describe_when_cleared` | 命中、但 `cleared_by_tool_regex` 也命中时改用这句 |
| `closing_text_regex` | 匹配 agent 收尾说的那段话 |
| `user_text_regex` | 匹配这个窗口里用户自己说过的话 |
| `tool_name_in` + `tool_arg_regex` | 匹配某类工具调用：工具名在列表里，且参数匹配 |
| `cleared_by_tool_regex` | 本轮任一工具调用匹配它，就换用 `describe_when_cleared` |

几个条件之间是「任一命中即命中」。`cleared_by_tool_regex` 不会让信号消失，只换措辞——「改了代码没跑检查」和「改了代码跑过检查」都该到模型面前，让它自己判断跑的那个检查够不够。

文件里另有一个 `discard_reason_regex`：LightAgent 给出的拦截理由里出现这些措辞就整条丢弃。那句理由会留在会话记录里影响后面每一轮，不只是这一轮，所以「别问用户」这类话一个字都不能放进去。

## 写正则的分寸

第二人称是关键。`这个函数错了` 说的是代码，`你错了` 说的才是 agent——不加这个区分，每一轮调试都会撞上闸门，白问一次模型。

同理，宁可窄不要宽：闸门宽了不会拦错人，但会让每一轮都多等三秒。

## 改完怎么验

```bash
frago-core --audit-rules      # 确认引擎确实在从这个文件读
```

想看某一轮会不会被拦，把那一轮的会话记录喂给诊断入口：

```bash
echo '{"session_id":"x","hook_event_name":"Stop","transcript_path":"<会话记录.jsonl>"}' \
  | frago-core --stop-check
```

它会依次打印闸门看到了哪些信号、第一遍判读说什么、否决那一环放不放行。

## 出错时会怎样

整个文件读不出来、JSON 解析不了、某一条正则编译不过——对应部分当作不存在，其余照常，原因记在 `~/.frago/hook-review.log`。一条正则写坏只影响它自己，不会带倒别的信号，更不会让 hook 崩掉。

## 下次召回入口

```bash
frago book stop-signals-authoring
```
