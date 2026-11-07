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

// The page change (site.css, VIEW TRANSITIONS): the mark stays out of the motion when less than two thirds of it is
// on screen, on the page being left or the page being opened, and when the page being opened was restored scrolled
// (Back, Forward), where the home's mark may be split and grey. Without this file only those cases look worse.
const mark = document.querySelector(".mark");
if (mark) {
  const keepOut = (event, scrolled) => {
    const types = event.viewTransition?.types;
    if (!types) return;
    const r = mark.getBoundingClientRect();
    if (scrolled || Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) < r.height * 2 / 3) types.add("mark-off");
  };
  addEventListener("pageswap", (event) => keepOut(event, false));
  addEventListener("pagereveal", (event) => keepOut(event, scrollY > 0));
}
