// Full tier only. Lays the message cards out like a comic page:
// 1st card top left, 2nd top right, 3rd under the 1st, 4th under the 2nd, and so on.
// Each column stacks its cards with no gaps. Without JavaScript the CSS falls back to plain columns.
(function () {
  var MIN_WIDTH = 280;   // narrowest card, in px (same as the CSS)
  var GAP = 12;          // space between columns, in px (same as the CSS)

  function setup(list) {
    var cards = Array.prototype.filter.call(list.children, function (el) {
      return el.classList.contains('post');
    });
    if (!cards.length) { return; }          // only the "no messages yet" line: nothing to lay out
    var columnCount = 0;

    function layout() {
      var count = Math.max(1, Math.floor((list.clientWidth + GAP) / (MIN_WIDTH + GAP)));
      if (count === columnCount) { return; }
      columnCount = count;

      var columns = [];
      for (var i = 0; i < count; i++) {
        var item = document.createElement('li');
        item.className = 'masonry-col';
        var inner = document.createElement('ul');
        inner.className = 'col-list';
        item.appendChild(inner);
        columns.push(inner);
      }
      cards.forEach(function (card, index) { columns[index % count].appendChild(card); });

      var old = list.querySelectorAll(':scope > .masonry-col');
      Array.prototype.forEach.call(old, function (el) { list.removeChild(el); });
      columns.forEach(function (col) { list.appendChild(col.parentNode); });
      list.setAttribute('data-columns', count);
    }

    layout();
    if (window.ResizeObserver) { new ResizeObserver(layout).observe(list); }
    else { window.addEventListener('resize', layout); }
  }

  Array.prototype.forEach.call(document.querySelectorAll('.cards'), setup);
})();
