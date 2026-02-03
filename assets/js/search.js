fetch('/search.json')
  .then(res => res.json())
  .then(data => {
    const input = document.getElementById("search-input");
    const results = document.getElementById("results");

    input.addEventListener("input", () => {
      results.innerHTML = "";
      data.filter(p => p.title.toLowerCase().includes(input.value.toLowerCase()))
        .forEach(p => {
          const li = document.createElement("li");
          li.innerHTML = `<a href="${p.url}">${p.title}</a>`;
          results.appendChild(li);
        });
    });
  });