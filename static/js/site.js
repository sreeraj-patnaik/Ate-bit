(function () {
  var btn = document.getElementById('menu-toggle');
  var menu = document.getElementById('mobile-menu');
  if (btn && menu) {
    btn.addEventListener('click', function () {
      menu.classList.toggle('open');
    });
  }

  var urgencyModal = document.getElementById('urgency-modal');
  if (urgencyModal) {
    urgencyModal.classList.add('open');

    var closeBtn = document.getElementById('close-urgency-modal');
    var closeBackdrop = urgencyModal.querySelector('[data-close-urgency-modal]');

    function closeModal() {
      urgencyModal.classList.remove('open');
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (closeBackdrop) closeBackdrop.addEventListener('click', closeModal);

    var openBtn = document.getElementById('open-urgency-modal');
    var openBtnMobile = document.getElementById('open-urgency-modal-mobile');
    function openModal() {
      urgencyModal.classList.add('open');
    }
    if (openBtn) openBtn.addEventListener('click', openModal);
    if (openBtnMobile) openBtnMobile.addEventListener('click', openModal);

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeModal();
    });
  }
})();
