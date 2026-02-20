import { chromium, type Browser, type Page, type ElementHandle } from "playwright";
import type {
  GetPageRequest,
  GetPageResponse,
  ListPagesResponse,
  ServerInfoResponse,
} from "./types";
import { getSnapshotScript } from "./snapshot/browser-script";

/**
 * Options for waiting for page load
 */
export interface WaitForPageLoadOptions {
  /** Maximum time to wait in ms (default: 10000) */
  timeout?: number;
  /** How often to check page state in ms (default: 50) */
  pollInterval?: number;
  /** Minimum time to wait even if page appears ready in ms (default: 100) */
  minimumWait?: number;
  /** Wait for network to be idle (no pending requests) (default: true) */
  waitForNetworkIdle?: boolean;
}

/**
 * Result of waiting for page load
 */
export interface WaitForPageLoadResult {
  /** Whether the page is considered loaded */
  success: boolean;
  /** Document ready state when finished */
  readyState: string;
  /** Number of pending network requests when finished */
  pendingRequests: number;
  /** Time spent waiting in ms */
  waitTimeMs: number;
  /** Whether timeout was reached */
  timedOut: boolean;
}

interface PageLoadState {
  documentReadyState: string;
  documentLoading: boolean;
  pendingRequests: PendingRequest[];
}

interface PendingRequest {
  url: string;
  loadingDurationMs: number;
  resourceType: string;
}

/**
 * Wait for a page to finish loading using document.readyState and performance API.
 *
 * Uses browser-use's approach of:
 * - Checking document.readyState for 'complete'
 * - Monitoring pending network requests via Performance API
 * - Filtering out ads, tracking, and non-critical resources
 * - Graceful timeout handling (continues even if timeout reached)
 */
export async function waitForPageLoad(
  page: Page,
  options: WaitForPageLoadOptions = {}
): Promise<WaitForPageLoadResult> {
  const {
    timeout = 10000,
    pollInterval = 50,
    minimumWait = 100,
    waitForNetworkIdle = true,
  } = options;

  const startTime = Date.now();
  let lastState: PageLoadState | null = null;

  // Wait minimum time first
  if (minimumWait > 0) {
    await new Promise((resolve) => setTimeout(resolve, minimumWait));
  }

  // Poll until ready or timeout
  while (Date.now() - startTime < timeout) {
    try {
      lastState = await getPageLoadState(page);

      // Check if document is complete
      const documentReady = lastState.documentReadyState === "complete";

      // Check if network is idle (no pending critical requests)
      const networkIdle = !waitForNetworkIdle || lastState.pendingRequests.length === 0;

      if (documentReady && networkIdle) {
        return {
          success: true,
          readyState: lastState.documentReadyState,
          pendingRequests: lastState.pendingRequests.length,
          waitTimeMs: Date.now() - startTime,
          timedOut: false,
        };
      }
    } catch {
      // Page may be navigating, continue polling
    }

    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  // Timeout reached - return current state
  return {
    success: false,
    readyState: lastState?.documentReadyState ?? "unknown",
    pendingRequests: lastState?.pendingRequests.length ?? 0,
    waitTimeMs: Date.now() - startTime,
    timedOut: true,
  };
}

/**
 * Get the current page load state including document ready state and pending requests.
 * Filters out ads, tracking, and non-critical resources that shouldn't block loading.
 */
async function getPageLoadState(page: Page): Promise<PageLoadState> {
  const result = await page.evaluate(() => {
    // Access browser globals via globalThis for TypeScript compatibility
    /* eslint-disable @typescript-eslint/no-explicit-any */
    const g = globalThis as { document?: any; performance?: any };
    /* eslint-enable @typescript-eslint/no-explicit-any */
    const perf = g.performance!;
    const doc = g.document!;

    const now = perf.now();
    const resources = perf.getEntriesByType("resource");
    const pending: Array<{ url: string; loadingDurationMs: number; resourceType: string }> = [];

    // Common ad/tracking domains and patterns to filter out
    const adPatterns = [
      "doubleclick.net",
      "googlesyndication.com",
      "googletagmanager.com",
      "google-analytics.com",
      "facebook.net",
      "connect.facebook.net",
      "analytics",
      "ads",
      "tracking",
      "pixel",
      "hotjar.com",
      "clarity.ms",
      "mixpanel.com",
      "segment.com",
      "newrelic.com",
      "nr-data.net",
      "/tracker/",
      "/collector/",
      "/beacon/",
      "/telemetry/",
      "/log/",
      "/events/",
      "/track.",
      "/metrics/",
    ];

    // Non-critical resource types
    const nonCriticalTypes = ["img", "image", "icon", "font"];

    for (const entry of resources) {
      // Resources with responseEnd === 0 are still loading
      if (entry.responseEnd === 0) {
        const url = entry.name;

        // Filter out ads and tracking
        const isAd = adPatterns.some((pattern) => url.includes(pattern));
        if (isAd) continue;

        // Filter out data: URLs and very long URLs
        if (url.startsWith("data:") || url.length > 500) continue;

        const loadingDuration = now - entry.startTime;

        // Skip requests loading > 10 seconds (likely stuck/polling)
        if (loadingDuration > 10000) continue;

        const resourceType = entry.initiatorType || "unknown";

        // Filter out non-critical resources loading > 3 seconds
        if (nonCriticalTypes.includes(resourceType) && loadingDuration > 3000) continue;

        // Filter out image URLs even if type is unknown
        const isImageUrl = /\.(jpg|jpeg|png|gif|webp|svg|ico)(\?|$)/i.test(url);
        if (isImageUrl && loadingDuration > 3000) continue;

        pending.push({
          url,
          loadingDurationMs: Math.round(loadingDuration),
          resourceType,
        });
      }
    }

    return {
      documentReadyState: doc.readyState,
      documentLoading: doc.readyState !== "complete",
      pendingRequests: pending,
    };
  });

  return result;
}

/** Server mode information */
export interface ServerInfo {
  wsEndpoint: string;
  mode: "launch" | "extension";
  extensionConnected?: boolean;
}

/**
 * Options for getOutline
 */
export interface OutlineOptions {
  /** CSS selector for the root element (default: "body") */
  selector?: string;
  /** Maximum depth to traverse (default: 6) */
  maxDepth?: number;
}

/**
 * Options for getVisibleText
 */
export interface VisibleTextOptions {
  /** CSS selector for the root element (default: "body") */
  selector?: string;
  /** Maximum characters to return (default: 10000) */
  limit?: number;
}

export interface DevBrowserClient {
  page: (name: string) => Promise<Page>;
  list: () => Promise<string[]>;
  close: (name: string) => Promise<void>;
  disconnect: () => Promise<void>;
  /**
   * Get AI-friendly ARIA snapshot for a page.
   * Returns YAML format with refs like [ref=e1], [ref=e2].
   * Refs are stored on window.__devBrowserRefs for cross-connection persistence.
   */
  getAISnapshot: (name: string) => Promise<string>;
  /**
   * Get an element handle by its ref from the last getAISnapshot call.
   * Refs persist across Playwright connections.
   */
  selectSnapshotRef: (name: string, ref: string) => Promise<ElementHandle | null>;
  /**
   * Get server information including mode and extension connection status.
   */
  getServerInfo: () => Promise<ServerInfo>;
  /**
   * Get a token-efficient tree outline of page elements.
   * Shows tag names, IDs, classes, and relevant attributes.
   * Collapses repeated siblings and limits depth for efficiency.
   */
  getOutline: (name: string, options?: OutlineOptions) => Promise<string>;
  /**
   * Get a token-efficient outline showing only interactive elements and landmarks.
   * Best for understanding page structure and available actions.
   */
  getInteractiveOutline: (name: string, selector?: string) => Promise<string>;
  /**
   * Get visible text from page, filtering out hidden elements.
   * Uses computed styles to exclude display:none, visibility:hidden, opacity:0.
   */
  getVisibleText: (name: string, options?: VisibleTextOptions) => Promise<string>;
}

export async function connect(serverUrl = "http://localhost:9222"): Promise<DevBrowserClient> {
  let browser: Browser | null = null;
  let wsEndpoint: string | null = null;
  let connectingPromise: Promise<Browser> | null = null;

  async function ensureConnected(): Promise<Browser> {
    // Return existing connection if still active
    if (browser && browser.isConnected()) {
      return browser;
    }

    // If already connecting, wait for that connection (prevents race condition)
    if (connectingPromise) {
      return connectingPromise;
    }

    // Start new connection with mutex
    connectingPromise = (async () => {
      try {
        // Fetch wsEndpoint from server
        const res = await fetch(serverUrl);
        if (!res.ok) {
          throw new Error(`Server returned ${res.status}: ${await res.text()}`);
        }
        const info = (await res.json()) as ServerInfoResponse;
        wsEndpoint = info.wsEndpoint;

        // Connect to the browser via CDP
        browser = await chromium.connectOverCDP(wsEndpoint);
        return browser;
      } finally {
        connectingPromise = null;
      }
    })();

    return connectingPromise;
  }

  // Find page by CDP targetId - more reliable than JS globals
  async function findPageByTargetId(b: Browser, targetId: string): Promise<Page | null> {
    for (const context of b.contexts()) {
      for (const page of context.pages()) {
        let cdpSession;
        try {
          cdpSession = await context.newCDPSession(page);
          const { targetInfo } = await cdpSession.send("Target.getTargetInfo");
          if (targetInfo.targetId === targetId) {
            return page;
          }
        } catch (err) {
          // Only ignore "target closed" errors, log unexpected ones
          const msg = err instanceof Error ? err.message : String(err);
          if (!msg.includes("Target closed") && !msg.includes("Session closed")) {
            console.warn(`Unexpected error checking page target: ${msg}`);
          }
        } finally {
          if (cdpSession) {
            try {
              await cdpSession.detach();
            } catch {
              // Ignore detach errors - session may already be closed
            }
          }
        }
      }
    }
    return null;
  }

  // Helper to get a page by name (used by multiple methods)
  async function getPage(name: string): Promise<Page> {
    // Request the page from server (creates if doesn't exist)
    const res = await fetch(`${serverUrl}/pages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name } satisfies GetPageRequest),
    });

    if (!res.ok) {
      throw new Error(`Failed to get page: ${await res.text()}`);
    }

    const pageInfo = (await res.json()) as GetPageResponse & { url?: string };
    const { targetId } = pageInfo;

    // Connect to browser
    const b = await ensureConnected();

    // Check if we're in extension mode
    const infoRes = await fetch(serverUrl);
    const info = (await infoRes.json()) as { mode?: string };
    const isExtensionMode = info.mode === "extension";

    if (isExtensionMode) {
      // In extension mode, DON'T use findPageByTargetId as it corrupts page state
      // Instead, find page by URL or use the only available page
      const allPages = b.contexts().flatMap((ctx) => ctx.pages());

      if (allPages.length === 0) {
        throw new Error(`No pages available in browser`);
      }

      if (allPages.length === 1) {
        return allPages[0]!;
      }

      // Multiple pages - try to match by URL if available
      if (pageInfo.url) {
        const matchingPage = allPages.find((p) => p.url() === pageInfo.url);
        if (matchingPage) {
          return matchingPage;
        }
      }

      // Fall back to first page
      if (!allPages[0]) {
        throw new Error(`No pages available in browser`);
      }
      return allPages[0];
    }

    // In launch mode, use the original targetId-based lookup
    const page = await findPageByTargetId(b, targetId);
    if (!page) {
      throw new Error(`Page "${name}" not found in browser contexts`);
    }

    return page;
  }

  return {
    page: getPage,

    async list(): Promise<string[]> {
      const res = await fetch(`${serverUrl}/pages`);
      const data = (await res.json()) as ListPagesResponse;
      return data.pages;
    },

    async close(name: string): Promise<void> {
      const res = await fetch(`${serverUrl}/pages/${encodeURIComponent(name)}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        throw new Error(`Failed to close page: ${await res.text()}`);
      }
    },

    async disconnect(): Promise<void> {
      // Just disconnect the CDP connection - pages persist on server
      if (browser) {
        await browser.close();
        browser = null;
      }
    },

    async getAISnapshot(name: string): Promise<string> {
      // Get the page
      const page = await getPage(name);

      // Inject the snapshot script and call getAISnapshot
      const snapshotScript = getSnapshotScript();
      const snapshot = await page.evaluate((script: string) => {
        // Inject script if not already present
        // Note: page.evaluate runs in browser context where window exists
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const w = globalThis as any;
        if (!w.__devBrowser_getAISnapshot) {
          // eslint-disable-next-line no-eval
          eval(script);
        }
        return w.__devBrowser_getAISnapshot();
      }, snapshotScript);

      return snapshot;
    },

    async selectSnapshotRef(name: string, ref: string): Promise<ElementHandle | null> {
      // Get the page
      const page = await getPage(name);

      // Find the element using the stored refs
      const elementHandle = await page.evaluateHandle((refId: string) => {
        // Note: page.evaluateHandle runs in browser context where globalThis is the window
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const w = globalThis as any;
        const refs = w.__devBrowserRefs;
        if (!refs) {
          throw new Error("No snapshot refs found. Call getAISnapshot first.");
        }
        const element = refs[refId];
        if (!element) {
          throw new Error(
            `Ref "${refId}" not found. Available refs: ${Object.keys(refs).join(", ")}`
          );
        }
        return element;
      }, ref);

      // Check if we got an element
      const element = elementHandle.asElement();
      if (!element) {
        await elementHandle.dispose();
        return null;
      }

      return element;
    },

    async getServerInfo(): Promise<ServerInfo> {
      const res = await fetch(serverUrl);
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${await res.text()}`);
      }
      const info = (await res.json()) as {
        wsEndpoint: string;
        mode?: string;
        extensionConnected?: boolean;
      };
      return {
        wsEndpoint: info.wsEndpoint,
        mode: (info.mode as "launch" | "extension") ?? "launch",
        extensionConnected: info.extensionConnected,
      };
    },

    async getOutline(name: string, options: OutlineOptions = {}): Promise<string> {
      const page = await getPage(name);
      const selector = options.selector ?? "body";
      const maxDepth = options.maxDepth ?? 6;

      const result = await page.evaluate(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ({ selector, maxDepth }: { selector: string; maxDepth: number }) => {
          // Browser context - use globalThis for DOM access
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const g = globalThis as any;
          const doc = g.document;

          const SKIP_TAGS = new Set([
            "SCRIPT",
            "STYLE",
            "NOSCRIPT",
            "SVG",
            "PATH",
            "BR",
            "HR",
            "META",
            "LINK",
          ]);

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function truncate(text: string, maxLen: number) {
            text = text.trim().replace(/\s+/g, " ");
            return text.length > maxLen ? text.slice(0, maxLen) + "..." : text;
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function getAttributes(el: any, getText: any) {
            const attrs: string[] = [];
            const tag = el.tagName;
            const text = getText(el);
            if (text) attrs.push('"' + text + '"');
            if (tag === "A") {
              const href = el.getAttribute("href");
              if (href) attrs.push("[href=" + href.slice(0, 50) + "]");
            }
            if (tag === "IMG") {
              const alt = el.getAttribute("alt");
              attrs.push(alt ? '[alt="' + alt.slice(0, 30) + '"]' : "[img]");
            }
            if (tag === "INPUT") {
              attrs.push("[type=" + (el.getAttribute("type") || "text") + "]");
              const placeholder = el.getAttribute("placeholder");
              if (placeholder) attrs.push('[placeholder="' + placeholder + '"]');
            }
            if (tag === "TEXTAREA") {
              const placeholder = el.getAttribute("placeholder");
              if (placeholder) attrs.push('[placeholder="' + placeholder + '"]');
            }
            if (tag === "SELECT") attrs.push("(" + el.options.length + " options)");
            const role = el.getAttribute("role");
            if (role) attrs.push("[role=" + role + "]");
            const ariaLabel = el.getAttribute("aria-label");
            if (ariaLabel) attrs.push('[aria-label="' + ariaLabel.slice(0, 30) + '"]');
            const elName = el.getAttribute("name");
            if (elName) attrs.push("[name=" + elName + "]");
            return attrs.join(" ");
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function formatLine(el: any, getId: any, getText: any, indent: string) {
            const attrs = getAttributes(el, getText);
            return indent + getId(el) + (attrs ? " " + attrs : "");
          }

          const root = doc.querySelector(selector);
          if (!root) throw new Error("Element not found: " + selector);

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function getId(el: any) {
            let id = el.tagName.toLowerCase();
            if (el.id) id += "#" + el.id;
            else if (el.className && typeof el.className === "string") {
              const cls = el.className.trim().split(/\s+/).slice(0, 2).join(".");
              if (cls) id += "." + cls;
            }
            return id;
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function getText(el: any) {
            let text = "";
            for (const child of el.childNodes) {
              if (child.nodeType === 3) text += child.textContent; // Node.TEXT_NODE = 3
            }
            return truncate(text, 50);
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function getSignature(el: any) {
            return getId(el) + " " + getText(el);
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function findRepeatedGroups(children: any[]) {
            const groups: Array<{ start: number; count: number }> = [];
            let i = 0;
            while (i < children.length) {
              const sig = getSignature(children[i]);
              let count = 1;
              while (i + count < children.length && getSignature(children[i + count]) === sig)
                count++;
              groups.push({ start: i, count });
              i += count;
            }
            return groups;
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function walk(el: any, depth: number): string {
            if (SKIP_TAGS.has(el.tagName)) return "";
            const indent = "  ".repeat(depth);
            let line = formatLine(el, getId, getText, indent);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const children = Array.from(el.children).filter((c: any) => !SKIP_TAGS.has(c.tagName));
            if (depth >= maxDepth && children.length > 0) line += " ... (" + children.length + ")";
            line += "\n";
            if (depth >= maxDepth || children.length === 0) return line;

            for (const { start, count } of findRepeatedGroups(children)) {
              if (count > 2) {
                const childOutput = walk(children[start], depth + 1);
                const firstLine = childOutput.split("\n")[0];
                line += firstLine + " (×" + count + ")\n";
                const rest = childOutput.split("\n").slice(1).join("\n");
                if (rest.trim()) line += rest;
              } else {
                for (let j = 0; j < count; j++) line += walk(children[start + j], depth + 1);
              }
            }
            return line;
          }

          return walk(root, 0);
        },
        { selector, maxDepth }
      );

      return result.trimEnd();
    },

    async getInteractiveOutline(name: string, selector = "body"): Promise<string> {
      const page = await getPage(name);

      const result = await page.evaluate((selector: string) => {
        // Browser context - use globalThis for DOM access
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const g = globalThis as any;
        const doc = g.document;

        const SKIP_TAGS = new Set([
          "SCRIPT",
          "STYLE",
          "NOSCRIPT",
          "SVG",
          "PATH",
          "BR",
          "HR",
          "META",
          "LINK",
        ]);
        const INTERACTIVE = new Set(["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"]);
        const LANDMARKS = new Set([
          "HEADER",
          "NAV",
          "MAIN",
          "FOOTER",
          "ASIDE",
          "SECTION",
          "FORM",
          "DIALOG",
        ]);
        const LANDMARK_ROLES = new Set([
          "banner",
          "navigation",
          "main",
          "contentinfo",
          "complementary",
          "region",
          "form",
          "search",
          "dialog",
        ]);

        function truncate(text: string, maxLen: number) {
          text = text.trim().replace(/\s+/g, " ");
          return text.length > maxLen ? text.slice(0, maxLen) + "..." : text;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function getAttributes(el: any, getText: any) {
          const attrs: string[] = [];
          const tag = el.tagName;
          const text = getText(el);
          if (text) attrs.push('"' + text + '"');
          if (tag === "A") {
            const href = el.getAttribute("href");
            if (href) attrs.push("[href=" + href.slice(0, 50) + "]");
          }
          if (tag === "IMG") {
            const alt = el.getAttribute("alt");
            attrs.push(alt ? '[alt="' + alt.slice(0, 30) + '"]' : "[img]");
          }
          if (tag === "INPUT") {
            attrs.push("[type=" + (el.getAttribute("type") || "text") + "]");
            const placeholder = el.getAttribute("placeholder");
            if (placeholder) attrs.push('[placeholder="' + placeholder + '"]');
          }
          if (tag === "TEXTAREA") {
            const placeholder = el.getAttribute("placeholder");
            if (placeholder) attrs.push('[placeholder="' + placeholder + '"]');
          }
          if (tag === "SELECT") attrs.push("(" + el.options.length + " options)");
          const role = el.getAttribute("role");
          if (role) attrs.push("[role=" + role + "]");
          const ariaLabel = el.getAttribute("aria-label");
          if (ariaLabel) attrs.push('[aria-label="' + ariaLabel.slice(0, 30) + '"]');
          const elName = el.getAttribute("name");
          if (elName) attrs.push("[name=" + elName + "]");
          return attrs.join(" ");
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function formatLine(el: any, getId: any, getText: any, indent: string) {
          const attrs = getAttributes(el, getText);
          return indent + getId(el) + (attrs ? " " + attrs : "");
        }

        const root = doc.querySelector(selector);
        if (!root) throw new Error("Element not found: " + selector);

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function isInteractive(el: any) {
          return (
            INTERACTIVE.has(el.tagName) ||
            el.getAttribute("role") === "button" ||
            el.hasAttribute("onclick") ||
            el.getAttribute("tabindex") === "0"
          );
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function isLandmark(el: any) {
          return LANDMARKS.has(el.tagName) || LANDMARK_ROLES.has(el.getAttribute("role") || "");
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function getId(el: any) {
          let id = el.tagName.toLowerCase();
          if (el.id) id += "#" + el.id;
          return id;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function getText(el: any) {
          return truncate(el.innerText || "", 50);
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function buildTree(el: any): any {
          if (SKIP_TAGS.has(el.tagName)) return null;
          if (isInteractive(el)) return { el, children: [] };

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const childTrees: any[] = [];
          for (const child of el.children) {
            const tree = buildTree(child);
            if (tree) childTrees.push(tree);
          }

          if (isLandmark(el) && childTrees.length > 0) return { el, children: childTrees };
          if (childTrees.length === 1) return childTrees[0];
          if (childTrees.length > 1) return { el: null, children: childTrees };
          return null;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        function render(node: any, depth = 0): string {
          if (!node) return "";
          const indent = "  ".repeat(depth);
          if (node.el) {
            let output = formatLine(node.el, getId, getText, indent) + "\n";
            for (const child of node.children) output += render(child, depth + 1);
            return output;
          }
          let output = "";
          for (const child of node.children) output += render(child, depth);
          return output;
        }

        const tree = buildTree(root);
        return tree ? render(tree) : "";
      }, selector);

      return result.trimEnd();
    },

    async getVisibleText(name: string, options: VisibleTextOptions = {}): Promise<string> {
      const page = await getPage(name);
      const selector = options.selector ?? "body";
      const limit = options.limit ?? 10000;

      const result = await page.evaluate(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ({ selector, limit }: { selector: string; limit: number }) => {
          // Browser context - use globalThis for DOM access
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const g = globalThis as any;
          const doc = g.document;

          const root = doc.querySelector(selector);
          if (!root) throw new Error("Element not found: " + selector);

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const cache = new Map<any, boolean>();

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function isVisible(el: any): boolean {
            if (!el || el === doc.documentElement) return true;
            if (cache.has(el)) return cache.get(el)!;
            const style = g.getComputedStyle(el);
            const visible =
              style.display !== "none" &&
              style.visibility !== "hidden" &&
              style.visibility !== "collapse" &&
              parseFloat(style.opacity) !== 0 &&
              isVisible(el.parentElement);
            cache.set(el, visible);
            return visible;
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          function isBlock(el: any): boolean {
            const display = g.getComputedStyle(el).display;
            return (
              display === "block" ||
              display === "flex" ||
              display === "grid" ||
              display === "list-item" ||
              display === "table" ||
              display === "table-row"
            );
          }

          let result = "";
          const walker = doc.createTreeWalker(
            root,
            0x5 // NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT = 4 + 1 = 5
          );
          while (walker.nextNode()) {
            const node = walker.currentNode;
            if (node.nodeType === 1) {
              // Node.ELEMENT_NODE = 1
              if (isBlock(node) && result.length > 0 && !result.endsWith("\n")) {
                result += "\n";
              }
            } else if (isVisible(node.parentElement)) {
              const t = (node.textContent || "").trim();
              if (t) result += t + " ";
            }
            // Early exit if we've exceeded the limit
            if (result.length > limit) break;
          }

          // Trim and truncate
          result = result.trim();
          if (result.length > limit) {
            result = result.slice(0, limit) + "...";
          }
          return result;
        },
        { selector, limit }
      );

      return result;
    },
  };
}
