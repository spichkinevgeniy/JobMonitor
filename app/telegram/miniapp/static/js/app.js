(function () {
  const webApp = window.Telegram && window.Telegram.WebApp;
  if (webApp) {
    webApp.ready();
    webApp.expand();
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
      applyCheckedValue("grade_choice", payload.grade_choice || "ANY");
      applyCheckedValue("experience_level_choice", payload.experience_level_choice || "ANY");
      return;
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
        grade_choice: getCheckedValue("grade_choice") || "ANY",
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
      setStatus("Откройте mini-app из Telegram.", "error");
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
      setStatus("Откройте mini-app из Telegram.", "error");
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
  toggleSalaryAmountField();
  loadCurrentState();
})();
