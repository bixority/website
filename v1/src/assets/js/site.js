// Progressive enhancement only: every page works without this file.

// Opened straight from disk (file://), a link to "services/" shows a folder
// listing instead of the page, so point such links at the index.html inside.
// On the web server these stay clean URLs.
if (location.protocol === "file:") {
  for (const link of document.querySelectorAll("a[href]")) {
    const href = link.getAttribute("href");
    if (href.endsWith("/") && !/^[a-z][a-z0-9+.-]*:|^\/\//i.test(href)) {
      link.setAttribute("href", href + "index.html");
    }
  }
}

// Copy buttons: <button data-copy="text" hidden>, status in [data-copy-status].
for (const button of document.querySelectorAll("button[data-copy]")) {
  const status = button.parentElement.querySelector("[data-copy-status]");
  button.hidden = false;
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      if (status) status.textContent = button.dataset.done;
    } catch {
      const target = document.getElementById(button.dataset.target);
      if (target) window.getSelection().selectAllChildren(target);
      if (status) status.textContent = button.dataset.failed;
    }
  });
}
