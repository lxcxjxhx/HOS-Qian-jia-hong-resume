# fix(tools): 回归脚本先创建 artifacts 父目录再分配输出

**PR 链接**: [NaiboWang/FoldMobileGym#1](https://github.com/NaiboWang/FoldMobileGym/pull/1)
**状态**: Merged
**合并时间**: 2026-11-28T03:01:25Z
**创建时间**: 2026-11-19T00:34:27Z
**作者**: [lxcxjxhx](https://github.com/lxcxjxhx)

## 统计信息

- **新增行数**: 13
- **删除行数**: 1
- **变更文件数**: 10
- **提交数**: 1

## 变更文件

| 文件 | 状态 | 新增 | 删除 |
|------|------|------|------|
| `.github/workflows/lightweight-checks.yml` | MOD | +2 | -0 |
| `tools/reviews/review_calculator_expression.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_file_preview_sources.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_file_search_identity.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_file_thumbnail_sources.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_file_uri_cache.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_meituan_fulfillment.mjs` | MOD | +3 | -1 |
| `tools/reviews/review_meituan_summary.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_sms_context_back.mjs` | MOD | +1 | -0 |
| `tools/reviews/review_sms_long_press.mjs` | MOD | +1 | -0 |

## PR 描述

## 问题

`tools/reviews/` 下有 9 个回归脚本直接对 `<repo>/artifacts/<name>-` 调用 `fs.mkdtempSync`，没有先建立 `artifacts/` 父目录：

```js
const output = fs.mkdtempSync(path.join(root, 'artifacts/sms-long-press-'));
```

`artifacts/` 被 `.gitignore` 的 `**/artifacts/` 忽略，因此**新 checkout 上这个父目录并不存在**，这些脚本在创建输出目录的第一步就抛：

```
ENOENT: no such file or directory, mkdtemp '<repo>rtifacts\sms-long-press-XXXXXX'
```

也就是说，按 `tools/README.md` 的说法首次运行回归脚本会直接崩；只有先前跑过别的诊断脚本、把 `artifacts/` 建出来之后才会“碰巧能跑”。

仓库自己的 `tools/reviews/test_review_bootstrap.mjs` 已经把这个当成硬约定：文件的**第一行**注释就是 `Read-only source contract. Do not create artifacts/ and conceal a fresh-checkout prerequisite.`，断言消息是 `A clean receiver must not depend on a prior diagnostic having made artifacts/`。当前它有 9 条失败。

## 改动

- 9 个脚本在分配输出之前补一行父目录引导（其余逻辑一字未动）：

  ```js
  fs.mkdirSync(path.join(root, 'artifacts'), { recursive: true });
  ```

  `review_calculator_expression` / `review_file_preview_sources` / `review_file_search_identity` / `review_file_thumbnail_sources` / `review_file_uri_cache` / `review_meituan_fulfillment` / `review_meituan_summary` / `review_sms_context_back` / `review_sms_long_press`
- `review_meituan_fulfillment.mjs` 原来把 `root`、`require`、`puppeteer`、`output` 挤在同一行，无法在 `mkdtempSync` 之前插入引导语句，故把它拆成三行，行为不变。
- `.github/workflows/lightweight-checks.yml` 增加一步 `node --test tools/reviews/test_review_bootstrap.mjs`：这条约定本来就有断言，但没有任何 CI 步骤执行它，所以 9 个脚本静默漂了。该步骤只读源文件、不需要浏览器和 `node_modules`（约 0.1 秒），符合工作流本身声明的 “lightweight source checks” 定位。

## 验证

**1. 仓库自带断言，修前 / 修后**

```
$ node --test tools/reviews/test_review_bootstrap.mjs
before: tests 48 | pass 39 | fail 9
after:  tests 48 | pass 48 | fail 0
```

**2. A/B 复现：把每个脚本里的两条文件系统语句按源码顺序回放到一个空目录上**

```
review_calculator_expression.mjs       base=ENOENT  fixed=allocated
review_file_preview_sources.mjs        base=ENOENT  fixed=allocated
review_file_search_identity.mjs        base=ENOENT  fixed=allocated
review_file_thumbnail_sources.mjs      base=ENOENT  fixed=allocated
review_file_uri_cache.mjs              base=ENOENT  fixed=allocated
review_meituan_fulfillment.mjs         base=ENOENT  fixed=allocated
review_meituan_summary.mjs             base=ENOENT  fixed=allocated
review_sms_context_back.mjs            base=ENOENT  fixed=allocated
review_sms_long_press.mjs              base=ENOENT  fixed=allocated
```

（`base` 取 `git show HEAD:tools/reviews/<file>`，`fixed` 取本分支工作副本；`root` 用 `fs.mkdtempSync(os.tmpdir())` 代表没有 `artifacts/` 的新 checkout。）

**3. 其它**

- `node --check` 通过 9 个改动文件；
- `lightweight-checks.yml` 可被 YAML 解析，`source-checks` 任务步骤顺序正常；
- 残留扫描：`tools/reviews` 下不再有“用了 `mkdtempSync` 但没建 `artifacts/`”的脚本（0 个）。

## 没有做的事

- **没有跑这几个脚本的浏览器端到端回归**：它们需要先启动模拟器、装好媒体包和前端依赖。我验证的是“脚本能在干净 checkout 上走到创建输出目录这一步”，这正好是这次缺陷的边界；脚本之后的浏览器断言不在本次改动范围内。
- 另外发现两个**与本 PR 无关**的独立问题，没有混进来，需要的话我另开 issue：
  1. `tools/release/test_reconstruction_workflow.mjs` 通过 `createRequire(foldmobilegym/package.json)` 加载 `js-yaml`，但 `foldmobilegym/package.json` 并未声明该依赖，干净 checkout 上必然 `MODULE_NOT_FOUND`；
  2. 同一个测试断言 `.github/workflows/reconstruction.yml`，而仓库里现在只有 `.github/workflows/lightweight-checks.yml`。


## 相关链接

- **源仓库**: [NaiboWang/FoldMobileGym](https://github.com/NaiboWang/FoldMobileGym)
- **PR 链接**: https://github.com/NaiboWang/FoldMobileGym/pull/1
- **Diff**: https://github.com/NaiboWang/FoldMobileGym/pull/1.diff

---
*Auto-generated at 2026-11-28 06:09:23 UTC*
