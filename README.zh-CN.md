# llm-cost-fixture-recorder

记录确定性的 LLM 成本 fixture，帮助团队在 CI 中捕获价格回归。

## 痛点

AI agents、MCP servers、成本控制、发布闸门和创作者工作流都在快速演进，但很多团队仍缺少小型、本地、可审计的工具：既能直接放进 CI，也能从终端运行，而且不需要把私有数据发送到第三方 SaaS。

## 为什么是现在

2026 年 6 月的趋势研究显示，MCP 作为 agent 集成标准、CLI-first coding agents、验证瓶颈、agent 安全控制、实用成本治理和内容自动化都在快速升温。本项目针对这些高信号运营缺口之一，提供一个小而可审计的工具。

## 安装

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -e .
```

除 Python 标准库外无需运行时依赖。

## 运行

```bash
python -m llm_cost_fixture_recorder examples/calls.csv --budget 0.05
python -m llm_cost_fixture_recorder examples/calls.csv --warn-budget 0.03 --budget 0.05
python -m llm_cost_fixture_recorder examples/calls.csv --prices-json prices.json --strict-models
```

可用 `--warn-budget` 先在 CI 中输出软预算提醒，再用硬性的 `--budget` 控制失败。

自定义价格文件可以把 CI 中使用的模型价格固定下来，适合供应商价格变化或内部网关别名不在内置表中的场景：

```json
{
  "my-model": {"input_per_million": "0.25", "output_per_million": "1.00"}
}
```

## 示例输出

对 `examples/` 中的文件运行上面的命令，可以得到适合演示、Issue 报告和 CI 日志的确定性输出。

## 自检

```bash
python -m unittest discover -s tests
```

## 路线图

- 增加更丰富的机器可读输出，用于 CI annotations。
- 增加更多来自 agent 和 MCP 工作流的真实 fixture。
- 为没有 Python 环境的用户发布打包二进制。
- 增加用于 pull-request 自动化的 GitHub Action 示例。

## License

MIT
