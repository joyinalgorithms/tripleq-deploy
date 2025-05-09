document.addEventListener("DOMContentLoaded", function() {
    const images = [
        "/static/images/bg1.jpg",
        "/static/images/bg2.jpg",
        "/static/images/bg3.jpg",
        "/static/images/bg4.jpg",
        "/static/images/bg5.jpg"
    ];

    let index = 0;
    const bgImage = document.getElementById("background-image");

    setInterval(() => {
        index = (index + 1) % images.length;
        bgImage.style.opacity = 0;
        setTimeout(() => {
            bgImage.src = images[index];
            bgImage.style.opacity = 1;
        }, 500);
    }, 4000);
});
