document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("galleryModal")
  const modalImg = document.getElementById("galleryModalImage")
  const counter = document.getElementById("galleryCounter")
  const downloadBtn = document.getElementById("galleryDownloadBtn")
  const closeBtn = document.querySelector(".galleryClose")
  const prevBtn = document.querySelector(".galleryPrev")
  const nextBtn = document.querySelector(".galleryNext")
  const images = document.querySelectorAll(".galleryImage")
  const fileInput = document.querySelector('input[type="file"][name="images"]')
  const selectedCount = document.getElementById("gallerySelectedCount")

  const toggleSelectionModeBtn = document.getElementById("toggleSelectionMode")
  const bulkDeleteBtn = document.getElementById("bulkDeleteBtn")
  const bulkCount = document.getElementById("galleryBulkCount")
  const galleryCards = document.querySelectorAll(".galleryCard")
  const selectInputs = document.querySelectorAll(".gallerySelectInput")

  let currentIndex = 0
  let touchStartX = 0
  let touchEndX = 0
  let selectionMode = false

  function buildDownloadUrl(url, filename) {
    const marker = "/image/upload/"

    if (!url.includes(marker)) {
      return url
    }

    return url.replace(
      marker,
      `${marker}fl_attachment:${filename}/`
    )
  }

  function getFileNameFromUrl(url) {
    const lastPart = url.split("/").pop() || "imagem"
    return lastPart.split(".")[0]
  }

  function updateCounter() {
    if (!counter || !images.length) {
      return
    }

    counter.textContent = `${currentIndex + 1} / ${images.length}`
  }

  function showImage(index) {
    if (!images.length || !modal || !modalImg || selectionMode) {
      return
    }

    if (index < 0) {
      currentIndex = images.length - 1
    } else if (index >= images.length) {
      currentIndex = 0
    } else {
      currentIndex = index
    }

    const currentImg = images[currentIndex]
    const src = currentImg.dataset.full || currentImg.src

    modal.style.display = "flex"
    document.body.style.overflow = "hidden"
    modalImg.src = src

    if (downloadBtn) {
      const fileNameFromUrl = getFileNameFromUrl(src)
      const filename = `ucc-galeria-${fileNameFromUrl}`
      downloadBtn.href = buildDownloadUrl(src, filename)
    }

    updateCounter()
  }

  function closeModal() {
    if (!modal || !modalImg) {
      return
    }

    modal.style.display = "none"
    modalImg.src = ""
    document.body.style.overflow = ""
  }

  function showNextImage() {
    showImage(currentIndex + 1)
  }

  function showPreviousImage() {
    showImage(currentIndex - 1)
  }

  function handleSwipe() {
    const swipeDistance = touchEndX - touchStartX
    const minSwipeDistance = 50

    if (Math.abs(swipeDistance) < minSwipeDistance) {
      return
    }

    if (swipeDistance < 0) {
      showNextImage()
    } else {
      showPreviousImage()
    }
  }

  function updateSelectedCount() {
    if (!fileInput || !selectedCount) {
      return
    }

    const totalFiles = fileInput.files ? fileInput.files.length : 0

    if (totalFiles === 0) {
      selectedCount.textContent = ""
      return
    }

    if (totalFiles === 1) {
      selectedCount.textContent = "1 imagem selecionada"
      return
    }

    selectedCount.textContent = `${totalFiles} imagens selecionadas`
  }

  function updateBulkSelectionState() {
    if (!bulkCount || !bulkDeleteBtn) {
      return
    }

    const checkedInputs = document.querySelectorAll(".gallerySelectInput:checked")
    const totalSelected = checkedInputs.length

    bulkCount.textContent = totalSelected
    bulkDeleteBtn.disabled = totalSelected === 0

    galleryCards.forEach((card) => {
      const input = card.querySelector(".gallerySelectInput")

      if (!input) {
        return
      }

      card.classList.toggle("isSelected", input.checked)
      card.classList.toggle("selectionMode", selectionMode)
    })

    if (toggleSelectionModeBtn) {
      toggleSelectionModeBtn.textContent = selectionMode ? "Cancelar seleção" : "Selecionar fotos"
    }
  }

  function clearSelection() {
    selectInputs.forEach((input) => {
      input.checked = false
    })

    updateBulkSelectionState()
  }

  images.forEach((img, index) => {
    img.addEventListener("click", () => {
      if (selectionMode) {
        const card = img.closest(".galleryCard")
        const input = card ? card.querySelector(".gallerySelectInput") : null

        if (input) {
          input.checked = !input.checked
          updateBulkSelectionState()
        }

        return
      }

      showImage(index)
    })
  })

  galleryCards.forEach((card) => {
    card.addEventListener("click", (event) => {
      if (!selectionMode) {
        return
      }

      const clickedOnCheckbox = event.target.closest(".gallerySelectBox")
      const clickedOnImage = event.target.closest(".galleryImage")

      if (clickedOnCheckbox || clickedOnImage) {
        return
      }

      const input = card.querySelector(".gallerySelectInput")

      if (!input) {
        return
      }

      input.checked = !input.checked
      updateBulkSelectionState()
    })
  })

  selectInputs.forEach((input) => {
    input.addEventListener("change", updateBulkSelectionState)
  })

  if (toggleSelectionModeBtn) {
    toggleSelectionModeBtn.addEventListener("click", () => {
      selectionMode = !selectionMode

      if (!selectionMode) {
        clearSelection()
      }

      updateBulkSelectionState()
    })
  }

  if (fileInput) {
    fileInput.addEventListener("change", updateSelectedCount)
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal)
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      showPreviousImage()
    })
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      showNextImage()
    })
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeModal()
      }
    })

    modal.addEventListener("touchstart", (e) => {
      touchStartX = e.changedTouches[0].screenX
    }, { passive: true })

    modal.addEventListener("touchend", (e) => {
      touchEndX = e.changedTouches[0].screenX
      handleSwipe()
    }, { passive: true })
  }

  document.addEventListener("keydown", (e) => {
    if (!modal || modal.style.display !== "flex") {
      return
    }

    if (e.key === "Escape") {
      closeModal()
    }

    if (e.key === "ArrowRight") {
      showNextImage()
    }

    if (e.key === "ArrowLeft") {
      showPreviousImage()
    }
  })

  updateBulkSelectionState()
})