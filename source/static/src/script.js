const publishIdeaLink = document.querySelector(".publish-idea"),
  publishIdeaBox = document.querySelector(".publish-idea-box"),
  publishIdeaContainer = document.querySelector(".publish-idea-container"),
  myAccount = document.querySelector(".my-account"),
  notificationsBoxx = document.querySelector('.notifications-box');

const NOTIFICATION_TAGS = {
  success: "/static/images/icons/check-circle-outline.svg",
  error: "/static/images/icons/cross-circled.svg",
  warning: "/static/images/icons/warning-circle-outline.svg",
  info: "/static/images/icons/info-outline.svg",
}

const createNotification = (status, message) => {
  let notif = document.createElement('div')
  notif.classList.add('alert', 'showAlert', 'show')
  
  let notifImg = document.createElement('img')
  notifImg.classList.add('msg')
  notifImg.setAttribute('src', NOTIFICATION_TAGS[status])
  notifImg.setAttribute('alt', 'Bildirim ikonu')

  let notifMsg = document.createElement('span')
  notifMsg.classList.add('msg')
  notifMsg.innerHTML = message

  notif.appendChild(notifImg)
  notif.appendChild(notifMsg)

  document.querySelector('ul.messages').appendChild(notif)
}

document.querySelector("html").addEventListener("click", (e) => {

 try {
  if (
    !publishIdeaContainer.contains(e.target) &&
    e.target != document.querySelector(".publish-idea svg") &&
    publishIdeaBox.classList.contains("writing-idea")
  ) {
    publishIdeaBox.classList.remove("writing-idea");
    publishIdeaBox.classList.add("inspecting-ideas");
    document.querySelector('html').style.overflowY = 'visible';
  }
 } catch (error) {
  
 } if (
    !myAccount.contains(e.target) &&
    myAccount.classList.contains("showed") &&
    e.target != document.querySelector(".btn")
  ) {
    myAccount.classList.remove("showed");
  } if (
    !notificationsBoxx.contains(e.target) &&
    notificationsBoxx.classList.contains("showing") &&
    e.target != document.querySelector(".header__notifications")
  ) {
    notificationsBoxx.classList.remove("showing");
  } 
});

try {
    publishIdeaLink.addEventListener("click", () => {
      // console.log('hi')
      let linkIcon = publishIdeaLink.querySelector("svg");
      if (linkIcon.classList.contains("add")) {
        publishIdeaBox.classList.add("writing-idea");
        publishIdeaBox.classList.remove("inspecting-ideas");
        if(window.matchMedia('(max-width: 43em)').matches) {

          document.querySelector('html').style.overflowY = 'hidden';
        }

      }
    });
  
} catch (error) {
  
}

// IDEAS

const ideas = document.querySelectorAll(".idea");

ideas.forEach((idea) => {
  idea.addEventListener("click", (e) => {
    
    if (
      !idea.querySelector(".idea__interaction-btns").contains(e.target) &&
      e.target.tagName == "a"
    ) {
      window.location.replace(
        idea.querySelector(".idea__comment-btn").getAttribute("href")
      );
    }
  });
});

// PROFILE

const expandMyAccount = () => {
  myAccount.classList.toggle("showed");
};



const confirmationBtn = document.querySelector('.confirm-purchase__btn--confirm'),
productBuyBtns = document.querySelectorAll('.product-buy'),
productUseBtns = document.querySelectorAll('.product-use'),
confirmPurchase = document.querySelector('.confirm-purchase')

productBuyBtns.forEach(productBuyBtn => {
  if (productBuyBtn) {
    productBuyBtn.addEventListener('click', (_e) => {
      confirmPurchase.querySelector('p').innerHTML = `${productBuyBtn.getAttribute('data-product')} adlı ürün için ${productBuyBtn.getAttribute('data-fee')} puan kullanmayı onaylıyor musun?` 
      confirmationBtn.setAttribute('data-product', productBuyBtn.getAttribute('data-product'))
    });
  }
})

productUseBtns.forEach(productUseBtn => {
  if (productUseBtn) {
    productUseBtn.addEventListener('click', (_e) => {
      $.ajax({
        type: 'GET',
        url: '/change-theme',
        data: {product_name: productUseBtn.getAttribute('data-product')},
        success: function(res) {
          window.location.reload()
        }
      })
    });
  }
});

  if (confirmationBtn) {
    confirmationBtn.addEventListener('click', (_e) => {
      $.ajax({
        type: 'POST',
        url: '/shop',
        data: {product_name: confirmationBtn.getAttribute('data-product'), csrfmiddlewaretoken: confirmPurchase.querySelector('input[name="csrfmiddlewaretoken"]').value},
        success: function(res) { window.location.reload() } 
      })
    });
  
  
  }