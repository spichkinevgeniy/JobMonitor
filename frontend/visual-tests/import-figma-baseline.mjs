import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import AdmZip from "adm-zip";

const ROOT = process.cwd();

const BASELINE_DIR = path.join(ROOT, "visual-artifacts", "figma-baseline");

const ZIP_PREFIX = "jobmonitor-figma-baseline";

const findLatestZip = () => {
  if (!fs.existsSync(BASELINE_DIR)) {
    throw new Error(`Baseline directory not found:\n${BASELINE_DIR}`);
  }

  const candidates = fs
    .readdirSync(BASELINE_DIR)
    .filter((fileName) => {
      const normalized = fileName.toLowerCase();

      return normalized.startsWith(ZIP_PREFIX) && normalized.endsWith(".zip");
    })
    .map((fileName) => {
      const filePath = path.join(BASELINE_DIR, fileName);

      const stats = fs.statSync(filePath);

      return {
        fileName,
        filePath,
        modifiedAt: stats.mtimeMs,
      };
    })
    .sort((a, b) => b.modifiedAt - a.modifiedAt);

  if (candidates.length === 0) {
    throw new Error(
      `Baseline ZIP not found in:\n${BASELINE_DIR}\n\n` +
        `Expected file like:\n${ZIP_PREFIX}.zip`,
    );
  }

  return candidates[0];
};

const validateZip = (zip) => {
  const entries = zip.getEntries().filter((entry) => !entry.isDirectory);

  const names = entries.map((entry) => entry.entryName.replace(/\\/g, "/"));

  const manifest = names.find((name) => name === "manifest.json");

  if (!manifest) {
    throw new Error(
      "Invalid baseline ZIP: manifest.json not found in archive root",
    );
  }

  const pngFiles = names.filter((name) => name.toLowerCase().endsWith(".png"));

  if (pngFiles.length === 0) {
    throw new Error("Invalid baseline ZIP: no PNG files found");
  }

  return {
    pngCount: pngFiles.length,
  };
};

const main = () => {
  console.log("");
  console.log("FIGMA BASELINE IMPORT");
  console.log("=====================");

  const latestZip = findLatestZip();

  console.log("");
  console.log(`ZIP: ${latestZip.fileName}`);

  /*
   * Сначала копируем ZIP во временную директорию.
   *
   * Это обязательно, потому что дальше
   * figma-baseline будет полностью удалён,
   * а оригинальный ZIP лежит именно внутри него.
   */
  const tempZipPath = path.join(
    os.tmpdir(),
    `jobmonitor-figma-baseline-${Date.now()}.zip`,
  );

  fs.copyFileSync(latestZip.filePath, tempZipPath);

  console.log("ZIP copied to temporary directory");

  try {
    /*
     * Проверяем архив ДО удаления старого baseline.
     */
    const zip = new AdmZip(tempZipPath);

    const { pngCount } = validateZip(zip);

    console.log(`PNG files: ${pngCount}`);

    /*
     * Удаляем старую папку целиком.
     *
     * Поэтому Windows больше не будет
     * спрашивать "Заменить существующий файл?".
     */
    fs.rmSync(BASELINE_DIR, {
      recursive: true,
      force: true,
    });

    fs.mkdirSync(BASELINE_DIR, {
      recursive: true,
    });

    console.log("Old baseline removed");

    /*
     * Распаковываем свежий baseline.
     */
    zip.extractAllTo(BASELINE_DIR, true);

    const manifestPath = path.join(BASELINE_DIR, "manifest.json");

    if (!fs.existsSync(manifestPath)) {
      throw new Error(
        `Import failed: manifest.json not found after extraction:\n${manifestPath}`,
      );
    }

    const extractedPngCount = fs
      .readdirSync(BASELINE_DIR)
      .filter((fileName) => fileName.toLowerCase().endsWith(".png")).length;

    console.log("New baseline extracted");

    console.log("");
    console.log(`Manifest: OK`);

    console.log(`PNG extracted: ${extractedPngCount}`);

    console.log("");
    console.log(`Destination:\n${BASELINE_DIR}`);

    console.log("");
    console.log("DONE");
  } finally {
    /*
     * Временный ZIP нам больше не нужен.
     */
    if (fs.existsSync(tempZipPath)) {
      fs.rmSync(tempZipPath, {
        force: true,
      });
    }
  }
};

try {
  main();
} catch (error) {
  console.error("");
  console.error("FIGMA BASELINE IMPORT FAILED");
  console.error("");

  console.error(error instanceof Error ? error.message : error);

  process.exitCode = 1;
}
