# UPThink

一个面向 AI 助手的中文思维训练 skill：根据指定 B 站视频的字幕和公开资料出题，在作答后对照作者的推理过程，并给出可核验的视频时间点。

默认示例是「有何高见9527」，也可以指定其他 UP 主或视频。本项目是独立学习工具，与该 UP 主及哔哩哔哩无关联。

## 使用

将 `skills/upthink` 文件夹安装到你的 AI 助手支持的 skill 目录。例如，Codex 用户可将它复制到 `~/.codex/skills/upthink`，然后重启或重新加载 skill。使用方式和可用的浏览、登录工具取决于助手环境。

示例：

> 用这个视频的字幕给我出思维训练题，先不要透露视频结论。  
> 我回答了前两题，请对照视频批改并给出时间点。

提供视频链接和**带时间戳的字幕**可以提高可靠性。需要登录或付费权限的内容，仅在你已经有权访问时使用；本项目不提供账号、Cookie、付费内容或绕过访问限制的功能。

## 本地字幕辅助工具

需要 Python 3.9 或更高版本，无需额外 Python 包。脚本不会访问网络或保存输出文件：

```bash
python skills/upthink/scripts/subtitle_tools.py inspect subtitle.json --duration 600
python skills/upthink/scripts/subtitle_tools.py find subtitle.json "需要查找的内容"
python skills/upthink/scripts/subtitle_tools.py reconcile 原始字幕.txt 标点建议.txt
```

字幕 JSON 使用 `body` 数组，每项包含数字型 `from`、`to` 和文本 `content`。`find` 支持跨字幕片段查找；字幕结尾与视频时长的差值只是提示，并不单独证明字幕完整或缺失。标点处理保留所有原始字符，只采纳对齐后纯标点或空白的插入。

本仓库**不自动抓取 B 站字幕，也不调用外部标点 API**。字幕获取取决于助手环境；若使用第三方模型处理字幕，先确认内容可以发送给该服务。不要将私有字幕、浏览器配置、Cookie 或 API 密钥提交到仓库。

## 设计原则

- 出题时不泄露作者结论；答题后对照作者的推理并附可靠时间点。
- 作者的观点是学习对象，事实需要独立核实；合理分歧不默认判错。
- 原始字幕与时间戳是依据，不从简介猜测视频内容。

## 验证

```bash
python -m unittest discover -s tests -v
```
