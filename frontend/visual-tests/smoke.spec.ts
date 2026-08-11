import { mkdir, readdir, unlink, writeFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import { designPreviews } from "../apps/shell/design/designPreviews";

const OUTPUT_DIR = "visual-artifacts/react-current";

type ColorData = {
  hex: string;
  opacity: number;
  token: null;
};

const parsePx = (value: string): number => {
  const parsed = Number.parseFloat(value);

  return Number.isFinite(parsed) ? parsed : 0;
};

const parseColor = (value: string): ColorData => {
  const match = value.match(
    /rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)/i,
  );

  if (!match) {
    return {
      hex: value,
      opacity: 1,
      token: null,
    };
  }

  const r = Math.round(Number(match[1]));
  const g = Math.round(Number(match[2]));
  const b = Math.round(Number(match[3]));
  const opacity = match[4] === undefined ? 1 : Number(match[4]);
  const hex = `#${[r, g, b]
    .map((channel) => channel.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}`;

  return {
    hex,
    opacity,
    token: null,
  };
};

const parseAttributeList = (value: string | null): string[] =>
  (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const clearGeneratedPngs = async () => {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const entries = await readdir(OUTPUT_DIR, { withFileTypes: true });

  await Promise.all(
    entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".png"))
      .map((entry) => unlink(`${OUTPUT_DIR}/${entry.name}`)),
  );
};

test("capture React visual audit baseline", async ({ page }) => {
  test.setTimeout(120_000);

  await clearGeneratedPngs();

  const auditIds = new Set<string>();
  const items: Record<string, unknown> = {};

  for (const previewPath of Object.values(designPreviews)) {
    const previewPage = previewPath.replace(/\/index\.html$/, "");

    await page.goto(`/miniapp/react/${previewPath}`);

    await page.evaluate(async () => {
      await document.fonts.ready;
    });

    const auditCases = page.locator("[data-audit-case]");
    const auditCaseCount = await auditCases.count();

    if (auditCaseCount === 0) {
      throw new Error(
        `Preview "${previewPage}" does not contain [data-audit-case]`,
      );
    }

    for (let caseIndex = 0; caseIndex < auditCaseCount; caseIndex += 1) {
      const auditCase = auditCases.nth(caseIndex);
      const auditId = await auditCase.getAttribute("data-audit-id");
      const auditKind =
        (await auditCase.getAttribute("data-audit-kind")) ?? "component";
      const ignoredSpacingFields = parseAttributeList(
        await auditCase.getAttribute("data-audit-ignore-spacing"),
      );
      const caseContext = `preview "${previewPage}"${auditId ? `, auditId "${auditId}"` : ""}`;

      if (!auditId) {
        throw new Error(
          `${caseContext}: [data-audit-case] does not have data-audit-id`,
        );
      }

      if (auditKind !== "component" && auditKind !== "composition") {
        throw new Error(
          `${caseContext}: unsupported data-audit-kind "${auditKind}"`,
        );
      }

      if (auditIds.has(auditId)) {
        throw new Error(`${caseContext}: duplicate data-audit-id`);
      }

      auditIds.add(auditId);

      const targets = auditCase.locator("[data-audit-target]");
      const targetCount = await targets.count();

      if (targetCount !== 1) {
        throw new Error(
          `${caseContext}: expected exactly one [data-audit-target], found ${targetCount}`,
        );
      }

      const target = targets.first();

      await expect(
        target,
        `${caseContext}: audit target must be visible`,
      ).toBeVisible();

      const raw = await target.evaluate(
        (auditTarget, options) => {
          const { context, auditKind } = options;
          const children = Array.from(auditTarget.children);
          const targetIsVisualRoot =
            auditTarget.hasAttribute("data-audit-root");

          if (!targetIsVisualRoot && children.length !== 1) {
            throw new Error(
              `${context}: data-audit-target must contain exactly one visual component root, found ${children.length}`,
            );
          }

          const root = targetIsVisualRoot ? auditTarget : children[0];

          if (!(root instanceof HTMLElement)) {
            throw new Error(
              `${context}: visual component root must be an HTMLElement`,
            );
          }

          const explicitContents = root.querySelectorAll(
            "[data-audit-content]",
          );
          const explicitTypographySources = root.querySelectorAll(
            "[data-audit-typography]",
          );

          if (explicitContents.length > 1) {
            throw new Error(
              `${context}: visual component root contains more than one [data-audit-content], found ${explicitContents.length}`,
            );
          }

          if (explicitTypographySources.length > 1) {
            throw new Error(
              `${context}: visual component root contains more than one [data-audit-typography], found ${explicitTypographySources.length}`,
            );
          }

          let contentElement: HTMLElement | null = null;
          let typographyElement: HTMLElement | null = null;

          if (explicitContents.length === 1) {
            const explicitContent = explicitContents[0];

            if (explicitContent instanceof HTMLElement) {
              contentElement = explicitContent;
            }
          }

          if (explicitTypographySources.length === 1) {
            const explicitTypographySource = explicitTypographySources[0];

            if (explicitTypographySource instanceof HTMLElement) {
              typographyElement = explicitTypographySource;
            }
          }

          const contentFallbackEnabled =
            auditTarget.getAttribute("data-audit-content-mode") !== "none";

          if (!contentElement && !typographyElement && contentFallbackEnabled) {
            const walker = document.createTreeWalker(
              root,
              NodeFilter.SHOW_TEXT,
            );
            let current = walker.nextNode();

            while (current) {
              const text = current.textContent?.trim();
              const parent = current.parentElement;

              if (text && parent && parent !== root) {
                const style = getComputedStyle(parent);
                const rect = parent.getBoundingClientRect();
                const visible =
                  style.display !== "none" &&
                  style.visibility !== "hidden" &&
                  Number(style.opacity) !== 0 &&
                  rect.width > 0 &&
                  rect.height > 0;

                if (visible) {
                  contentElement = parent;
                  break;
                }
              }

              current = walker.nextNode();
            }
          }

          const rootStyle = getComputedStyle(root);
          const rootRect = root.getBoundingClientRect();
          const borderTop = Number.parseFloat(rootStyle.borderTopWidth) || 0;
          const borderRight =
            Number.parseFloat(rootStyle.borderRightWidth) || 0;
          const borderBottom =
            Number.parseFloat(rootStyle.borderBottomWidth) || 0;
          const borderLeft = Number.parseFloat(rootStyle.borderLeftWidth) || 0;

          let content = null;
          const textMetricsElement = contentElement ?? typographyElement;

          if (textMetricsElement) {
            const contentStyle = getComputedStyle(textMetricsElement);
            const contentRect = textMetricsElement.getBoundingClientRect();

            content = {
              text: textMetricsElement.textContent?.trim() ?? "",
              color: contentStyle.color,
              typography: {
                fontFamily: contentStyle.fontFamily,
                fontStyle: contentStyle.fontStyle,
                fontSize: contentStyle.fontSize,
                fontWeight: contentStyle.fontWeight,
                lineHeight: contentStyle.lineHeight,
              },
              contentInsets: contentElement
                ? {
                    top: Math.max(
                      0,
                      contentRect.top - rootRect.top - borderTop,
                    ),
                    right: Math.max(
                      0,
                      rootRect.right - contentRect.right - borderRight,
                    ),
                    bottom: Math.max(
                      0,
                      rootRect.bottom - contentRect.bottom - borderBottom,
                    ),
                    left: Math.max(
                      0,
                      contentRect.left - rootRect.left - borderLeft,
                    ),
                  }
                : null,
            };
          }

          const getColorAlpha = (value: string): number => {
            const match = value.match(
              /rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+(?:\s*,\s*([\d.]+))?\s*\)/i,
            );

            if (!match) {
              return value === "transparent" ? 0 : 1;
            }

            return match[1] === undefined ? 1 : Number(match[1]);
          };

          let rasterBackground: string | null = null;

          if (auditKind === "composition") {
            let currentElement: HTMLElement | null = root;

            while (currentElement) {
              const backgroundColor =
                getComputedStyle(currentElement).backgroundColor;

              if (getColorAlpha(backgroundColor) >= 0.999) {
                rasterBackground = backgroundColor;
                break;
              }

              currentElement = currentElement.parentElement;
            }
          }

          return {
            tagName: root.tagName,
            className: root.getAttribute("class") ?? "",
            geometry: {
              width: rootRect.width,
              height: rootRect.height,
              borderTopWidth: rootStyle.borderTopWidth,
              borderRightWidth: rootStyle.borderRightWidth,
              borderBottomWidth: rootStyle.borderBottomWidth,
              borderLeftWidth: rootStyle.borderLeftWidth,
              borderTopLeftRadius: rootStyle.borderTopLeftRadius,
              borderTopRightRadius: rootStyle.borderTopRightRadius,
              borderBottomRightRadius: rootStyle.borderBottomRightRadius,
              borderBottomLeftRadius: rootStyle.borderBottomLeftRadius,
            },
            colors: {
              background: rootStyle.backgroundColor,
              border: rootStyle.borderTopColor,
              text: content?.color ?? null,
            },
            typography: content?.typography ?? null,
            rasterBackground,
            spacing: {
              paddingTop: rootStyle.paddingTop,
              paddingRight: rootStyle.paddingRight,
              paddingBottom: rootStyle.paddingBottom,
              paddingLeft: rootStyle.paddingLeft,
              gap: rootStyle.gap,
              contentInsets: content?.contentInsets ?? null,
            },
          };
        },
        {
          context: caseContext,
          auditKind,
        },
      );

      const borderWidths = [
        parsePx(raw.geometry.borderTopWidth),
        parsePx(raw.geometry.borderRightWidth),
        parsePx(raw.geometry.borderBottomWidth),
        parsePx(raw.geometry.borderLeftWidth),
      ];
      const borderRadii = {
        topLeft: parsePx(raw.geometry.borderTopLeftRadius),
        topRight: parsePx(raw.geometry.borderTopRightRadius),
        bottomRight: parsePx(raw.geometry.borderBottomRightRadius),
        bottomLeft: parsePx(raw.geometry.borderBottomLeftRadius),
      };
      const typography = raw.typography
        ? {
            fontFamily: raw.typography.fontFamily
              .split(",")[0]
              .replaceAll('"', "")
              .trim(),
            fontStyle: raw.typography.fontStyle,
            fontSize: parsePx(raw.typography.fontSize),
            fontWeight: Number.parseInt(raw.typography.fontWeight, 10),
            lineHeight: parsePx(raw.typography.lineHeight),
          }
        : null;

      items[auditId] = {
        id: auditId,
        png: `${auditId}.png`,
        auditKind,
        rasterBackground: raw.rasterBackground
          ? parseColor(raw.rasterBackground).hex
          : null,
        auditPolicy:
          ignoredSpacingFields.length > 0
            ? {
                ignoredSpacingFields,
              }
            : {},
        source: {
          nodeName: raw.className || raw.tagName,
          nodeType: "DOM",
          page: previewPage,
          url: page.url(),
        },
        geometry: {
          width: raw.geometry.width,
          height: raw.geometry.height,
          borderWidth: borderWidths[0],
          borderRadius: borderRadii.topLeft,
          borderRadii,
        },
        colors: {
          background: parseColor(raw.colors.background),
          border: parseColor(raw.colors.border),
          text: raw.colors.text ? parseColor(raw.colors.text) : null,
        },
        typography,
        spacing: {
          paddingTop: parsePx(raw.spacing.paddingTop),
          paddingRight: parsePx(raw.spacing.paddingRight),
          paddingBottom: parsePx(raw.spacing.paddingBottom),
          paddingLeft: parsePx(raw.spacing.paddingLeft),
          gap: raw.spacing.gap === "normal" ? 0 : parsePx(raw.spacing.gap),
          contentInsets: raw.spacing.contentInsets,
        },
      };

      await target.scrollIntoViewIfNeeded();

      const box = await target.boundingBox();

      if (!box) {
        throw new Error(
          `${caseContext}: audit target does not have a bounding box`,
        );
      }

      const clip = {
        x: Math.round(box.x),
        y: Math.round(box.y),
        width: Math.round(box.width),
        height: Math.round(box.height),
      };

      await page.screenshot({
        path: `${OUTPUT_DIR}/${auditId}.png`,
        clip,
        animations: "disabled",
        omitBackground: true,
        scale: "css",
      });

      console.log(`${auditId}: ${clip.width}x${clip.height}`);
    }
  }

  const manifest = {
    schemaVersion: 2,
    generatedAt: new Date().toISOString(),
    source: {
      app: "JobMonitor",
      renderer: "React / Chromium",
    },
    items,
  };

  await writeFile(
    `${OUTPUT_DIR}/manifest.json`,
    JSON.stringify(manifest, null, 2),
    "utf8",
  );

  console.log(`Captured ${auditIds.size} audit cases`);
  console.log(`Saved: ${OUTPUT_DIR}/manifest.json`);
});
