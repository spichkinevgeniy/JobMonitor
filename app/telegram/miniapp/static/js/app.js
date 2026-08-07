(function () {
  const webApp = window.Telegram && window.Telegram.WebApp;
  const telegramDebugInfo = () => {
    const hashKeys = [...new URLSearchParams(window.location.hash.slice(1)).keys()];
    // Порядок важен: сообщение обрезается, а решает первое поле. Пустой
    // tgWebAppData значит, что мини-апп открыли кнопкой reply-клавиатуры —
    // такому Telegram подписанные данные не передаёт.
    return JSON.stringify({
      tgWebAppData: hashKeys.includes("tgWebAppData"),
      initDataLength: webApp && webApp.initData ? webApp.initData.length : 0,
      sdk: Boolean(webApp),
      hashKeys,
      platform: webApp ? webApp.platform : null,
      version: webApp ? webApp.version : null,
    });
  };
  if (webApp) {
    webApp.ready();
    webApp.expand();
  }

  const statsRoot = document.querySelector("[data-stats-root]");
  if (statsRoot) {
    initStatsPage(statsRoot);
    return;
  }

  const form = document.querySelector("[data-miniapp-form]");
  if (!form) {
    return;
  }

  const statusNode = form.querySelector("[data-status]");
  const submitButton = form.querySelector("[data-submit-button]");
  const saveUrl = form.dataset.saveUrl;
  const pageKind = form.dataset.pageKind;
  const successText = form.dataset.successText || "Изменения сохранены.";
  const defaultButtonText = submitButton ? submitButton.textContent : "";
  const salaryAmountField = form.querySelector("[data-salary-amount-field]");
  const salaryAmountInput = form.querySelector("input[name='salary_amount_rub']");
  const salaryModeInputs = form.querySelectorAll("input[name='salary_mode']");
  const gradeModeInputs = form.querySelectorAll("input[name='grade_mode']");
  const experienceModeInputs = form.querySelectorAll("input[name='experience_mode']");
  let isLoaded = false;

  function setStatus(message, state) {
    if (!statusNode) {
      return;
    }

    statusNode.textContent = message || "";
    statusNode.classList.remove("is-error", "is-success");
    if (state === "error") {
      statusNode.classList.add("is-error");
    }
    if (state === "success") {
      statusNode.classList.add("is-success");
    }
  }

  function setSavingState(isSaving) {
    if (!submitButton) {
      return;
    }

    submitButton.disabled = isSaving;
    submitButton.textContent = isSaving ? "Сохраняем..." : defaultButtonText;
  }

  function setLoadingState(isLoading) {
    if (!submitButton) {
      return;
    }

    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading ? "Загружаем..." : defaultButtonText;
  }

  function getCheckedValues(name) {
    return Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map(
      (input) => input.value,
    );
  }

  function getCheckedValue(name) {
    const input = form.querySelector(`input[name="${name}"]:checked`);
    return input ? input.value : "";
  }

  function toggleSalaryAmountField() {
    if (!salaryAmountField) {
      return;
    }

    const shouldShow = getCheckedValue("salary_mode") === "FROM";
    salaryAmountField.hidden = !shouldShow;
    salaryAmountField.classList.toggle("is-hidden", !shouldShow);
    if (salaryAmountInput) {
      salaryAmountInput.disabled = !shouldShow;
    }
  }

  function toggleLevelValueSection(sectionKey, modeName) {
    const section = form.querySelector(`[data-level-values-section="${sectionKey}"]`);
    if (!section) {
      return;
    }

    const shouldHide = getCheckedValue(modeName) === "IGNORE";
    section.hidden = shouldHide;
    section.classList.toggle("is-hidden", shouldHide);
    section
      .querySelectorAll('input[type="radio"]')
      .forEach((input) => {
        input.disabled = shouldHide;
      });
  }

  function ensureLevelChoice(name) {
    const checkedInput = form.querySelector(`input[name="${name}"]:checked`);
    if (checkedInput && checkedInput.value !== "ANY") {
      return;
    }

    const firstRealOption = form.querySelector(`input[name="${name}"]:not([value="ANY"])`);
    if (firstRealOption) {
      firstRealOption.checked = true;
    }
  }

  function toggleLevelValueSections() {
    if (getCheckedValue("grade_mode") !== "IGNORE") {
      ensureLevelChoice("grade_choice");
    }
    if (getCheckedValue("experience_mode") !== "IGNORE") {
      ensureLevelChoice("experience_level_choice");
    }

    toggleLevelValueSection("grade", "grade_mode");
    toggleLevelValueSection("experience", "experience_mode");
  }

  function applyCheckedValues(name, values) {
    const checkedValues = new Set(Array.isArray(values) ? values : []);
    form.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
      input.checked = checkedValues.has(input.value);
    });
  }

  function applyCheckedValue(name, value) {
    form.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
      input.checked = input.value === value;
    });
  }

  function applyCurrentState(payload) {
    if (!payload || typeof payload !== "object") {
      return;
    }

    if (pageKind === "specialty") {
      applyCheckedValues("specializations", payload.specializations);
      applyCheckedValues("skills", payload.skills);
      return;
    }

    if (pageKind === "format") {
      applyCheckedValue("work_format_choice", payload.work_format_choice || "ANY");
      return;
    }

    if (pageKind === "salary") {
      applyCheckedValue("salary_mode", payload.salary_mode || "ANY");
      if (salaryAmountInput) {
        salaryAmountInput.value =
          payload.salary_amount_rub === null || payload.salary_amount_rub === undefined
            ? ""
            : String(payload.salary_amount_rub);
      }
      toggleSalaryAmountField();
      return;
    }

    if (pageKind === "level") {
      applyCheckedValue("grade_mode", payload.grade_mode || "IGNORE");
      applyCheckedValue("grade_choice", payload.grade_choice || "ANY");
      applyCheckedValue("experience_mode", payload.experience_mode || "IGNORE");
      applyCheckedValue("experience_level_choice", payload.experience_level_choice || "ANY");
      toggleLevelValueSections();
    }
  }

  function buildPayload() {
    if (pageKind === "specialty") {
      return {
        specializations: getCheckedValues("specializations"),
        skills: getCheckedValues("skills"),
      };
    }

    if (pageKind === "format") {
      return {
        work_format_choice: getCheckedValue("work_format_choice") || "ANY",
      };
    }

    if (pageKind === "salary") {
      const salaryMode = getCheckedValue("salary_mode") || "ANY";
      const rawAmount = salaryAmountInput ? salaryAmountInput.value.trim() : "";
      const parsedAmount = rawAmount ? Number.parseInt(rawAmount, 10) : null;
      return {
        salary_mode: salaryMode,
        salary_amount_rub: salaryMode === "FROM" ? parsedAmount : null,
      };
    }

    if (pageKind === "level") {
      return {
        grade_mode: getCheckedValue("grade_mode") || "IGNORE",
        grade_choice: getCheckedValue("grade_choice") || "ANY",
        experience_mode: getCheckedValue("experience_mode") || "IGNORE",
        experience_level_choice: getCheckedValue("experience_level_choice") || "ANY",
      };
    }

    return {};
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!isLoaded) {
      setStatus("Дождитесь загрузки актуальных значений.", "error");
      return;
    }

    if (!saveUrl) {
      setStatus("Не найден адрес сохранения.", "error");
      return;
    }

    if (!webApp || !webApp.initData) {
      setStatus(`Откройте mini-app из Telegram. ${telegramDebugInfo()}`, "error");
      return;
    }

    setSavingState(true);
    setStatus("");

    try {
      const response = await fetch(saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          init_data: webApp.initData,
          ...buildPayload(),
        }),
      });

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        const message =
          result && typeof result.detail === "string"
            ? result.detail
            : "Не удалось сохранить изменения.";
        setStatus(message, "error");
        return;
      }

      const message =
        result && typeof result.message === "string" ? result.message : successText;
      setStatus(message, "success");
      window.setTimeout(() => {
        if (webApp && typeof webApp.close === "function") {
          webApp.close();
        }
      }, 300);
    } catch {
      setStatus("Ошибка сети. Попробуйте еще раз.", "error");
    } finally {
      setSavingState(false);
    }
  }

  async function loadCurrentState() {
    if (!saveUrl) {
      setStatus("Не найден адрес загрузки.", "error");
      return;
    }

    if (!webApp || !webApp.initData) {
      setStatus(`Откройте mini-app из Telegram. ${telegramDebugInfo()}`, "error");
      return;
    }

    setLoadingState(true);
    setStatus("Загружаем актуальные значения...");

    try {
      const response = await fetch(saveUrl, {
        method: "GET",
        headers: {
          "X-Telegram-Init-Data": webApp.initData,
        },
      });

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        const message =
          result && typeof result.detail === "string"
            ? result.detail
            : "Не удалось загрузить актуальные значения.";
        setStatus(message, "error");
        return;
      }

      applyCurrentState(result);
      isLoaded = true;
      setStatus("");
    } catch {
      setStatus("Ошибка загрузки. Попробуйте открыть форму еще раз.", "error");
    } finally {
      setLoadingState(false);
    }
  }

  form.addEventListener("submit", handleSubmit);
  salaryModeInputs.forEach((input) => {
    input.addEventListener("change", toggleSalaryAmountField);
  });
  gradeModeInputs.forEach((input) => {
    input.addEventListener("change", toggleLevelValueSections);
  });
  experienceModeInputs.forEach((input) => {
    input.addEventListener("change", toggleLevelValueSections);
  });
  toggleSalaryAmountField();
  toggleLevelValueSections();
  loadCurrentState();

  function initStatsPage(root) {
    const statusNode = root.querySelector("[data-stats-status]");
    const cardsNode = root.querySelector("[data-stats-cards]");
    const emptyNode = root.querySelector("[data-stats-empty]");
    const noDataNode = root.querySelector("[data-stats-no-data]");
    const statsUrl = root.dataset.statsUrl;
    const exportUrl = root.dataset.exportUrl;

    function setStatsStatus(message, state) {
      if (!statusNode) {
        return;
      }
      statusNode.textContent = message || "";
      statusNode.classList.remove("is-error");
      if (state === "error") {
        statusNode.classList.add("is-error");
      }
    }

    const DENSE_CHART_THRESHOLD = 10;
    let trendSeries = [];
    let toggleButtons = [];
    let activeGranularity = "";
    let selectedPointIndex = -1;

    function buildTrendToggle() {
      const toggleNode = root.querySelector("[data-stats-toggle]");
      if (!toggleNode) {
        return;
      }
      toggleNode.textContent = "";
      toggleButtons = [];
      if (trendSeries.length < 2) {
        toggleNode.classList.add("is-hidden");
        return;
      }
      toggleNode.classList.remove("is-hidden");
      trendSeries.forEach((series) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "trend-toggle__item";
        button.textContent = series.toggle_label;
        button.dataset.granularity = series.granularity;
        button.addEventListener("click", () => {
          if (series.granularity === activeGranularity) {
            return;
          }
          activeGranularity = series.granularity;
          selectedPointIndex = -1;
          syncTrendToggle();
          renderTrendChart();
        });
        toggleButtons.push(button);
        toggleNode.append(button);
      });
      syncTrendToggle();
    }

    // Обновляем состояние на месте, не пересоздавая кнопки: иначе при работе
    // с клавиатуры фокус слетает с нажатой кнопки.
    function syncTrendToggle() {
      toggleButtons.forEach((button) => {
        const isActive = button.dataset.granularity === activeGranularity;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
      });
    }

    function selectTrendPoint(index) {
      selectedPointIndex = selectedPointIndex === index ? -1 : index;
      const columns = root.querySelectorAll("[data-stats-chart] .stats-chart__col");
      columns.forEach((column, columnIndex) => {
        const isSelected = columnIndex === selectedPointIndex;
        column.classList.toggle("is-selected", isSelected);
        column.setAttribute("aria-pressed", String(isSelected));
      });
    }

    function renderTrendChart() {
      const chartNode = root.querySelector("[data-stats-chart]");
      const fromNode = root.querySelector("[data-stats-chart-from]");
      const headlineValueNode = root.querySelector("[data-stats-headline-value]");
      const headlineLabelNode = root.querySelector("[data-stats-headline-label]");
      const series = trendSeries.find((item) => item.granularity === activeGranularity);
      if (!chartNode || !series) {
        return;
      }

      const points = series.points;
      const lastPoint = points.length > 0 ? points[points.length - 1] : null;
      if (headlineValueNode) {
        headlineValueNode.textContent = lastPoint ? String(lastPoint.count) : "0";
      }
      if (headlineLabelNode) {
        headlineLabelNode.textContent = series.headline_label;
      }

      chartNode.textContent = "";
      chartNode.classList.toggle("stats-chart--dense", points.length > DENSE_CHART_THRESHOLD);
      const maxCount = points.reduce((max, point) => Math.max(max, point.count), 0);

      points.forEach((point, index) => {
        const column = document.createElement("button");
        column.type = "button";
        column.className = "stats-chart__col";
        column.setAttribute("aria-pressed", "false");
        column.setAttribute("aria-label", `${point.label}: ${point.count}`);

        const value = document.createElement("span");
        value.className = "stats-chart__value";
        value.textContent = String(point.count);

        const bar = document.createElement("div");
        bar.className = "stats-chart__bar";
        const ratio = maxCount > 0 ? point.count / maxCount : 0;
        bar.style.height = `${Math.max(ratio * 100, point.count > 0 ? 6 : 2)}%`;

        const tip = document.createElement("span");
        tip.className = "stats-chart__tip";
        tip.textContent = point.label;

        column.append(value, bar, tip);
        column.addEventListener("click", () => selectTrendPoint(index));
        chartNode.append(column);
      });

      if (fromNode && points.length > 0) {
        fromNode.textContent = `с ${points[0].label}`;
      }
    }

    function renderTrend(series) {
      trendSeries = Array.isArray(series) ? series : [];
      activeGranularity = trendSeries.length > 0 ? trendSeries[0].granularity : "";
      selectedPointIndex = -1;
      buildTrendToggle();
      renderTrendChart();
    }

    function pluralize(amount, one, few, many) {
      const mod100 = amount % 100;
      if (mod100 >= 11 && mod100 <= 14) {
        return many;
      }
      const mod10 = amount % 10;
      if (mod10 === 1) {
        return one;
      }
      if (mod10 >= 2 && mod10 <= 4) {
        return few;
      }
      return many;
    }

    function renderExport(exportInfo) {
      const cardNode = root.querySelector("[data-stats-export-card]");
      const introNode = root.querySelector("[data-stats-export-intro]");
      const statusNode = root.querySelector("[data-stats-export-status]");
      if (!cardNode || !introNode) {
        return;
      }
      if (!exportInfo || !exportInfo.count) {
        cardNode.classList.add("is-hidden");
        return;
      }

      cardNode.classList.remove("is-hidden");
      const word = pluralize(exportInfo.count, "вакансию", "вакансии", "вакансий");
      introNode.textContent = `Выгрузить ${exportInfo.count} ${word} файлом:`;
      root.querySelectorAll("[data-export-format]").forEach((button) => {
        button.addEventListener("click", () => sendExport(button, statusNode));
      });
    }

    async function sendExport(button, statusNode) {
      if (!exportUrl || !webApp || !webApp.initData) {
        return;
      }

      const buttons = root.querySelectorAll("[data-export-format]");
      buttons.forEach((item) => {
        item.disabled = true;
      });
      if (statusNode) {
        statusNode.textContent = "Готовим файл...";
        statusNode.classList.remove("is-error", "is-success");
      }

      try {
        const response = await fetch(exportUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            init_data: webApp.initData,
            export_format: button.dataset.exportFormat,
          }),
        });
        const result = await response.json().catch(() => null);
        if (!statusNode) {
          return;
        }
        if (!response.ok) {
          statusNode.textContent =
            result && typeof result.detail === "string"
              ? result.detail
              : "Не удалось сформировать файл.";
          statusNode.classList.add("is-error");
          return;
        }
        statusNode.textContent = result && result.message ? result.message : "Файл отправлен.";
        statusNode.classList.add("is-success");
      } catch {
        if (statusNode) {
          statusNode.textContent = "Ошибка отправки. Попробуйте ещё раз.";
          statusNode.classList.add("is-error");
        }
      } finally {
        buttons.forEach((item) => {
          item.disabled = false;
        });
      }
    }

    function renderAdvice(result) {
      const cardNode = root.querySelector("[data-stats-advice-card]");
      const titleNode = root.querySelector("[data-stats-advice-title]");
      const listNode = root.querySelector("[data-stats-advice-list]");
      if (!cardNode || !listNode) {
        return;
      }
      const items = result.skill_suggestions || [];
      if (!items.length) {
        cardNode.classList.add("is-hidden");
        return;
      }

      cardNode.classList.remove("is-hidden");
      if (titleNode) {
        const funnel = result.funnel || {};
        titleNode.textContent = `Сейчас подходит ${funnel.rows && funnel.rows.length ? funnel.rows[0].count : 0} из ${funnel.total || 0}`;
      }

      listNode.textContent = "";
      items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "advice-row";

        const skill = document.createElement("span");
        skill.className = "advice-row__skill";
        skill.textContent = item.skill;

        const unlocks = document.createElement("span");
        unlocks.className = "advice-row__unlocks";
        unlocks.textContent = `+${item.unlocks}`;

        row.append(skill, unlocks);
        listNode.append(row);
      });
    }

    function renderFunnel(funnel) {
      const cardNode = root.querySelector("[data-stats-funnel-card]");
      const barNode = root.querySelector("[data-stats-funnel-bar]");
      const listNode = root.querySelector("[data-stats-funnel-list]");
      const totalNode = root.querySelector("[data-stats-funnel-total]");
      if (!cardNode || !barNode || !listNode) {
        return;
      }
      if (!funnel || !funnel.total) {
        cardNode.classList.add("is-hidden");
        return;
      }

      cardNode.classList.remove("is-hidden");
      barNode.textContent = "";
      listNode.textContent = "";

      funnel.rows.forEach((row, index) => {
        const tone = `funnel-tone-${Math.min(index, 4)}`;

        const segment = document.createElement("div");
        segment.className = `funnel-bar__seg ${tone}`;
        segment.style.width = `${row.percent}%`;
        barNode.append(segment);

        const listRow = document.createElement("div");
        listRow.className = "funnel-row";

        const dot = document.createElement("span");
        dot.className = `funnel-row__dot ${tone}`;

        const name = document.createElement("span");
        name.className = "funnel-row__name";
        name.textContent = row.label;

        const count = document.createElement("span");
        count.className = "funnel-row__num";
        count.textContent = String(row.count);

        listRow.append(dot, name, count);
        listNode.append(listRow);
      });

      if (totalNode) {
        totalNode.textContent = String(funnel.total);
      }
    }

    function renderCompanyBreakdown(data) {
      const listNode = root.querySelector("[data-stats-company]");
      const cardNode = root.querySelector("[data-stats-company-card]");
      const totalNode = root.querySelector("[data-stats-company-total]");
      if (!listNode || !cardNode) {
        return;
      }
      if (!data.company_breakdown.length) {
        cardNode.classList.add("is-hidden");
        return;
      }
      cardNode.classList.remove("is-hidden");
      listNode.textContent = "";
      data.company_breakdown.forEach((item) => {
        const row = document.createElement("div");
        row.className = "stats-bar-row";

        const label = document.createElement("div");
        label.className = "stats-bar-row__label";
        const name = document.createElement("b");
        name.textContent = item.label;
        const share = document.createElement("span");
        share.textContent = `${item.percent}%`;
        label.append(name, share);

        const track = document.createElement("div");
        track.className = "stats-bar-row__track";
        const fill = document.createElement("div");
        fill.className = "stats-bar-row__fill";
        fill.style.width = `${item.percent}%`;
        track.append(fill);

        row.append(label, track);
        listNode.append(row);
      });
      if (totalNode) {
        totalNode.textContent = `Всего вакансий в выборке: ${data.company_total}.`;
      }
    }

    async function loadStats() {
      if (!statsUrl) {
        setStatsStatus("Не найден адрес аналитики.", "error");
        return;
      }
      if (!webApp || !webApp.initData) {
        setStatsStatus(`Откройте mini-app из Telegram. ${telegramDebugInfo()}`, "error");
        return;
      }

      try {
        const response = await fetch(statsUrl, {
          method: "GET",
          headers: {
            "X-Telegram-Init-Data": webApp.initData,
          },
        });
        const result = await response.json().catch(() => null);
        if (!response.ok) {
          const message =
            result && typeof result.detail === "string"
              ? result.detail
              : "Не удалось загрузить аналитику.";
          setStatsStatus(message, "error");
          return;
        }

        setStatsStatus("");
        // Выгрузку показываем всегда: она про уже полученные вакансии и не
        // зависит от того, заполнен ли профиль сейчас.
        renderExport(result.export);

        if (!result.has_profile) {
          if (emptyNode) {
            emptyNode.classList.remove("is-hidden");
          }
          return;
        }

        // Профиль есть, но окна пустые: рисовать нули во всех карточках честнее
        // не показывать вовсе, иначе выглядит как сломанная аналитика.
        if (!result.has_data) {
          if (noDataNode) {
            noDataNode.classList.remove("is-hidden");
          }
          return;
        }

        renderTrend(result.trends);
        renderFunnel(result.funnel);
        renderAdvice(result);
        renderCompanyBreakdown(result);
        if (cardsNode) {
          cardsNode.classList.remove("is-hidden");
        }
      } catch {
        setStatsStatus("Ошибка загрузки. Попробуйте открыть аналитику еще раз.", "error");
      }
    }

    loadStats();
  }
})();
