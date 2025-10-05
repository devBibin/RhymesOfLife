document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript is loaded and working!");

    let heading = document.getElementById("welcome-heading");
    if (heading) {
        heading.addEventListener("click", function () {
            heading.style.color = "red";
        });
    }
});

// Хедер
document.addEventListener('DOMContentLoaded', () => {
  const menuBtn  = document.querySelector('.header__nav-menu-btn');
  const nav      = document.querySelector('.header__nav');
  const closeBtn = document.querySelector('.close-menu');

  // Открыть/закрыть бургер
  if (menuBtn && nav){
    menuBtn.addEventListener('click', () => {
      nav.classList.toggle('active');
      document.body.classList.toggle('menu-open');
      menuBtn.setAttribute('aria-expanded', nav.classList.contains('active'));
    });
  }

  // Кнопка "×"
  if (closeBtn){
    closeBtn.addEventListener('click', () => {
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
      menuBtn && menuBtn.setAttribute('aria-expanded','false');
    });
  }

  // Делегирование на выпадашку "Классификация"
  document.addEventListener('click', e => {
    const toggle = e.target.closest('.dropdown-toggle');
    if (!toggle) return;

    e.preventDefault();
    const dropdown = toggle.closest('.dropdown');
    const menu     = dropdown.querySelector('.dropdown-menu');
    const open     = dropdown.classList.toggle('active');

    toggle.setAttribute('aria-expanded', open);
    // Автовысота для плавной анимации
    menu.style.maxHeight = open ? menu.scrollHeight + 'px' : 0;
  });

  // Закрываем меню при клике по пункту
  document.querySelectorAll('.header__nav-list-item-link, .dropdown-item').forEach(item=>{
    item.addEventListener('click', ()=>{
      nav.classList.remove('active');
      document.body.classList.remove('menu-open');
    });
  });
});