document.addEventListener("DOMContentLoaded", () => {

  const modal = document.getElementById("galleryModal")
  const modalImg = document.getElementById("galleryModalImage")
  const downloadBtn = document.getElementById("galleryDownloadBtn")
  const closeBtn = document.querySelector(".galleryClose")
  const images = document.querySelectorAll(".galleryImage")

  function buildDownloadUrl(url, filename){

    const marker = "/image/upload/"

    if(!url.includes(marker)){
      return url
    }

    return url.replace(
      marker,
      `${marker}fl_attachment:${filename}/`
    )

  }

  images.forEach((img) => {

    img.addEventListener("click", () => {

      const src = img.dataset.full

      modal.style.display = "flex"
      modalImg.src = src

      // extrai nome real do ficheiro da imagem
      const fileNameFromUrl = src.split("/").pop().split(".")[0]

      const filename = `ucc-galeria-${fileNameFromUrl}`

      downloadBtn.href = buildDownloadUrl(src, filename)

    })

  })

  closeBtn.onclick = () => {
    modal.style.display = "none"
  }

  modal.onclick = (e) => {

    if(e.target === modal){
      modal.style.display = "none"
    }

  }

})