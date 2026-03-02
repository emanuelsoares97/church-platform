document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector(".nav-toggle");
  const menu = document.querySelector("#nav-menu");
  if (!btn || !menu) return;

  const closeMenu = () => {
    menu.classList.remove("is-open");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-label", "Abrir menu");
  };

  const openMenu = () => {
    menu.classList.add("is-open");
    btn.setAttribute("aria-expanded", "true");
    btn.setAttribute("aria-label", "Fechar menu");
  };

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains("is-open");
    isOpen ? closeMenu() : openMenu();
  });

  // Fecha ao clicar num link
  menu.addEventListener("click", (e) => {
    if (e.target.closest("a")) closeMenu();
  });

  // Fecha ao clicar fora
  document.addEventListener("click", (e) => {
    if (e.target.closest(".topbarInner")) return;
    closeMenu();
  });

  // Fecha com ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  // Se sair do mobile, fecha
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) closeMenu();
  });
});