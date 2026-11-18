
// Builds the right-rail table of contents from the lesson's h2 headings.
(function () {
  var toc = document.getElementById('toc-list');
  if (!toc) return;
  var heads = document.querySelectorAll('main h2');
  var used = {};
  heads.forEach(function (h) {
    if (h.closest('#objectives') || h.closest('.references')) return;
    if (!h.id) {
      var base = h.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50) || 'section';
      var id = base, n = 2;
      while (used[id] || document.getElementById(id)) { id = base + '-' + n++; }
      h.id = id;
    }
    used[h.id] = true;
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    a.title = h.textContent;
    li.appendChild(a);
    toc.appendChild(li);
  });
})();
