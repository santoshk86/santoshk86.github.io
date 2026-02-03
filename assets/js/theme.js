const toggle = document.getElementById("theme-toggle");
const saved = localStorage.getItem("theme");

if (saved === "dark") document.body.classList.add("dark");

toggle.onclick = () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("theme",
    document.body.classList.contains("dark") ? "dark" : "light");
};
