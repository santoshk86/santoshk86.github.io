const toggle = document.getElementById("theme-toggle");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
const storedTheme = localStorage.getItem("theme");

/* Initial theme */
if (storedTheme === "dark" || (!storedTheme && prefersDark)) {
  document.body.classList.add("dark");
  toggle.textContent = "☀️";
} else {
  toggle.textContent = "🌙";
}

/* Toggle handler */
toggle.addEventListener("click", () => {
  const isDark = document.body.classList.toggle("dark");

  localStorage.setItem("theme", isDark ? "dark" : "light");
  toggle.textContent = isDark ? "☀️" : "🌙";
});
