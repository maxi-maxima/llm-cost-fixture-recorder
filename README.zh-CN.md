# llm-cost-fixture-recorder

记录确定性的 LLM 成本样本，帮助团队在 CI 中发现价格回归。

## 解决的痛点

AI Agent、MCP Server、成本控制、发布门禁和内容自动化都在快速发展，但团队常常缺少可以本地运行、容易审计、能放进 CI 的小工具，导致验证、权限、成本和交付风险只能靠人工检查。

## 为什么现在值得做

2026 年 6 月的趋势调研显示，MCP 标准化、CLI-first 编程 Agent、验证瓶颈、安全控制、成本治理和内容自动化都在开发者社区持续升温。本项目用最小可运行工具切入其中一个明确问题。

## 安装

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -e .
```

运行时只依赖 Python 标准库。

## 运行

```bash
python -m llm_cost_fixture_recorder examples/calls.csv --budget 0.05
python -m llm_cost_fixture_recorder examples/calls.csv --prices-json prices.json --strict-models
```

自定义价格文件可以把 CI 中使用的模型价格固定下来，适合供应商价格变化或内部网关别名不在内置表中的场景：

```json
{
  "my-model": {"input_per_million": "0.25", "output_per_million": "1.00"}
}
```

## 示例

`examples/` 目录包含可直接运行的输入文件。执行上面的命令会输出确定性的终端结果，适合演示、CI 和问题复现。

## 自检

```bash
python -m unittest discover -s tests
```

## 路线图

- 增加更丰富的 CI 注释输出。
- 补充来自真实 Agent 与 MCP 工作流的样例。
- 发布免 Python 环境的二进制版本。
- 增加 GitHub Action 集成示例。

## 许可证

MIT
