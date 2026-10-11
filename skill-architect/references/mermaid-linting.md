# Mermaid Diagram Clean Syntax & Linting Guide

Guidelines for generating clean, spec-compliant Mermaid diagrams that render reliably across GitHub, GitLab, VS Code, and browser renderers without syntax errors.

---

## 1. Top Mermaid Syntax Pitfalls

### Pitfall 1: Bare Double Quotes in Labels & Units
- **Problem**: Writing inches or quotes inside edge labels (e.g., `==|Arterial 48" Corridor|`) breaks Mermaid's lexer. The quote character switches parsing into string literal mode (`STR`), causing an unexpected token error.
- **Solution**: Use text units or hyphens:
  - ❌ `==|Arterial 48" Corridor|`
  - ✅ `==|Arterial 48-in Corridor|` or `==|Arterial 48 in Corridor|`
  - ✅ If quotes are required, use the HTML entity: `#quot;`

### Pitfall 2: Non-Standard Bidirectional Arrow Tokens
- **Problem**: `<==>` is not valid in standard Mermaid flowcharts.
- **Solution**:
  - For standard bidirectional links: use `<-->`
  - For directed thick arrows: use `==>` (one-way only)

### Pitfall 3: Trailing Semicolons
- **Problem**: Semicolons on `classDef` or styling lines (e.g., `classDef public fill:#eee,stroke:#333;`) cause strict parsers like `@probelabs/maid` to fail with `Redundant input, expecting EOF but found: ;`.
- **Solution**: Omit the trailing semicolon:
  - ❌ `classDef public fill:#eee,stroke:#333;`
  - ✅ `classDef public fill:#eee,stroke:#333`

### Pitfall 4: Unquoted Parentheses and Special Characters in Node Labels
- **Problem**: `Node[Living (Main)]` can conflict with shape syntax because `(` and `)` are stadium/circle delimiters.
- **Solution**: Always quote node labels that contain parentheses, brackets, or commas:
  - ❌ `Node[Living (Main)]`
  - ✅ `Node["Living (Main)"]`

---

## 2. Supported Diagram Types

Always begin the Mermaid fence with a recognized diagram keyword on the first line:
- `graph TD` / `graph LR` / `flowchart TD` / `flowchart LR`
- `sequenceDiagram`
- `stateDiagram` / `stateDiagram-v2`
- `classDiagram`
- `erDiagram`
- `gantt`
- `pie`
- `mindmap`
- `timeline`

---

## 3. Bundled Linting & Auto-Fix Utilities

`skill-architect` provides two layers of syntax enforcement:

### 1. `lint_mermaid.py`
Standalone CLI that scans Markdown files or `.mmd` files:
```bash
# Validate diagrams
python3 skill-architect/scripts/lint_mermaid.py <path-to-file-or-dir>

# Automatically fix common errors (quotes, semicolons, invalid arrows)
python3 skill-architect/scripts/lint_mermaid.py <path-to-file-or-dir> --fix
```

### 2. Modern CLI Validator (`@probelabs/maid`)
When Node/npx is available, `lint_mermaid.py` delegates to `@probelabs/maid`:
```bash
npx -y @probelabs/maid <markdown-file>
```
`maid` is a fast parser specifically tuned for AI-generated Mermaid code blocks, identifying unclosed quotes, broken arrows, and malformed styling within milliseconds without spinning up a headless browser.

### 3. Integrated in `validate_skill.py`
Whenever `python3 skill-architect/scripts/validate_skill.py <skill-dir>` runs, all Mermaid diagrams across `SKILL.md` and `references/` are automatically validated. Any syntax defect blocks validation until resolved.
