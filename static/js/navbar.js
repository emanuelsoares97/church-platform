document.addEventListener("DOMContentLoaded", () => {

  const btn = document.querySelector(".navToggle");
  const menu = document.querySelector("#nav-menu");
  const overlay = document.querySelector("#nav-overlay");

  if (!btn || !menu || !overlay) return;

  const closeMenu = () => {

    menu.classList.remove("is-open");
    overlay.classList.remove("is-open");
    btn.classList.remove("is-open");

    document.body.classList.remove("nav-open");

    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-label", "Abrir menu");
  };

  const openMenu = () => {

    menu.classList.add("is-open");
    overlay.classList.add("is-open");
    btn.classList.add("is-open");

    document.body.classList.add("nav-open");

    btn.setAttribute("aria-expanded", "true");
    btn.setAttribute("aria-label", "Fechar menu");
  };

  btn.addEventListener("click", (e) => {

    e.stopPropagation();

    const isOpen = menu.classList.contains("is-open");

    isOpen ? closeMenu() : openMenu();

  });

  menu.addEventListener("click", (e) => {

    if (e.target.closest("a")) {
      closeMenu();
    }

  });

  overlay.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (e) => {

    if (e.key === "Escape") {
      closeMenu();
    }

  });

  window.addEventListener("resize", () => {

    if (window.innerWidth > 900) {
      closeMenu();
    }

  });

});

const header = document.querySelector(".siteHeader");

window.addEventListener("scroll", () => {

  if (window.scrollY > 40) {
    header.classList.add("scrolled");
  } else {
    header.classList.remove("scrolled");
  }

});
