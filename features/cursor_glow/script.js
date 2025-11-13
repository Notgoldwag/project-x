// Cursor Glow Feature - Smooth cursor follower effect
(function () {
  'use strict';

  const glow = document.getElementById('cursor-glow');
  if (!glow) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let targetX = window.innerWidth / 2, targetY = window.innerHeight / 2;
  let currentX = targetX, currentY = targetY;
  const lerp = (a, b, n) => (1 - n) * a + n * b;
  const ease = 0.14; // follow speed

  function onLeave() { glow.style.opacity = '0.0'; }
  function onEnter() { glow.style.opacity = '0.8'; }
  window.addEventListener('mouseleave', onLeave);
  window.addEventListener('mouseenter', onEnter);

  window.addEventListener('mousemove', (e) => {
    targetX = e.clientX;
    targetY = e.clientY;
    if (!reduceMotion) glow.style.opacity = '0.85';
    clearTimeout(window.__glowIdleTimer);
    window.__glowIdleTimer = setTimeout(() => {
      glow.style.opacity = '0.65';
    }, 900);
  }, { passive: true });

  function animate() {
    if (reduceMotion) {
      glow.style.transform = `translate(${targetX - 150}px, ${targetY - 150}px)`;
    } else {
      currentX = lerp(currentX, targetX, ease);
      currentY = lerp(currentY, targetY, ease);
      glow.style.transform = `translate(${currentX - 150}px, ${currentY - 150}px)`;
    }
    requestAnimationFrame(animate);
  }
  animate();

  window.addEventListener('resize', () => {
    targetX = Math.min(targetX, window.innerWidth);
    targetY = Math.min(targetY, window.innerHeight);
  });
})();
