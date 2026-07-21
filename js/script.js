// Preloader Logic
document.addEventListener('DOMContentLoaded', () => {
    const preloader = document.createElement('div');
    preloader.id = 'preloader';
    preloader.innerHTML = `
        <div class="loader-container">
            <div class="loader-circle">
                <img src="images/logo.png" alt="School Logo" class="loader-logo">
            </div>
            <div class="loader-arcs">
                <div class="arc arc1"></div>
                <div class="arc arc2"></div>
                <div class="arc arc3"></div>
            </div>
        </div>
        <div class="loader-text">Loading Sts. Joachim and Anne Catholic School...</div>
    `;
    document.body.prepend(preloader);
});

window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.classList.add('hidden');
        setTimeout(() => {
            preloader.remove();
        }, 500); // Wait for transition
    }
});

// Initialize AOS (Animate On Scroll)
AOS.init({
    duration: 1000,
    once: true,
    offset: 100
});

// Counter Animation for Stats
function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    const speed = 200;

    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-target');
            const count = +counter.innerText;
            const increment = target / speed;

            if (count < target) {
                counter.innerText = Math.ceil(count + increment);
                setTimeout(updateCount, 1);
            } else {
                counter.innerText = target;
            }
        };

        updateCount();
    });
}

// Trigger counter animation when stats section is in view
const statsSection = document.querySelector('.stat-counter');
if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                observer.unobserve(entry.target);
            }
        });
    });
    observer.observe(statsSection);
}

// Gallery Filter Functionality
function filterGallery(category) {
    const items = document.querySelectorAll('.gallery-item');
    const buttons = document.querySelectorAll('.filter-btn');

    // Remove active class from all buttons
    buttons.forEach(btn => btn.classList.remove('active'));

    // Add active class to clicked button
    event.target.classList.add('active');

    // Show/hide items based on category
    items.forEach(item => {
        if (category === 'all' || item.classList.contains(category)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Lightbox Functionality
function openLightbox(src, caption) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
            <img src="${src}" alt="${caption}">
            <div class="lightbox-caption">${caption}</div>
        </div>
    `;
    document.body.appendChild(lightbox);

    // Close lightbox on click outside image
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });

    // Close lightbox on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeLightbox();
        }
    });
}

function closeLightbox() {
    const lightbox = document.querySelector('.lightbox');
    if (lightbox) {
        lightbox.remove();
    }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Growth Panel Animation - Animate bars from 0% to target percentage
document.addEventListener('DOMContentLoaded', function() {
    const growthPanel = document.querySelector('.growth-panel');
    if (!growthPanel) return;

    const animateGrowthBars = () => {
        const fills = growthPanel.querySelectorAll('.growth-fill');
        const percents = growthPanel.querySelectorAll('.growth-percent');
        
        fills.forEach((fill) => {
            const targetWidth = parseInt(fill.getAttribute('data-width'));
            // Reset to 0 first
            fill.style.width = '0%';
            
            // Animate the width (CSS transition handles the animation)
            setTimeout(() => {
                fill.style.width = targetWidth + '%';
            }, 100);
        });
        
        percents.forEach((percent, index) => {
            const target = parseInt(percent.getAttribute('data-target'));
            let current = 0;
            percent.innerText = '0%';
            
            // Stagger the counter start slightly after bar animation
            setTimeout(() => {
                const interval = setInterval(() => {
                    if (current < target) {
                        current++;
                        percent.innerText = current + '%';
                    } else {
                        clearInterval(interval);
                    }
                }, 25);
            }, 300 + (index * 100));
        });
    };

    // Use IntersectionObserver to trigger once when growth panel is visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateGrowthBars();
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });
    
    observer.observe(growthPanel);
});

// Navbar active state
const navLinks = document.querySelectorAll('.nav-link');
const currentPath = window.location.pathname.split('/').pop();

navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
    }
});

// Contact form submission (placeholder)
const contactForm = document.querySelector('#contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Thank you for your message! We will get back to you soon.');
        contactForm.reset();
    });
}

// Sample users data
// Portal login form


// Auto-slide hero carousel every  seconds
document.addEventListener('DOMContentLoaded', function() {
    const heroCarousel = document.querySelector('#heroCarousel');
    if (heroCarousel) {
        const carousel = new bootstrap.Carousel(heroCarousel, {
            interval: 5000, // 3.5 seconds
            ride: 'carousel'
        });
    }
});

// Add section titles class for styling
document.addEventListener('DOMContentLoaded', function() {
    const sectionTitles = document.querySelectorAll('section h2');
    sectionTitles.forEach(title => {
        title.classList.add('section-title');
    });
});

// Fetch and Inject Dynamic Content
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/api/content');
        if (response.ok) {
            const resData = await response.json();
            if (resData.success) {
                const data = resData.data;
                
                // Inject Text Elements based on classes or IDs
                const elementsToUpdate = [
                    'academic_year', 
                    'current_term', 
                    'about_intro', 
                    'about_mission', 
                    'about_vision'
                ];
                
                elementsToUpdate.forEach(id => {
                    if (data[id]) {
                        const els = document.querySelectorAll('.' + id + '-dynamic, #' + id + '-dynamic');
                        els.forEach(el => {
                            el.innerHTML = data[id];
                        });
                    }
                });
                
                // Inject Image Elements
                const imagesToUpdate = {
                    'priest_image': '.priest-image-dynamic',
                    'hero_bg': '.hero-bg-dynamic',
                    'about_image': '.about-image-dynamic'
                };
                
                for (const [key, selector] of Object.entries(imagesToUpdate)) {
                    if (data[key]) {
                        const els = document.querySelectorAll(selector);
                        els.forEach(el => {
                            if (el.tagName === 'IMG') {
                                el.src = data[key];
                            } else {
                                el.style.backgroundImage = `url('${data[key]}')`;
                            }
                        });
                    }
                }
                
                // Inject Gallery Data if present
                const galleryGrid = document.getElementById('dynamic-gallery-grid');
                if(galleryGrid && data.gallery) {
                    galleryGrid.innerHTML = '';
                    if(data.gallery.length === 0) {
                        galleryGrid.innerHTML = '<div class="w-100 text-center py-5">No gallery images yet.</div>';
                    }
                    data.gallery.forEach(item => {
                        galleryGrid.innerHTML += `
                            <div class="gallery-item ${item.category}" data-aos="fade-up" onclick="openLightbox('${item.image_path}', '${item.title}')">
                                <img src="${item.image_path}" alt="${item.title}" class="img-fluid" style="width: 100%; height: 250px; object-fit: cover;">
                                <div class="gallery-overlay">
                                    <h5>${item.title || 'Gallery Image'}</h5>
                                    <p>${item.category}</p>
                                </div>
                            </div>
                        `;
                    });
                }
            }
        }
    } catch(e) {
        console.error("Error loading dynamic content:", e);
    }
});
