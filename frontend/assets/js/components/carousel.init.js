// Controla el carrusel de metricas; es decir, la navegacion via dots, deteccion del slide visible mediante IntersectionObserver, y auto-rotacion que se desactiva por completo si el usuario prefiere menos movimiento, no solo se hace mas lenta.

(function () {
  const carousel = document.querySelector("[data-carousel]");
  if (!carousel) return;

  const track = carousel.querySelector("[data-carousel-track]");
  const slides = Array.from(carousel.querySelectorAll("[data-carousel-slide]"));
  const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  let currentIndex = 0;
  let autoRotateTimer = null;

  function setActiveDot(index) {
    dots.forEach(function (dot, i) {
      const isActive = i === index;
      dot.classList.toggle("carousel__dot--active", isActive);
      dot.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    currentIndex = index;
  }

  function goToSlide(index) {
    const slide = slides[index];
    if (!slide) return;
    // Solo ejecuta scrollIntoView si el carousel esta dentro del viewport.
    // Si esta fuera (por ejemplo el usuario bajo al footer), avanza el indice
    // logico sin mover la pagina, para que al volver vea el slide correcto.
    const rect = carousel.getBoundingClientRect();
    const inViewport = rect.top >= 0 && rect.bottom <= window.innerHeight;
    if (inViewport) {
      slide.scrollIntoView({
        behavior: prefersReducedMotion ? "auto" : "smooth",
        inline: "start",
        block: "nearest",
      });
    } else {
      setActiveDot(index);
    }
  }

  dots.forEach(function (dot, index) {
    dot.addEventListener("click", function () {
      goToSlide(index);
      stopAutoRotate();
    });
  });

  // IntersectionObserver detecta cual slide esta realmente visible cuando el usuario hace swipe manual, manteniendo los dots sincronizados sin depender de calculos manuales de scroll.
  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
          const index = slides.indexOf(entry.target);
          if (index !== -1) {
            setActiveDot(index);
          }
        }
      });
    },
    { root: track, threshold: 0.5 },
  );

  slides.forEach(function (slide) {
    observer.observe(slide);
  });

  function startAutoRotate() {
    if (prefersReducedMotion || autoRotateTimer) return;
    autoRotateTimer = setInterval(function () {
      const nextIndex = (currentIndex + 1) % slides.length;
      goToSlide(nextIndex);
    }, 4000);
  }

  function stopAutoRotate() {
    if (autoRotateTimer) {
      clearInterval(autoRotateTimer);
      autoRotateTimer = null;
    }
  }

  // IntersectionObserver sobre el carousel completo: detiene el auto-rotate
  // cuando el carousel sale del viewport y lo reanuda cuando entra.
  // Esto reemplaza los listeners de mouseenter/mouseleave/touchstart.
  const visibilityObserver = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          startAutoRotate();
        } else {
          stopAutoRotate();
        }
      });
    },
    { threshold: 0.1 },
  );

  visibilityObserver.observe(carousel);
})();
