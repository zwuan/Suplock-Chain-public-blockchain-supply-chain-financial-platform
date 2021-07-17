const openModalButtons = document.getElementById('add_coco')
const overlay = document.getElementById('overlay')
const pop_div = document.getElementById('pop_div')

openModalButtons.addEventListener('click',() => {
  openModal()
})

overlay.addEventListener('click',() => {
  closeModal()
})
function openModal(){
  pop_div.classList.add('active')
  overlay.classList.add('active')
}

function closeModal(){
  pop_div.classList.remove('active')
  overlay.classList.remove('active')
}

