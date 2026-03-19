# shixiseng-job-csv

从[实习僧](https://www.shixiseng.com)爬取招聘信息并导出为 CSV 文件的 Claude Skill。

## 功能

- 搜索关键词，批量抓取职位详情
- 翻页收集（默认 3 页）
- 导出字段：职位名、公司、薪资、城市、学历、上班时间、实习时长、福利、截止日期、工作地点、公司简介、职位描述、原始链接

## 前置依赖

- [agent-browser](https://github.com/anthropics/agent-browser) - 浏览器自动化工具，需安装在 PATH 中
- Python 3.x - 用于运行导出脚本

## 安装方式

### 方式一：直接安装 .skill 文件（推荐）

1. 下载 `shixiseng-job-csv.skill`
2. 放到 `~/.claude/skills/` 目录下

```bash
# 或通过 Claude Code 安装
mkdir -p ~/.claude/skills
cp shixiseng-job-csv.skill ~/.claude/skills/
```

### 方式二：从源码安装

```bash
git clone https://github.com/s0meb0dy3/shixiseng-job-csv.git ~/.claude/skills/shixiseng-job-csv
```

## 使用方法

在 Claude Code 中触发：

```
帮我爬取实习僧上"LLM算法"相关的实习职位，导出为 CSV
```

Claude 会自动：
1. 打开实习僧搜索页
2. 收集职位详情链接
3. 翻页收集（默认 3 页）
4. 提取每个职位的详细信息
5. 生成 CSV 文件

## 导出字段说明

| 字段 | 说明 |
|------|------|
| title | 职位名称 |
| company | 公司名称 |
| refresh_time | 更新时间 |
| salary | 薪资 |
| city | 城市 |
| education | 学历要求 |
| attendance | 上班时间 |
| duration | 实习时长 |
| benefits | 福利待遇 |
| deadline | 截止日期 |
| location | 工作地点 |
| company_description | 公司简介 |
| job_description | 职位描述 |
| url | 原始链接 |

## 手动使用导出脚本

如果已有职位链接清单（manifest.json），可手动运行脚本：

```bash
python3 scripts/export_shixiseng_jobs_csv.py ./manifest.json --output ./jobs.csv
```

## 注意事项

- 默认抓取前 3 页，如需指定页数请在请求时说明
- 部分字段可能为空，CSV 中会留空
- 请勿过于频繁地爬取，以免对网站造成负担
