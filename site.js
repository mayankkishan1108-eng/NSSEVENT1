document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector("[data-menu-toggle]");
  const sidebar = document.querySelector("#sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("is-open");
      menuToggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("click", (event) => {
      if (window.innerWidth <= 700 && sidebar.classList.contains("is-open") &&
          !sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
        sidebar.classList.remove("is-open");
        menuToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  if (window.location.hash) {
    const target = document.querySelector(window.location.hash);
    if (target instanceof HTMLDetailsElement) target.open = true;
  }

  document.querySelectorAll(".attendance-cell input").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const label = checkbox.nextElementSibling;
      if (label) label.textContent = checkbox.checked ? "Present" : "Mark present";
    });
  });
});
