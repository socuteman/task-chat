/* ========================================
   Task-Chat Presentations - Common JS
   ======================================== */

class Presentation {
    constructor(totalSlides) {
        this.currentSlide = 0;
        this.totalSlides = totalSlides;
        this.init();
    }

    init() {
        this.showSlide(this.currentSlide);
        this.updateProgress();
        this.updateIndicators();
        this.bindEvents();
        this.animateOnScroll();
    }

    showSlide(index) {
        const slides = document.querySelectorAll('.slide');
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
        this.currentSlide = index;
        this.updateNavigation();
        this.updateProgress();
        this.updateIndicators();
        
        // Анимация элементов на слайде
        this.animateSlideElements(index);
    }

    nextSlide() {
        if (this.currentSlide < this.totalSlides - 1) {
            this.showSlide(this.currentSlide + 1);
        }
    }

    prevSlide() {
        if (this.currentSlide > 0) {
            this.showSlide(this.currentSlide - 1);
        }
    }

    goToSlide(index) {
        this.showSlide(index);
    }

    updateNavigation() {
        const prevBtn = document.querySelector('.nav-btn.prev');
        const nextBtn = document.querySelector('.nav-btn.next');

        if (prevBtn) {
            prevBtn.disabled = this.currentSlide === 0;
            prevBtn.onclick = () => this.prevSlide();
        }

        if (nextBtn) {
            if (this.currentSlide === this.totalSlides - 1) {
                nextBtn.innerHTML = '✓ Завершить';
                nextBtn.onclick = () => window.location.href = 'index.html';
            } else {
                nextBtn.innerHTML = 'Далее →';
                nextBtn.onclick = () => this.nextSlide();
            }
        }
    }

    updateProgress() {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const progress = ((this.currentSlide + 1) / this.totalSlides) * 100;
            progressBar.style.width = progress + '%';
        }
    }

    updateIndicators() {
        const indicators = document.querySelectorAll('.indicator');
        indicators.forEach((indicator, i) => {
            indicator.classList.toggle('active', i === this.currentSlide);
        });
    }

    bindEvents() {
        // Клавиатурная навигация
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === 'Space') {
                this.nextSlide();
            } else if (e.key === 'ArrowLeft') {
                this.prevSlide();
            }
        });

        // Свайпы для мобильных
        let touchStartX = 0;
        let touchEndX = 0;

        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });

        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            if (touchStartX - touchEndX > 50) {
                this.nextSlide();
            } else if (touchEndX - touchStartX > 50) {
                this.prevSlide();
            }
        });
    }

    animateSlideElements(index) {
        const activeSlide = document.querySelector('.slide.active');
        if (!activeSlide) return;

        // Анимация карточек
        const cards = activeSlide.querySelectorAll('.card, .feature-card, .stat-card');
        cards.forEach((card, i) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, i * 150);
        });

        // Анимация заголовков
        const titles = activeSlide.querySelectorAll('h1, h2, h3');
        titles.forEach((title, i) => {
            title.style.opacity = '0';
            setTimeout(() => {
                title.style.transition = 'opacity 0.5s ease';
                title.style.opacity = '1';
            }, i * 100);
        });
    }

    animateOnScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.card, .feature-card, .stat-card').forEach(el => {
            observer.observe(el);
        });
    }

    // Анимация чисел в статистике
    animateNumber(element, target, duration = 2000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target + (element.dataset.suffix || '');
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current) + (element.dataset.suffix || '');
            }
        }, 16);
    }

    // Инициализация анимации чисел
    initNumberAnimations() {
        document.querySelectorAll('[data-animate-number]').forEach(el => {
            const target = parseInt(el.dataset.animateNumber);
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    this.animateNumber(el, target);
                    observer.unobserve(el);
                }
            });
            observer.observe(el);
        });
    }
}

// ========================================
// Chart Initialization (Chart.js)
// ========================================

function initChart(ctx, type, data, options) {
    if (typeof Chart !== 'undefined') {
        return new Chart(ctx, {
            type: type,
            data: data,
            options: options
        });
    }
    return null;
}

// ========================================
// Mobile Frame Screenshot Loader
// ========================================

function loadMobileScreenshot(containerId, imagePath, caption) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="mobile-frame">
            <div class="mobile-screen">
                <img src="${imagePath}" alt="Mobile screenshot" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 300 600%22><rect fill=%22%23f0f0f0%22 width=%22300%22 height=%22600%22/><text x=%22150%22 y=%22300%22 text-anchor=%22middle%22 fill=%22%23999%22>Скриншот</text></svg>'">
            </div>
        </div>
        ${caption ? `<p class="screenshot-caption">${caption}</p>` : ''}
    `;
}

// ========================================
// Desktop Frame Screenshot Loader
// ========================================

function loadDesktopScreenshot(containerId, imagePath, caption) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="desktop-frame">
            <div class="desktop-header">
                <div class="desktop-dot red"></div>
                <div class="desktop-dot yellow"></div>
                <div class="desktop-dot green"></div>
            </div>
            <div class="desktop-screen">
                <img src="${imagePath}" alt="Desktop screenshot" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 800 600%22><rect fill=%22%23f0f0f0%22 width=%22800%22 height=%22600%22/><text x=%22400%22 y=%22300%22 text-anchor=%22middle%22 fill=%22%23999%22>Скриншот</text></svg>'">
            </div>
        </div>
        ${caption ? `<p class="screenshot-caption">${caption}</p>` : ''}
    `;
}

// ========================================
// Comparison View Loader
// ========================================

function loadComparisonView(containerId, desktopImage, mobileImage, caption) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="comparison-view">
            <div class="desktop-frame">
                <div class="desktop-header">
                    <div class="desktop-dot red"></div>
                    <div class="desktop-dot yellow"></div>
                    <div class="desktop-dot green"></div>
                </div>
                <div class="desktop-screen">
                    <img src="${desktopImage}" alt="Desktop view">
                </div>
            </div>
            <div class="mobile-frame">
                <div class="mobile-screen">
                    <img src="${mobileImage}" alt="Mobile view">
                </div>
            </div>
        </div>
        ${caption ? `<p class="screenshot-caption">${caption}</p>` : ''}
    `;
}

// ========================================
// Initialize All Presentations
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Инициализация анимации чисел
    const presentation = new Presentation(document.querySelectorAll('.slide').length);
    presentation.initNumberAnimations();

    // Плавная прокрутка к якорям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// ========================================
// Export for use in presentations
// ========================================

window.TaskChatPresentation = {
    Presentation,
    initChart,
    loadMobileScreenshot,
    loadDesktopScreenshot,
    loadComparisonView
};
