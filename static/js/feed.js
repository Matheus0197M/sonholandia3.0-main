function revealOnScroll() {
    const reveals = document.querySelectorAll(".reveal");
    for(let el of reveals) {
       const windowHeight = window.innerHeight;
       const elementTop = el.getBoundingClientRect().top;
       const elementBottom = el.getBoundingClientRect().bottom;

       if (elementTop < windowHeight - 100 && elementBottom > 100) {
           el.classList.add("active");
       } else {
           el.classList.remove("active");
       }
    }   
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll); 