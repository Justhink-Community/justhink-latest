
const countdownValue = document.querySelector('.countdown__value'),
controllerStart = document.querySelectorAll('.controller__start')
let COUNTDOWN_STOPPED = false 

function startCountdown() {
  countdownValue.innerHTML = 90
  setInterval(() => {
    if (!COUNTDOWN_STOPPED) {
      countdownValue.innerHTML -= 1

      if (countdownValue.innerHTML == 0) {
        window.location.reload()
      }
    }
  }, 1000)
}

function stopCountdown() {
  COUNTDOWN_STOPPED = !COUNTDOWN_STOPPED;
  if (COUNTDOWN_STOPPED) {
    controllerStart[0].classList.add('invisible') 
    controllerStart[1].classList.remove('invisible') 
  } else {
    controllerStart[0].classList.remove('invisible') 
    controllerStart[1].classList.add('invisible') 
  }
} 

startCountdown()

