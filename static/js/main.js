document.addEventListener('DOMContentLoaded', () => {
  // Load dark mode preference from localStorage
  const isDarkMode = localStorage.getItem('darkMode') === 'true';
  if (isDarkMode) {
    document.body.classList.add('dark-mode');
  }

  // Handle theme toggle in settings
  const themeSelect = document.querySelector('[name="theme"]');
  if (themeSelect) {
    // Set initial value based on current mode
    themeSelect.value = isDarkMode ? 'dark' : 'light';
    
    themeSelect.addEventListener('change', (event) => {
      const isDark = event.target.value === 'dark';
      if (isDark) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
      } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
      }
    });
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  // Smooth number animations for stat cards
  const statElements = document.querySelectorAll('.stat-card h2, .stat-card h3, .stat-panel strong');
  statElements.forEach((el) => {
    const text = el.textContent;
    if (text.includes('$')) {
      const match = text.match(/[\d.]+/);
      if (match) {
        const finalValue = parseFloat(match[0]);
        let currentValue = 0;
        const increment = finalValue / 20;
        const interval = setInterval(() => {
          currentValue += increment;
          if (currentValue >= finalValue) {
            el.textContent = '$' + finalValue.toFixed(2);
            clearInterval(interval);
          } else {
            el.textContent = '$' + currentValue.toFixed(2);
          }
        }, 30);
      }
    }
  });
});
