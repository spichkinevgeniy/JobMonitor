// Просмотр главной засчитываем, только когда страницу открыл браузер и она
// пробыла на экране пару секунд: роботы обычно не выполняют скрипты или
// уходят сразу. Счёт пишет POST /miniapp/api/market/view.
(function () {
  const url = "/miniapp/api/market/view";
  let sent = false;

  const send = () => {
    if (sent || document.visibilityState !== "visible") {
      return;
    }
    sent = true;
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url);
    } else {
      fetch(url, { method: "POST", keepalive: true });
    }
  };

  setTimeout(() => {
    send();
    // Открыли во фоновой вкладке — засчитаем, когда на неё переключатся.
    if (!sent) {
      document.addEventListener("visibilitychange", send);
    }
  }, 2000);
})();
