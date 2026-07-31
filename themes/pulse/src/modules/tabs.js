export function initTabs(root = document) {
  root.querySelectorAll("[data-ps-tabs]").forEach((tabs) => {
    if (tabs.dataset.bound === "1") return;
    tabs.dataset.bound = "1";

    const buttons = [...tabs.querySelectorAll("[data-ps-tab]")];
    const panels = [...tabs.querySelectorAll("[data-ps-panel]")];

    const activate = (id) => {
      buttons.forEach((btn) => {
        const on = btn.dataset.psTab === id;
        btn.classList.toggle("is-active", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.psPanel !== id;
      });
    };

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => activate(btn.dataset.psTab));
    });

    const initial = buttons.find((b) => b.classList.contains("is-active"))?.dataset.psTab || buttons[0]?.dataset.psTab;
    if (initial) activate(initial);
  });
}
