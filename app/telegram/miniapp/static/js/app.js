(function () {
  const webApp = window.Telegram && window.Telegram.WebApp;
  const telegramDebugInfo = () =>
    JSON.stringify({
      sdk: Boolean(webApp),
      initDataLength: webApp && webApp.initData ? webApp.initData.length : 0,
      hashLength: window.location.hash.length,
      hasTgWebAppData: new URLSearchParams(window.location.hash.slice(1)).has("tgWebAppData"),
      platform: webApp ? webApp.platform : null,
      version: webApp ? webApp.version : null,
    });
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
    const statsUrl = root.dataset.statsUrl;

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

    function renderWeekCard(data) {
      const countNode = root.querySelector("[data-stats-week-count]");
      const deltaNode = root.querySelector("[data-stats-delta]");
      if (countNode) {
        countNode.textContent = String(data.current_week_count);
      }
      if (!deltaNode) {
        return;
      }
      if (data.delta_percent === null || data.delta_percent === undefined) {
        deltaNode.classList.add("is-hidden");
        return;
      }
      const isUp = data.delta_percent >= 0;
      deltaNode.textContent = `${isUp ? "▲" : "▼"} ${isUp ? "+" : ""}${data.delta_percent}% к пред. неделе`;
      deltaNode.classList.remove("is-hidden", "is-up", "is-down");
      deltaNode.classList.add(isUp ? "is-up" : "is-down");
    }

    function renderTrend(points) {
      const chartNode = root.querySelector("[data-stats-chart]");
      const fromNode = root.querySelector("[data-stats-chart-from]");
      if (!chartNode) {
        return;
      }
      chartNode.textContent = "";
      const maxCount = points.reduce((max, point) => Math.max(max, point.count), 0);
      points.forEach((point) => {
        const column = document.createElement("div");
        column.className = "stats-chart__col";
        column.title = `${point.week_label}: ${point.count}`;

        const bar = document.createElement("div");
        bar.className = "stats-chart__bar";
        const ratio = maxCount > 0 ? point.count / maxCount : 0;
        bar.style.height = `${Math.max(ratio * 100, point.count > 0 ? 6 : 2)}%`;

        const value = document.createElement("span");
        value.className = "stats-chart__value";
        value.textContent = String(point.count);

        column.append(value, bar);
        chartNode.append(column);
      });
      if (fromNode && points.length > 0) {
        fromNode.textContent = `с ${points[0].week_label}`;
      }
    }

    function renderCompanyBreakdown(data) {
      const listNode = root.querySelector("[data-stats-company]");
      const cardNode = root.querySelector("[data-stats-company-card]");
      const noteNode = root.querySelector("[data-stats-company-note]");
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
      if (noteNode) {
        noteNode.textContent = `Всего вакансий в выборке: ${data.company_total}. Тип определяется автоматически по тексту вакансии — иногда данных не хватает.`;
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
        if (!result.has_profile) {
          if (emptyNode) {
            emptyNode.classList.remove("is-hidden");
          }
          return;
        }

        renderWeekCard(result);
        renderTrend(result.trend);
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
