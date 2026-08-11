import fs from "node:fs";
import path from "node:path";

import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";

const ROOT = process.cwd();

const FIGMA_DIR = path.join(ROOT, "visual-artifacts", "figma-baseline");

const REACT_DIR = path.join(ROOT, "visual-artifacts", "react-current");

const DIFF_DIR = path.join(ROOT, "visual-artifacts", "diff");

const REPORT_PATH = path.join(ROOT, "visual-artifacts", "visual-report.json");

const WEIGHTS = {
  geometry: 0.3,
  colors: 0.25,
  typography: 0.2,
  spacing: 0.15,
  raster: 0.1,
};

const TOLERANCES = {
  geometry: {
    width: 1,
    height: 1,
    borderWidth: 0.5,
    borderRadius: 1,

    borderRadii: {
      topLeft: 1,
      topRight: 1,
      bottomRight: 1,
      bottomLeft: 1,
    },
  },

  typography: {
    fontSize: 0.5,
    fontWeight: 0,
    lineHeight: 0.5,
  },

  spacing: {
    paddingTop: 1,
    paddingRight: 1,
    paddingBottom: 1,
    paddingLeft: 1,
    gap: 1,

    contentInsets: {
      top: 1,
      right: 1,
      bottom: 1,
      left: 1,
    },
  },
};

const PASS_SCORE = 97;
const WARNING_SCORE = 94;

const AUDIT_POLICIES = {
  "button--default": {
    layout: "fluid-x",
  },
  "button--disabled": {
    layout: "fluid-x",
  },
  "button--loading": {
    layout: "fluid-x",
  },
  "button--hug-width": {
    layout: "fixed",
    widthTolerance: 2,
  },

  "back-button--default": {
    layout: "fixed",
    ignoredSpacingFields: ["paddingTop", "paddingBottom"],
    contentInsetTolerances: {
      top: 2,
    },
    skipRaster: true,
  },

  "icon-button--default": {
    layout: "fixed",
    rasterBackground: "#FFFFFF",
  },
  "icon-button--close": {
    layout: "fixed",
    rasterBackground: "#FFFFFF",
  },
  "icon-button--disabled": {
    layout: "fixed",
    rasterBackground: "#FFFFFF",
  },
  "icon-button--hover": {
    layout: "fixed",
  },

  "selection-card--default": {
    layout: "fixed",
    ignoredContentInsetFields: ["right"],
  },
  "selection-card--selected": {
    layout: "fixed",
    ignoredContentInsetFields: ["right"],
  },
  "selection-card--disabled": {
    layout: "fixed",
    ignoredContentInsetFields: ["right"],
  },

  "text-field--default": {
    layout: "fluid-x",
    ignoreTextColor: true,
    ignoredSpacingFields: ["gap"],
    ignoredTypographyFields: ["lineHeight"],
  },
  "text-field--search": {
    layout: "fluid-x",
    ignoreTextColor: true,
    ignoredTypographyFields: ["lineHeight"],
  },
  "text-field--salary": {
    layout: "fluid-x",
    ignoredTypographyFields: ["lineHeight"],
  },
  "text-field--error": {
    layout: "fluid-x",
    ignoredSpacingFields: ["gap"],
    ignoredTypographyFields: ["lineHeight"],
  },
  "text-field--disabled": {
    layout: "fluid-x",
    ignoredSpacingFields: ["gap"],
    ignoredTypographyFields: ["lineHeight"],
  },

  "progress-stepper--step-1": {
    layout: "fixed",
    skipTypography: true,
    rasterBackground: "#FFFFFF",
  },
  "progress-stepper--step-2": {
    layout: "fixed",
    skipTypography: true,
    rasterBackground: "#FFFFFF",
  },
  "progress-stepper--step-3": {
    layout: "fixed",
    skipTypography: true,
    rasterBackground: "#FFFFFF",
  },
  "progress-stepper--step-4": {
    layout: "fixed",
    skipTypography: true,
    rasterBackground: "#FFFFFF",
  },
};

const DEFAULT_POLICY = {
  layout: "fixed",

  widthTolerance: TOLERANCES.geometry.width,

  skipRaster: false,

  skipTypography: false,

  rasterBackground: null,

  ignoreTextColor: false,

  ignoredSpacingFields: [],

  ignoredContentInsetFields: [],

  ignoredTypographyFields: [],

  contentInsetTolerances: {},
};

const mergeUnique = (...groups) => [
  ...new Set(groups.flatMap((group) => group ?? [])),
];

const getAuditPolicy = ({ auditId, figma, react }) => {
  const auditKind = react.auditKind ?? figma.auditKind ?? "component";

  const compositionDefaults =
    auditKind === "composition"
      ? {
          skipTypography: true,
          rasterBackground:
            react.rasterBackground ?? figma.rasterBackground ?? null,
        }
      : {};

  const manifestPolicy = react.auditPolicy ?? figma.auditPolicy ?? {};
  const custom = AUDIT_POLICIES[auditId] ?? {};

  return {
    ...DEFAULT_POLICY,
    ...compositionDefaults,
    ...manifestPolicy,
    ...custom,

    auditKind,

    ignoredSpacingFields: mergeUnique(
      compositionDefaults.ignoredSpacingFields,
      manifestPolicy.ignoredSpacingFields,
      custom.ignoredSpacingFields,
    ),

    ignoredContentInsetFields: mergeUnique(
      compositionDefaults.ignoredContentInsetFields,
      manifestPolicy.ignoredContentInsetFields,
      custom.ignoredContentInsetFields,
    ),

    ignoredTypographyFields: mergeUnique(
      compositionDefaults.ignoredTypographyFields,
      manifestPolicy.ignoredTypographyFields,
      custom.ignoredTypographyFields,
    ),

    contentInsetTolerances: {
      ...(compositionDefaults.contentInsetTolerances ?? {}),
      ...(manifestPolicy.contentInsetTolerances ?? {}),
      ...(custom.contentInsetTolerances ?? {}),
    },
  };
};

const getCliOption = (name) => {
  const args = process.argv.slice(2);

  const inlinePrefix = `--${name}=`;

  const inlineArgument = args.find((argument) =>
    argument.startsWith(inlinePrefix),
  );

  if (inlineArgument) {
    const value = inlineArgument.slice(inlinePrefix.length).trim();

    return value || null;
  }

  const optionIndex = args.indexOf(`--${name}`);

  if (optionIndex === -1) {
    return null;
  }

  const value = args[optionIndex + 1];

  if (!value || value.startsWith("--")) {
    return null;
  }

  return value.trim() || null;
};

const FILTER = getCliOption("filter");

const matchesFilter = (auditId, filter) => {
  if (!filter) {
    return true;
  }

  const normalizedAuditId = String(auditId).trim().toLowerCase();

  const normalizedFilter = String(filter).trim().toLowerCase();

  return (
    normalizedAuditId === normalizedFilter ||
    normalizedAuditId.startsWith(`${normalizedFilter}--`)
  );
};

const readJson = (filePath) => {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found:\n${filePath}`);
  }

  return JSON.parse(fs.readFileSync(filePath, "utf8"));
};

const round = (value, digits = 2) => {
  const multiplier = 10 ** digits;

  return Math.round(value * multiplier) / multiplier;
};

const numberMatches = (expected, actual, tolerance) => {
  if (typeof expected !== "number" || typeof actual !== "number") {
    return false;
  }

  return Math.abs(expected - actual) <= tolerance;
};

const stringMatches = (expected, actual) =>
  String(expected).trim().toLowerCase() === String(actual).trim().toLowerCase();

const percentage = (passed, total) => {
  if (total === 0) {
    return 100;
  }

  return (passed / total) * 100;
};

const makeCheck = ({ name, expected, actual, pass }) => ({
  name,
  expected,
  actual,
  pass,
});

const makeSection = (checks, options = {}) => {
  const {
    applicable = checks.length > 0,

    reason = null,
  } = options;

  return {
    checks,
    applicable,
    reason,

    score: applicable
      ? percentage(
          checks.filter((check) => check.pass).length,

          checks.length,
        )
      : null,
  };
};

const makeSkippedSection = (reason) => ({
  checks: [],
  applicable: false,
  score: null,
  reason,
});

const normalizeFontStyle = (value) => {
  const normalized = String(value ?? "").toLowerCase();

  return normalized.includes("italic") ? "italic" : "normal";
};

const hasVisibleBorder = (item) => {
  const borderWidth = item.geometry?.borderWidth ?? 0;

  const border = item.colors?.border;

  if (borderWidth <= 0 || border == null) {
    return false;
  }

  if (typeof border.opacity === "number" && border.opacity <= 0) {
    return false;
  }

  return true;
};

const compareGeometry = ({ figma, react, policy }) => {
  const checks = [];

  if (policy.layout !== "fluid-x") {
    checks.push(
      makeCheck({
        name: "width",

        expected: figma.geometry.width,

        actual: react.geometry.width,

        pass: numberMatches(
          figma.geometry.width,

          react.geometry.width,

          policy.widthTolerance,
        ),
      }),
    );
  }

  checks.push(
    makeCheck({
      name: "height",

      expected: figma.geometry.height,

      actual: react.geometry.height,

      pass: numberMatches(
        figma.geometry.height,

        react.geometry.height,

        TOLERANCES.geometry.height,
      ),
    }),
  );

  const figmaHasBorder = hasVisibleBorder(figma);

  const reactHasBorder = hasVisibleBorder(react);

  checks.push(
    makeCheck({
      name: "border.visible",

      expected: figmaHasBorder,

      actual: reactHasBorder,

      pass: figmaHasBorder === reactHasBorder,
    }),
  );

  if (figmaHasBorder || reactHasBorder) {
    checks.push(
      makeCheck({
        name: "borderWidth",

        expected: figma.geometry.borderWidth,

        actual: react.geometry.borderWidth,

        pass: numberMatches(
          figma.geometry.borderWidth,

          react.geometry.borderWidth,

          TOLERANCES.geometry.borderWidth,
        ),
      }),
    );
  }

  checks.push(
    makeCheck({
      name: "borderRadius",

      expected: figma.geometry.borderRadius,

      actual: react.geometry.borderRadius,

      pass: numberMatches(
        figma.geometry.borderRadius,

        react.geometry.borderRadius,

        TOLERANCES.geometry.borderRadius,
      ),
    }),
  );

  const corners = ["topLeft", "topRight", "bottomRight", "bottomLeft"];

  for (const corner of corners) {
    const expected = figma.geometry.borderRadii?.[corner];

    const actual = react.geometry.borderRadii?.[corner];

    if (expected === undefined || actual === undefined) {
      continue;
    }

    checks.push(
      makeCheck({
        name: `borderRadii.${corner}`,

        expected,
        actual,

        pass: numberMatches(
          expected,
          actual,

          TOLERANCES.geometry.borderRadii[corner],
        ),
      }),
    );
  }

  return makeSection(checks);
};

const compareColor = (name, figma, react) => {
  const checks = [];

  if (figma?.hex !== undefined && react?.hex !== undefined) {
    checks.push(
      makeCheck({
        name: `${name}.hex`,

        expected: figma.hex,

        actual: react.hex,

        pass: stringMatches(figma.hex, react.hex),
      }),
    );
  }

  if (figma?.opacity !== undefined && react?.opacity !== undefined) {
    checks.push(
      makeCheck({
        name: `${name}.opacity`,

        expected: figma.opacity,

        actual: react.opacity,

        pass: Math.abs(figma.opacity - react.opacity) <= 0.01,
      }),
    );
  }

  return checks;
};

const compareColors = ({ figma, react, policy }) => {
  const checks = [
    ...compareColor(
      "background",

      figma.colors.background,

      react.colors.background,
    ),
  ];

  if (!policy.ignoreTextColor) {
    checks.push(
      ...compareColor(
        "text",

        figma.colors.text,

        react.colors.text,
      ),
    );
  }

  if (hasVisibleBorder(figma) || hasVisibleBorder(react)) {
    checks.push(
      ...compareColor(
        "border",

        figma.colors.border,

        react.colors.border,
      ),
    );
  }

  if (checks.length === 0) {
    return makeSkippedSection("colors not applicable");
  }

  return makeSection(checks);
};

const compareTypography = ({ figma, react, policy }) => {
  if (policy.skipTypography) {
    return makeSkippedSection("typography skipped by audit policy");
  }

  if (figma == null && react == null) {
    return makeSkippedSection("typography not applicable");
  }

  if (figma == null || react == null) {
    return makeSection([
      makeCheck({
        name: "typography",

        expected: figma,

        actual: react,

        pass: false,
      }),
    ]);
  }

  const checks = [];

  if (!policy.ignoredTypographyFields.includes("fontFamily")) {
    checks.push(
      makeCheck({
        name: "fontFamily",

        expected: figma.fontFamily,

        actual: react.fontFamily,

        pass: stringMatches(figma.fontFamily, react.fontFamily),
      }),
    );
  }

  if (!policy.ignoredTypographyFields.includes("fontStyle")) {
    const figmaFontStyle = normalizeFontStyle(figma.fontStyle);

    const reactFontStyle = normalizeFontStyle(react.fontStyle);

    checks.push(
      makeCheck({
        name: "fontStyle",

        expected: figmaFontStyle,

        actual: reactFontStyle,

        pass: figmaFontStyle === reactFontStyle,
      }),
    );
  }

  if (!policy.ignoredTypographyFields.includes("fontSize")) {
    checks.push(
      makeCheck({
        name: "fontSize",

        expected: figma.fontSize,

        actual: react.fontSize,

        pass: numberMatches(
          figma.fontSize,
          react.fontSize,

          TOLERANCES.typography.fontSize,
        ),
      }),
    );
  }

  if (!policy.ignoredTypographyFields.includes("fontWeight")) {
    checks.push(
      makeCheck({
        name: "fontWeight",

        expected: figma.fontWeight,

        actual: react.fontWeight,

        pass: numberMatches(
          figma.fontWeight,
          react.fontWeight,

          TOLERANCES.typography.fontWeight,
        ),
      }),
    );
  }

  if (!policy.ignoredTypographyFields.includes("lineHeight")) {
    checks.push(
      makeCheck({
        name: "lineHeight",

        expected: figma.lineHeight,

        actual: react.lineHeight,

        pass: numberMatches(
          figma.lineHeight,
          react.lineHeight,

          TOLERANCES.typography.lineHeight,
        ),
      }),
    );
  }

  if (checks.length === 0) {
    return makeSkippedSection("all typography fields ignored by audit policy");
  }

  return makeSection(checks);
};

const compareSpacing = ({ figma, react, policy }) => {
  if (figma == null && react == null) {
    return makeSkippedSection("spacing not applicable");
  }

  if (figma == null || react == null) {
    return makeSection([
      makeCheck({
        name: "spacing",

        expected: figma,

        actual: react,

        pass: false,
      }),
    ]);
  }

  const checks = [];

  const simpleFields = [
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "gap",
  ];

  for (const field of simpleFields) {
    if (policy.ignoredSpacingFields.includes(field)) {
      continue;
    }

    const expected = figma[field];

    const actual = react[field];

    if (expected === undefined || actual === undefined) {
      continue;
    }

    checks.push(
      makeCheck({
        name: field,

        expected,
        actual,

        pass: numberMatches(
          expected,
          actual,

          TOLERANCES.spacing[field],
        ),
      }),
    );
  }

  const baseInsetFields =
    policy.layout === "fluid-x"
      ? ["top", "bottom"]
      : ["top", "right", "bottom", "left"];

  const insetFields = baseInsetFields.filter(
    (field) => !policy.ignoredContentInsetFields.includes(field),
  );

  for (const field of insetFields) {
    const expected = figma.contentInsets?.[field];

    const actual = react.contentInsets?.[field];

    if (expected === undefined || actual === undefined) {
      continue;
    }

    const tolerance =
      policy.contentInsetTolerances[field] ??
      TOLERANCES.spacing.contentInsets[field];

    checks.push(
      makeCheck({
        name: `contentInsets.${field}`,

        expected,
        actual,

        pass: numberMatches(expected, actual, tolerance),
      }),
    );
  }

  if (checks.length === 0) {
    return makeSkippedSection("spacing not applicable");
  }

  return makeSection(checks);
};

/*
 * Преобразуем #RRGGBB в RGB.
 */
const parseHexColor = (hex) => {
  const normalized = String(hex).replace("#", "").trim();

  if (normalized.length !== 6) {
    throw new Error(`Unsupported raster background color: ${hex}`);
  }

  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),

    g: Number.parseInt(normalized.slice(2, 4), 16),

    b: Number.parseInt(normalized.slice(4, 6), 16),
  };
};

/*
 * Кладём PNG с alpha на заданный surface.
 *
 * Это нужно, когда:
 *
 * Figma:
 * transparent root
 *
 * React:
 * тот же root снят поверх белого preview.
 *
 * После этого pixelmatch сравнивает
 * реальный внешний вид компонента,
 * а не transparent vs white.
 */
const flattenPngOnBackground = (source, backgroundHex) => {
  if (!backgroundHex) {
    return source;
  }

  const background = parseHexColor(backgroundHex);

  const flattened = new PNG({
    width: source.width,

    height: source.height,
  });

  for (let index = 0; index < source.data.length; index += 4) {
    const alpha = source.data[index + 3] / 255;

    const inverseAlpha = 1 - alpha;

    flattened.data[index] = Math.round(
      source.data[index] * alpha + background.r * inverseAlpha,
    );

    flattened.data[index + 1] = Math.round(
      source.data[index + 1] * alpha + background.g * inverseAlpha,
    );

    flattened.data[index + 2] = Math.round(
      source.data[index + 2] * alpha + background.b * inverseAlpha,
    );

    flattened.data[index + 3] = 255;
  }

  return flattened;
};

const normalizePngSize = (source, width, height) => {
  if (source.width === width && source.height === height) {
    return source;
  }

  const normalized = new PNG({
    width,
    height,
  });

  normalized.data.fill(0);

  for (let y = 0; y < source.height; y += 1) {
    const sourceStart = y * source.width * 4;

    const sourceEnd = sourceStart + source.width * 4;

    const targetStart = y * width * 4;

    source.data.copy(normalized.data, targetStart, sourceStart, sourceEnd);
  }

  return normalized;
};

const compareRaster = ({ auditId, figmaPath, reactPath, policy }) => {
  if (policy.layout === "fluid-x") {
    return makeSkippedSection("full raster skipped for fluid-x layout");
  }

  if (policy.skipRaster) {
    return makeSkippedSection("full raster skipped by audit policy");
  }

  if (!fs.existsSync(figmaPath)) {
    return {
      score: 0,
      applicable: true,
      checks: null,

      differentPixels: null,

      totalPixels: null,

      reason: "Figma PNG not found",
    };
  }

  if (!fs.existsSync(reactPath)) {
    return {
      score: 0,
      applicable: true,
      checks: null,

      differentPixels: null,

      totalPixels: null,

      reason: "React PNG not found",
    };
  }

  let originalFigma = PNG.sync.read(fs.readFileSync(figmaPath));

  let originalReact = PNG.sync.read(fs.readFileSync(reactPath));

  /*
   * Если audit policy задаёт surface,
   * обе картинки сначала композим
   * на один и тот же фон.
   */
  if (policy.rasterBackground) {
    originalFigma = flattenPngOnBackground(
      originalFigma,
      policy.rasterBackground,
    );

    originalReact = flattenPngOnBackground(
      originalReact,
      policy.rasterBackground,
    );
  }

  const widthDifference = Math.abs(originalFigma.width - originalReact.width);

  const heightDifference = Math.abs(
    originalFigma.height - originalReact.height,
  );

  if (
    widthDifference > policy.widthTolerance ||
    heightDifference > TOLERANCES.geometry.height
  ) {
    return {
      score: 0,
      applicable: true,
      checks: null,

      differentPixels: null,

      totalPixels: null,

      reason:
        `dimensions differ beyond tolerance: ` +
        `${originalFigma.width}x${originalFigma.height} ` +
        `vs ${originalReact.width}x${originalReact.height}`,
    };
  }

  const comparisonWidth = Math.max(originalFigma.width, originalReact.width);

  const comparisonHeight = Math.max(originalFigma.height, originalReact.height);

  const figma = normalizePngSize(
    originalFigma,
    comparisonWidth,
    comparisonHeight,
  );

  const react = normalizePngSize(
    originalReact,
    comparisonWidth,
    comparisonHeight,
  );

  const diff = new PNG({
    width: comparisonWidth,

    height: comparisonHeight,
  });

  const differentPixels = pixelmatch(
    figma.data,
    react.data,
    diff.data,

    comparisonWidth,
    comparisonHeight,

    {
      threshold: 0.1,
      includeAA: false,
      diffMask: true,
    },
  );

  fs.mkdirSync(DIFF_DIR, {
    recursive: true,
  });

  const diffPath = path.join(DIFF_DIR, `${auditId}.png`);

  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const totalPixels = comparisonWidth * comparisonHeight;

  const differencePercent = (differentPixels / totalPixels) * 100;

  const dimensionsWereNormalized =
    originalFigma.width !== originalReact.width ||
    originalFigma.height !== originalReact.height;

  return {
    score: Math.max(0, 100 - differencePercent),

    applicable: true,

    checks: null,

    differentPixels,
    totalPixels,

    differencePercent,

    diff: path.relative(ROOT, diffPath),

    ...(policy.rasterBackground
      ? {
          background: policy.rasterBackground,
        }
      : {}),

    ...(dimensionsWereNormalized
      ? {
          reason:
            `dimensions normalized within tolerance: ` +
            `${originalFigma.width}x${originalFigma.height} ` +
            `vs ${originalReact.width}x${originalReact.height}`,
        }
      : {}),
  };
};

const calculateFinalScore = (sections) => {
  let weightedScore = 0;
  let activeWeight = 0;

  for (const [sectionName, weight] of Object.entries(WEIGHTS)) {
    const section = sections[sectionName];

    if (
      !section ||
      section.applicable === false ||
      typeof section.score !== "number"
    ) {
      continue;
    }

    weightedScore += section.score * weight;

    activeWeight += weight;
  }

  if (activeWeight === 0) {
    return 0;
  }

  return weightedScore / activeWeight;
};

const getStatus = (score) => {
  if (score >= PASS_SCORE) {
    return "PASS";
  }

  if (score >= WARNING_SCORE) {
    return "WARNING";
  }

  return "FAIL";
};

const printSection = (name, section) => {
  console.log("");

  if (section.applicable === false) {
    console.log(`${name}: SKIPPED`);

    if (section.reason) {
      console.log(`  ! ${section.reason}`);
    }

    return;
  }

  console.log(`${name}: ${section.score.toFixed(2)}%`);

  if (section.reason) {
    console.log(`  ! ${section.reason}`);
  }

  if (section.background) {
    console.log(`  ! raster background: ${section.background}`);
  }

  if (!section.checks) {
    return;
  }

  for (const check of section.checks) {
    console.log(
      `  ${check.pass ? "✓" : "✗"} ${check.name}: ` +
        `${check.expected} → ${check.actual}`,
    );
  }
};

const compareItem = ({ auditId, figma, react }) => {
  const policy = getAuditPolicy({
    auditId,
    figma,
    react,
  });

  const geometry = compareGeometry({
    figma,
    react,
    policy,
  });

  const colors = compareColors({
    figma,
    react,
    policy,
  });

  const typography = compareTypography({
    figma: figma.typography,

    react: react.typography,

    policy,
  });

  const spacing = compareSpacing({
    figma: figma.spacing,

    react: react.spacing,

    policy,
  });

  const raster = compareRaster({
    auditId,

    figmaPath: path.join(FIGMA_DIR, figma.png),

    reactPath: path.join(REACT_DIR, react.png),

    policy,
  });

  const sections = {
    geometry,
    colors,
    typography,
    spacing,
    raster,
  };

  const score = round(calculateFinalScore(sections), 2);

  return {
    auditId,
    policy,
    score,

    status: getStatus(score),

    sections,
  };
};

const figmaManifest = readJson(path.join(FIGMA_DIR, "manifest.json"));

const reactManifest = readJson(path.join(REACT_DIR, "manifest.json"));

if (figmaManifest.schemaVersion !== 2) {
  throw new Error(
    `Unsupported Figma schemaVersion: ${figmaManifest.schemaVersion}`,
  );
}

if (reactManifest.schemaVersion !== 2) {
  throw new Error(
    `Unsupported React schemaVersion: ${reactManifest.schemaVersion}`,
  );
}

fs.mkdirSync(DIFF_DIR, {
  recursive: true,
});

const figmaIds = Object.keys(figmaManifest.items);

const reactIds = Object.keys(reactManifest.items);

const allIds = FILTER
  ? figmaIds.filter((auditId) => matchesFilter(auditId, FILTER)).sort()
  : [...new Set([...figmaIds, ...reactIds])].sort();

if (FILTER && allIds.length === 0) {
  throw new Error(
    `No Figma baselines matched filter "${FILTER}".\n` +
      `Link/export at least one matching Figma baseline first.`,
  );
}

const results = [];

let hasFailure = false;

console.log("");

console.log("========================================");

console.log("JOBMONITOR VISUAL DESIGN TEST");

console.log("========================================");

if (FILTER) {
  console.log("");

  console.log(`FILTER: ${FILTER}`);

  console.log(`FIGMA BASELINES IN SCOPE: ${allIds.length}`);

  console.log("MODE: compare matching Figma baselines only");
}

for (const auditId of allIds) {
  const figma = figmaManifest.items[auditId];

  const react = reactManifest.items[auditId];

  console.log("");

  console.log("----------------------------------------");

  console.log(auditId);

  console.log("----------------------------------------");

  if (!figma) {
    console.log("FAIL: missing Figma baseline");

    results.push({
      auditId,
      score: 0,

      status: "FAIL",

      reason: "missing Figma baseline",
    });

    hasFailure = true;

    continue;
  }

  if (!react) {
    console.log("FAIL: missing React capture");

    results.push({
      auditId,
      score: 0,

      status: "FAIL",

      reason: "missing React capture",
    });

    hasFailure = true;

    continue;
  }

  const result = compareItem({
    auditId,
    figma,
    react,
  });

  results.push(result);

  console.log(`Kind: ${result.policy.auditKind}`);
  console.log(`Layout: ${result.policy.layout}`);

  printSection("Geometry", result.sections.geometry);

  printSection("Colors", result.sections.colors);

  printSection("Typography", result.sections.typography);

  printSection("Spacing", result.sections.spacing);

  printSection("Raster", result.sections.raster);

  console.log("");

  console.log(`DESIGN MATCH: ${result.score.toFixed(2)}%`);

  console.log(`STATUS: ${result.status}`);

  if (result.status === "FAIL") {
    hasFailure = true;
  }
}

const averageScore =
  results.length === 0
    ? 0
    : results.reduce((sum, result) => sum + result.score, 0) / results.length;

const report = {
  schemaVersion: 1,

  generatedAt: new Date().toISOString(),

  filter: FILTER,

  thresholds: {
    pass: PASS_SCORE,

    warning: WARNING_SCORE,
  },

  weights: WEIGHTS,

  policies: AUDIT_POLICIES,

  summary: {
    total: results.length,

    passed: results.filter((result) => result.status === "PASS").length,

    warnings: results.filter((result) => result.status === "WARNING").length,

    failed: results.filter((result) => result.status === "FAIL").length,

    averageScore: round(averageScore, 2),
  },

  results,
};

fs.writeFileSync(
  REPORT_PATH,

  JSON.stringify(report, null, 2),
);

console.log("");

console.log("========================================");

console.log(`AVERAGE DESIGN MATCH: ${report.summary.averageScore.toFixed(2)}%`);

console.log(`PASS: ${report.summary.passed}`);

console.log(`WARNING: ${report.summary.warnings}`);

console.log(`FAIL: ${report.summary.failed}`);

console.log("========================================");

console.log("");

console.log(`Report: ${REPORT_PATH}`);

if (hasFailure) {
  process.exitCode = 1;
}
