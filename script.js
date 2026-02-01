const API_KEY = "adeb00f46aed436faca7d6576f1d6476";
const url = "https://newsapi.org/v2/everything?q=";

let bookmarks = JSON.parse(localStorage.getItem("bookmarks")) || [];
let curSelectedNav = null;

window.addEventListener("load", () => {
    fetchNews("India");
    loadBookmarks(); // Optional: load this in a dedicated view like a bookmarks tab
});

function reload() {
    window.location.reload();
}

async function fetchNews(query) {
    try {
        const res = await fetch(`${url}${query}&apiKey=${API_KEY}`);
        const data = await res.json();
        bindData(data.articles);
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}

function bindData(articles) {
    const cardsContainer = document.getElementById("cards-container");
    const newsCardTemplate = document.getElementById("template-news-card");

    cardsContainer.innerHTML = "";

    articles.forEach((article) => {
        if (!article.urlToImage) return;
        const cardClone = newsCardTemplate.content.cloneNode(true);
        fillDataInCard(cardClone, article);
        cardsContainer.appendChild(cardClone);
    });
}

function fillDataInCard(cardClone, article) {
    const newsImg = cardClone.querySelector("#news-img");
    const newsTitle = cardClone.querySelector("#news-title");
    const newsSource = cardClone.querySelector("#news-source");
    const newsDesc = cardClone.querySelector("#news-desc");
    const bookmarkBtn = cardClone.querySelector(".bookmark-btn");

    newsImg.src = article.urlToImage;
    newsTitle.innerHTML = article.title;
    newsDesc.innerHTML = article.description;

    const date = new Date(article.publishedAt).toLocaleString("en-US", {
        timeZone: "Asia/Jakarta",
    });

    newsSource.innerHTML = `${article.source.name} · ${date}`;

    if (bookmarks.some((b) => b.url === article.url)) {
        bookmarkBtn.textContent = "Bookmarked ✅";
        bookmarkBtn.disabled = true;
    }

    bookmarkBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        saveBookmark(article, bookmarkBtn);
    });

    cardClone.firstElementChild.addEventListener("click", () => {
        window.open(article.url, "_blank");
    });
}

function saveBookmark(article, button) {
    bookmarks = JSON.parse(localStorage.getItem("bookmarks")) || [];

    if (bookmarks.some((b) => b.url === article.url)) {
        alert("Already bookmarked!");
        return;
    }

    bookmarks.push(article);
    localStorage.setItem("bookmarks", JSON.stringify(bookmarks));
    alert("Article bookmarked!");

    button.textContent = "Bookmarked ✅";
    button.disabled = true;
}

function loadBookmarks() {
    const bookmarksContainer = document.getElementById("cards-container");
    const savedBookmarks = JSON.parse(localStorage.getItem("bookmarks")) || [];

    bookmarksContainer.innerHTML = "";

    savedBookmarks.forEach((bookmark) => {
        const bookmarkCard = document.createElement("div");
        bookmarkCard.classList.add("card");

        bookmarkCard.innerHTML = `
            <div class="card-header">
                <img src="${bookmark.urlToImage}" alt="News Image">
            </div>
            <div class="card-content">
                <h3>${bookmark.title}</h3>
                <h6 class="news-source">${bookmark.source.name}</h6>
                <p class="news-desc">${bookmark.description}</p>
                <a href="${bookmark.url}" target="_blank" class="read-more">Read More</a>
                <button class="remove-btn" onclick="removeBookmark('${bookmark.url}')">Remove</button>
            </div>
        `;

        bookmarksContainer.appendChild(bookmarkCard);
    });
}

function removeBookmark(url) {
    let bookmarks = JSON.parse(localStorage.getItem("bookmarks")) || [];
    bookmarks = bookmarks.filter(item => item.url !== url);
    localStorage.setItem("bookmarks", JSON.stringify(bookmarks));
    loadBookmarks();
}

function onNavItemClick(id) {
    fetchNews(id);
    const navItem = document.getElementById(id);
    curSelectedNav?.classList.remove("active");
    curSelectedNav = navItem;
    curSelectedNav.classList.add("active");
}

const searchButton = document.getElementById("search-button");
const searchText = document.getElementById("search-text");

searchButton.addEventListener("click", () => {
    const query = searchText.value.trim();
    if (!query) return;
    fetchNews(query);
    curSelectedNav?.classList.remove("active");
    curSelectedNav = null;
});

function showBookmarks() {
    loadBookmarks();
}
