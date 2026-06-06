// ── ShopZen Main JS ──

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss toasts ──
  document.querySelectorAll('.toast').forEach(function (toast) {
    toast.addEventListener('click', function () { this.remove(); });
    setTimeout(function () {
      toast.style.transition = 'opacity 0.3s, transform 0.3s';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(110%)';
      setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
  });

  // ── Live Search ──
  var searchInput = document.getElementById('nav-search-input');
  var suggestions = document.getElementById('search-suggestions');
  if (searchInput && suggestions) {
    var timeout;
    searchInput.addEventListener('input', function () {
      clearTimeout(timeout);
      var q = this.value.trim();
      if (q.length < 2) { suggestions.classList.remove('show'); return; }
      timeout = setTimeout(function () {
        fetch('/api/search?q=' + encodeURIComponent(q))
          .then(function(r) { return r.json(); })
          .then(function (data) {
            suggestions.innerHTML = '';
            if (!data.length) { suggestions.classList.remove('show'); return; }
            data.forEach(function (item) {
              var div = document.createElement('div');
              div.className = 'suggestion-item';
              div.innerHTML =
                '<img src="' + item.image + '" alt="" onerror="this.src=\'https://via.placeholder.com/40\'">' +
                '<div><div style="font-weight:600;font-size:13px">' + item.name + '</div>' +
                '<div style="color:#888;font-size:12px">₹' + parseInt(item.price).toLocaleString('en-IN') + '</div></div>';
              div.addEventListener('click', function () { window.location.href = '/product/' + item.id; });
              suggestions.appendChild(div);
            });
            suggestions.classList.add('show');
          });
      }, 280);
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-search')) suggestions.classList.remove('show');
    });
  }

  // ── Tabs ──
  document.querySelectorAll('.tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      var target = this.dataset.tab;
      var container = this.closest('.tabs-container');
      if (!container) return;
      container.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
      container.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
      this.classList.add('active');
      var panel = container.querySelector('#' + target);
      if (panel) panel.classList.add('active');
    });
  });

  // ── Cart qty buttons ──
  document.querySelectorAll('.qty-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = this.parentElement.querySelector('.qty-input');
      var val = parseInt(input.value) || 1;
      if (this.dataset.action === 'inc') input.value = val + 1;
      else if (this.dataset.action === 'dec' && val > 1) input.value = val - 1;
    });
  });

  // ── Star rating input ──
  document.querySelectorAll('.star-rating-input').forEach(function (wrap) {
    var btns  = wrap.querySelectorAll('.star-btn');
    var input = wrap.querySelector('input[name="rating"]');
    if (!input) return;
    function paint(n) {
      btns.forEach(function(b, i) { b.style.color = i < n ? '#f59e0b' : '#d1d5db'; });
    }
    paint(parseInt(input.value) || 5);
    btns.forEach(function (btn, idx) {
      btn.addEventListener('mouseenter', function () { paint(idx + 1); });
      btn.addEventListener('mouseleave', function () { paint(parseInt(input.value) || 0); });
      btn.addEventListener('click', function () { input.value = idx + 1; paint(idx + 1); });
    });
  });

  // ── Confirm delete ──
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });

});
