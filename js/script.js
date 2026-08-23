// Standardize navigation across all public pages.
document.addEventListener('DOMContentLoaded', () => {
    const list = document.querySelector('.navbar-nav');
    if (!list || location.pathname.includes('admin')) return;
    list.innerHTML = `<li class="nav-item"><a class="nav-link" href="/">Home</a></li><li class="nav-item"><a class="nav-link" href="about">About Us</a></li><li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="academics" data-bs-toggle="dropdown">Academics</a><ul class="dropdown-menu"><li><a class="dropdown-item" href="academics">Overview</a></li><li><a class="dropdown-item" href="jss-subjects">JSS Subjects</a></li><li><a class="dropdown-item" href="education-facilities">Facilities</a></li><li><a class="dropdown-item" href="school-rules-regulations">Rules &amp; Regulations</a></li><li><a class="dropdown-item" href="disciplinary-measures">Discipline</a></li><li><a class="dropdown-item" href="education-anthem">Anthem</a></li></ul></li><li class="nav-item"><a class="nav-link" href="admissions">Admissions</a></li><li class="nav-item"><a class="nav-link" href="admission-form">Admission Form</a></li><li class="nav-item"><a class="nav-link" href="news">News &amp; Events</a></li><li class="nav-item"><a class="nav-link" href="gallery">Gallery</a></li><li class="nav-item"><a class="nav-link" href="contact">Contact</a></li><li class="nav-item"><a class="nav-link" href="https://schoolos.osartech.com.ng/" target="_blank" rel="noopener">Portal</a></li>`;
});

// Preloader Logic - Hide quickly after DOM ready, don't wait for all images
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
        <div class="loader-text">Loading SS. Joachim and Anne Catholic School...</div>
    `;
    document.body.prepend(preloader);
    
    // Hide preloader after max 800ms - don't wait for all images to load
    setTimeout(() => {
        const p = document.getElementById('preloader');
        if (p) {
            p.classList.add('hidden');
            setTimeout(() => { if (p.parentNode) p.remove(); }, 300);
        }
    }, 800);
});

// Fallback: hide on window load too
window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.classList.add('hidden');
        setTimeout(() => {
            if (preloader.parentNode) preloader.remove();
        }, 300);
    }
});

// Initialize AOS (Animate On Scroll) - with shorter duration
AOS.init({
    duration: 600,
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

// ============================================================
// Homepage Latest News / Blog / Events
// ============================================================
document.addEventListener('DOMContentLoaded', async function() {
    const grid = document.getElementById('homePostsGrid');
    if (!grid) return; // Only run on pages that have the grid (homepage)

    const catLabels = { news: 'News', blog: 'Blog', event: 'Event' };

    try {
        const res = await fetch('/api/posts');
        const data = await res.json();
        if (!data.success) throw new Error('Failed to load posts');

        const posts = (data.data || []).slice(0, 3); // Show latest 3

        if (posts.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center text-muted py-5"><i class="fas fa-newspaper fa-3x mb-3"></i><p>No updates published yet. Check back soon!</p></div>';
            return;
        }

        grid.innerHTML = posts.map(p => {
            const img = p.image_path
                ? `<img src="${p.image_path}" alt="${p.title || 'Post image'}" style="height:200px;width:100%;object-fit:cover;background:#eef1f5;">`
                : `<div style="height:200px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#003366,#0056b3);"><i class="fas fa-newspaper text-white" style="font-size:3rem;opacity:.6;"></i></div>`;
            const excerpt = (p.content || '').length > 100 ? p.content.substring(0, 100) + '…' : (p.content || '');
            return `
                <div class="col-md-6 col-lg-4">
                    <div class="card h-100 post-card border-0 shadow-sm" style="border-radius:14px;overflow:hidden;transition:transform .3s,box-shadow .3s;">
                        <div class="position-relative">
                            ${img}
                            <span class="position-absolute" style="top:14px;left:14px;background:#003366;color:#fff;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px;padding:4px 10px;border-radius:30px;">${catLabels[p.category] || 'News'}</span>
                        </div>
                        <div class="card-body p-4">
                            ${p.date ? `<small class="text-muted"><i class="far fa-calendar-alt me-1"></i>${p.date}</small>` : ''}
                            <h5 class="fw-bold mt-1 mb-2" style="color:var(--primary-color);">${p.title || 'Untitled'}</h5>
                            <p class="text-muted mb-0" style="font-size:.95rem;">${excerpt}</p>
                            <a href="/post/${p.id}" class="btn btn-primary btn-sm mt-3 rounded-pill">Learn more</a>
                        </div>
                    </div>
                </div>`;
        }).join('');
    } catch(e) {
        console.error('Error loading homepage posts', e);
        grid.innerHTML = '<div class="col-12 text-center text-muted py-5"><p>Unable to load updates at the moment.</p></div>';
    }
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

// Auto-slide hero carousel
document.addEventListener('DOMContentLoaded', function() {
    const heroCarousel = document.querySelector('#heroCarousel');
    if (heroCarousel) {
        const carousel = new bootstrap.Carousel(heroCarousel, {
            interval: 5000,
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

// Fetch and Inject Dynamic Content (non-blocking with timeout)
document.addEventListener('DOMContentLoaded', async function() {
    // Delay API call slightly so page renders first
    await new Promise(r => setTimeout(r, 200));
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
                        `;
                    });
                }
            }
        }
    } catch(e) {
        console.error("Error loading dynamic content:", e);
    }
});
