---
name: dev-browser
description: Browser automation with persistent page state. Use when users ask to navigate websites, fill forms, take screenshots, extract web data, test web apps, or automate browser workflows. Trigger phrases include "go to [url]", "click on", "fill out the form", "take a screenshot", "scrape", "automate", "test the website", "log into", or any browser interaction request.
---

# Dev Browser Skill

Browser automation that maintains page state across script executions. Write small, focused scripts to accomplish tasks incrementally. Once you've proven out part of a workflow and there is repeated work to be done, you can write a script to do the repeated work in a single execution.

## Choosing Your Approach

- **Local/source-available sites**: Read the source code first to write selectors directly
- **Unknown page layouts**: Use `getAISnapshot()` to discover elements and `selectSnapshotRef()` to interact with them
- **Visual feedback**: Take screenshots to see what the user sees

## Setup

**IMPORTANT: Always use Standalone Mode for browser automation.** Extension Mode is rarely needed.

### Standalone Mode (Default)

Launches a Chromium browser with a **persistent profile**. Login sessions, cookies, and local storage persist across browser restarts.

**Start the server:**

```bash
~/.config/amp/skills/dev-browser/server.sh &
```

Wait for the `Ready` message before running scripts. Add `--headless` flag if user requests headless mode.

**Key points:**
- Profile stored at `~/.config/amp/skills/dev-browser/profiles/browser-data`
- Once logged in, future sessions remain authenticated
- Use this mode for local dev testing with auth (localhost:3000, etc.)

### Extension Mode (Rarely Used)

Connects to user's existing Chrome browser. **Only use when explicitly requested** - the user must install a browser extension.

```bash
cd ~/.config/amp/skills/dev-browser && npm i && npm run start-extension &
```

Download link: https://github.com/SawyerHood/dev-browser/releases

## Writing Scripts

> **Run all scripts from the dev-browser directory.** The `@/` import alias requires this directory's config.

Execute scripts inline using heredocs:

```bash
cd ~/.config/amp/skills/dev-browser && npx tsx <<'EOF'
import { connect, waitForPageLoad } from "@/client.js";

const client = await connect();
const page = await client.page("example"); // descriptive name like "cnn-homepage"
await page.setViewportSize({ width: 1280, height: 800 });

await page.goto("https://example.com");
await waitForPageLoad(page);

console.log({ title: await page.title(), url: page.url() });
await client.disconnect();
EOF
```

**Write to `tmp/` files only when** the script needs reuse, is complex, or user explicitly requests it.

### Key Principles

1. **Small scripts**: Each script does ONE thing (navigate, click, fill, check)
2. **Evaluate state**: Log/return state at the end to decide next steps
3. **Descriptive page names**: Use `"checkout"`, `"login"`, not `"main"`
4. **Disconnect to exit**: `await client.disconnect()` - pages persist on server
5. **Plain JS in evaluate**: `page.evaluate()` runs in browser - no TypeScript syntax

## Workflow Loop

Follow this pattern for complex tasks:

1. **Write a script** to perform one action
2. **Run it** and observe the output
3. **Evaluate** - did it work? What's the current state?
4. **Decide** - is the task complete or do we need another script?
5. **Repeat** until task is done

### No TypeScript in Browser Context

Code passed to `page.evaluate()` runs in the browser, which doesn't understand TypeScript:

```typescript
// ✅ Correct: plain JavaScript
const text = await page.evaluate(() => {
  return document.body.innerText;
});

// ❌ Wrong: TypeScript syntax will fail at runtime
const text = await page.evaluate(() => {
  const el: HTMLElement = document.body; // Type annotation breaks in browser!
  return el.innerText;
});
```

## Scraping Data

For scraping large datasets, intercept and replay network requests rather than scrolling the DOM. See [references/scraping.md](references/scraping.md) for the complete guide covering request capture, schema discovery, and paginated API replay.

## Client API

```typescript
const client = await connect();
const page = await client.page("name"); // Get or create named page
const pages = await client.list(); // List all page names
await client.close("name"); // Close a page
await client.disconnect(); // Disconnect (pages persist)

// ARIA Snapshot methods
const snapshot = await client.getAISnapshot("name"); // Get accessibility tree
const element = await client.selectSnapshotRef("name", "e5"); // Get element by ref

// Token-efficient content extraction (NEW)
const outline = await client.getOutline("name"); // Tree of all elements
const interactive = await client.getInteractiveOutline("name"); // Only interactive elements
const text = await client.getVisibleText("name"); // Visible text only
```

The `page` object is a standard Playwright Page.

### Token-Efficient Content Extraction

These methods provide structured, concise output that uses far fewer tokens than screenshots or full ARIA snapshots:

**`getOutline(name, options?)`** - Returns a tree structure of DOM elements:
```typescript
const outline = await client.getOutline("mypage", { maxDepth: 4 });
// Output:
// body
//   header#main-header
//     nav [role=navigation]
//       a "Home" [href=/]
//       a "Products" [href=/products]
//   main
//     div.product-list ... (24)
```
- Shows tag names, IDs, classes, and relevant attributes
- Collapses repeated siblings (shows `(×5)` instead of repeating)
- Limits depth to reduce noise (default: 6)
- Options: `{ selector?: string, maxDepth?: number }`

**`getInteractiveOutline(name, selector?)`** - Returns only interactive elements and landmarks:
```typescript
const interactive = await client.getInteractiveOutline("mypage");
// Output:
// header
//   a "Home" [href=/]
//   a "Products" [href=/products]
// main
//   button "Add to Cart"
//   input [type=text] [placeholder="Search"]
// footer
//   a "Contact" [href=/contact]
```
- Best for understanding available actions
- Automatically prunes non-interactive containers
- Shows landmarks (header, nav, main, footer, form, etc.)

**`getVisibleText(name, options?)`** - Returns only visible text, filtering hidden elements:
```typescript
const text = await client.getVisibleText("mypage", { limit: 5000 });
```
- Excludes `display: none`, `visibility: hidden`, `opacity: 0`
- Respects parent visibility (hidden parent = hidden children)
- Preserves block structure with newlines
- Options: `{ selector?: string, limit?: number }`

**When to use which:**
| Method | Use case | Token efficiency |
|--------|----------|------------------|
| `getInteractiveOutline()` | Discover clickable elements | ⭐⭐⭐ Most efficient |
| `getOutline()` | Understand page structure | ⭐⭐ Very efficient |
| `getVisibleText()` | Extract readable content | ⭐⭐ Very efficient |
| `getAISnapshot()` | Need ref-based clicking | ⭐ Full ARIA tree |
| `screenshot()` | Visual debugging | Uses vision tokens |

## Waiting

```typescript
import { waitForPageLoad } from "@/client.js";

await waitForPageLoad(page); // After navigation
await page.waitForSelector(".results"); // For specific elements
await page.waitForURL("**/success"); // For specific URL
```

## Inspecting Page State

### Screenshots

```typescript
await page.screenshot({ path: "tmp/screenshot.png" });
await page.screenshot({ path: "tmp/full.png", fullPage: true });
```

### ARIA Snapshot (Element Discovery)

Use `getAISnapshot()` to discover page elements. Returns YAML-formatted accessibility tree:

```yaml
- banner:
  - link "Hacker News" [ref=e1]
  - navigation:
    - link "new" [ref=e2]
- main:
  - list:
    - listitem:
      - link "Article Title" [ref=e8]
      - link "328 comments" [ref=e9]
- contentinfo:
  - textbox [ref=e10]
    - /placeholder: "Search"
```

**Interpreting refs:**

- `[ref=eN]` - Element reference for interaction (visible, clickable elements only)
- `[checked]`, `[disabled]`, `[expanded]` - Element states
- `[level=N]` - Heading level
- `/url:`, `/placeholder:` - Element properties

**Interacting with refs:**

```typescript
const snapshot = await client.getAISnapshot("hackernews");
console.log(snapshot); // Find the ref you need

const element = await client.selectSnapshotRef("hackernews", "e2");
await element.click();
```

## Error Recovery

Page state persists after failures. Debug with:

```bash
cd ~/.config/amp/skills/dev-browser && npx tsx <<'EOF'
import { connect } from "@/client.js";

const client = await connect();
const page = await client.page("hackernews");

await page.screenshot({ path: "tmp/debug.png" });
console.log({
  url: page.url(),
  title: await page.title(),
  bodyText: await page.textContent("body").then((t) => t?.slice(0, 200)),
});

await client.disconnect();
EOF
```
