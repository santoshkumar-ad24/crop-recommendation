// Mobile hamburger menu toggle
(function(){
	const btn = document.querySelector('.menu-toggle');
	const nav = document.getElementById('primary-navigation');

	if(!btn || !nav) return;

	function setOpen(open){
		nav.classList.toggle('open', open);
		btn.setAttribute('aria-expanded', String(!!open));

		// Toggle body scroll lock so background can't be scrolled when menu is open
		document.body.classList.toggle('nav-open', !!open);

		// Manage focus for accessibility: trap focus inside nav when open
		if(open){
			previousActive = document.activeElement;
			const focusable = nav.querySelectorAll(focusableSelectors);
			if(focusable.length) focusable[0].focus();
			// add keydown listener to trap tab and close on Escape
			document.addEventListener('keydown', handleKeydown);
		} else {
			// restore previous focus
			document.removeEventListener('keydown', handleKeydown);
			if(previousActive && typeof previousActive.focus === 'function') previousActive.focus();
		}

		// Visual state on button
		btn.classList.toggle('open', !!open);
	}

	btn.addEventListener('click', (e) => {
		const isOpen = btn.getAttribute('aria-expanded') === 'true';
		setOpen(!isOpen);
	});

	// Key handling: Escape & Tab trapping
	let previousActive = null;
	const focusableSelectors = 'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])';

	function handleKeydown(e){
		if(e.key === 'Escape'){
			setOpen(false);
			return;
		}

		if(e.key === 'Tab' && nav.classList.contains('open')){
			// Trap focus inside nav
			const items = Array.from(nav.querySelectorAll(focusableSelectors)).filter(el => el.offsetParent !== null);
			if(items.length === 0) return;
			const first = items[0];
			const last = items[items.length - 1];
			if(e.shiftKey && document.activeElement === first){
				e.preventDefault();
				last.focus();
			} else if(!e.shiftKey && document.activeElement === last){
				e.preventDefault();
				first.focus();
			}
		}
	}

	// Close when clicking outside the nav on small screens
	document.addEventListener('click', (e) => {
		if(window.innerWidth > 600) return; // only on small
		const target = e.target;
		if(!nav.contains(target) && !btn.contains(target)){
			setOpen(false);
		}
	});

	// Close menu when clicking an internal link inside nav
	nav.addEventListener('click', (e) => {
		const a = e.target.closest('a[href^="#"]');
		if(a && nav.classList.contains('open')){
			setOpen(false);
		}
	});

	// Close menu when resizing to wide screens to avoid stuck-open state
	window.addEventListener('resize', () => {
		if(window.innerWidth > 600 && nav.classList.contains('open')){
			setOpen(false);
		}
	});
})();

/* Smooth scroll to anchors with header offset */
(function(){
	const header = document.querySelector('.header');
	const nav = document.getElementById('primary-navigation');
	const menuBtn = document.querySelector('.menu-toggle');

	function getHeaderOffset(){
		if(!header) return 0;
		// compute visible header height (use boundingClientRect to include transforms)
		const rect = header.getBoundingClientRect();
		return Math.max(rect.height, 0);
	}

	function scrollToElement(el){
		if(!el) return;
		const offset = getHeaderOffset();
		const rect = el.getBoundingClientRect();
		const targetY = window.scrollY + rect.top - offset - 8; // small gap
		window.scrollTo({ top: targetY, behavior: 'smooth' });
	}

	// Intercept internal link clicks
	document.addEventListener('click', (e) => {
		const a = e.target.closest('a[href^="#"]');
		if(!a) return;
		const href = a.getAttribute('href');
		if(!href || href === '#') return;

		const id = href.slice(1);
		const target = document.getElementById(id);
		if(!target) return; // let default if no target

		e.preventDefault();

		// If mobile nav is open, close it first to avoid it covering target
		if(nav && nav.classList.contains('open')){
			nav.classList.remove('open');
			if(menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
		}

		// small timeout to allow close animation if any
		setTimeout(() => scrollToElement(target), 80);
	}, { passive: true });

	// On load, if there's a hash, scroll to it accounting for header
	window.addEventListener('load', () => {
		if(location.hash){
			const id = location.hash.slice(1);
			const target = document.getElementById(id);
			if(target) {
				// small delay to allow layout to settle
				setTimeout(() => scrollToElement(target), 60);
			}
		}
	});
})();
