if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker
      .register("/sw.js")
      .then(function (registration) {
        console.log("Service Worker registado:", registration.scope);
      })
      .catch(function (error) {
        console.log("Erro SW:", error);
      });
  });
}

let deferredPrompt = null;

const installBtn = document.getElementById("installAppBtn");
const iosInstallModal = document.getElementById("iosInstallModal");
const closeInstallModal = document.getElementById("closeInstallModal");
const iosInstallText = document.getElementById("iosInstallText");
const iosBrowserHelp = document.getElementById("iosBrowserHelp");

const userAgent = window.navigator.userAgent;
const userAgentLower = userAgent.toLowerCase();

const isIos = /iphone|ipad|ipod/.test(userAgentLower);
const isAndroid = /android/.test(userAgentLower);
const isMobile = isIos || isAndroid;

const isIosChrome = /crios/i.test(userAgent);
const isIosEdge = /edgios/i.test(userAgent);
const isIosFirefox = /fxios/i.test(userAgent);
const isIosOpera = /opios/i.test(userAgent);

const isSafari =
  isIos &&
  /safari/i.test(userAgent) &&
  !isIosChrome &&
  !isIosEdge &&
  !isIosFirefox &&
  !isIosOpera;

const isInStandaloneMode =
  window.matchMedia("(display-mode: standalone)").matches ||
  window.navigator.standalone === true;

if (installBtn && isMobile && !isInStandaloneMode) {
  installBtn.hidden = false;
}

window.addEventListener("beforeinstallprompt", function (event) {
  event.preventDefault();
  deferredPrompt = event;

  if (installBtn && isMobile && !isInStandaloneMode) {
    installBtn.hidden = false;
  }
});

function openIosInstallModal() {
  if (!iosInstallModal) {
    return;
  }

  if (iosInstallText) {
    if (isSafari) {
      iosInstallText.textContent = "No iPhone, para instalares a app:";
    } else {
      iosInstallText.textContent =
        "No iPhone, se estiveres a usar Chrome ou outro browser, abre este site no Safari para instalar a app:";
    }
  }

  if (iosBrowserHelp) {
    if (isSafari) {
      iosBrowserHelp.hidden = true;
    } else {
      iosBrowserHelp.hidden = false;
    }
  }

  iosInstallModal.hidden = false;
}

if (installBtn) {
  installBtn.addEventListener("click", async function () {
    if (isIos) {
      openIosInstallModal();
      return;
    }

    if (!deferredPrompt) {
      return;
    }

    deferredPrompt.prompt();

    const choiceResult = await deferredPrompt.userChoice;

    if (choiceResult.outcome === "accepted") {
      console.log("Utilizador aceitou instalar a app.");
    } else {
      console.log("Utilizador recusou instalar a app.");
    }

    deferredPrompt = null;
    installBtn.hidden = true;
  });
}

if (closeInstallModal) {
  closeInstallModal.addEventListener("click", function () {
    if (iosInstallModal) {
      iosInstallModal.hidden = true;
    }
  });
}

if (iosInstallModal) {
  iosInstallModal.addEventListener("click", function (event) {
    if (event.target === iosInstallModal) {
      iosInstallModal.hidden = true;
    }
  });
}

window.addEventListener("appinstalled", function () {
  console.log("App instalada com sucesso.");

  if (installBtn) {
    installBtn.hidden = true;
  }
});