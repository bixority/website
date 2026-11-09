// Progressive enhancement only: every page works without this file.

// Opened straight from disk (file://), a link to "services/" shows a folder
// listing instead of the page, so point such links at the index.html inside,
// keeping any #fragment. On the web server these stay clean URLs.
if (location.protocol === "file:") {
  for (const link of document.querySelectorAll("a[href]")) {
    const href = link.getAttribute("href");
    if (/^[a-z][a-z0-9+.-]*:|^\/\//i.test(href)) continue;
    const [path, hash] = href.split("#");
    if (path.endsWith("/")) {
      link.setAttribute("href", path + "index.html" + (hash === undefined ? "" : "#" + hash));
    }
  }
}
