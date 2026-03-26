document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("galleryModal")
  const modalImg = document.getElementById("galleryModalImage")
  const modalContent = document.querySelector(".galleryModalContent")
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
  const uploadForm = document.querySelector(".galleryUploadForm")
  const uploadBtn = document.getElementById("uploadPhotosBtn")

  let currentIndex = 0
  let touchStartX = 0
  let touchCurrentX = 0
  let isDraggingModal = false
  let selectionMode = false

  // Constroi a url de download no caso de imagens vindas do Cloudinary
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

  // Tenta obter um nome base a partir da url da imagem
  function getFileNameFromUrl(url) {
    const lastPart = url.split("/").pop() || "imagem"
    return lastPart.split(".")[0]
  }

  // Atualiza o contador do modal
  function updateCounter() {
    if (!counter || !images.length) {
      return
    }

    counter.textContent = `${currentIndex + 1} / ${images.length}`
  }

  // Atualiza o link de download da imagem atual no modal
  function updateDownloadUrl(src) {
    if (!downloadBtn) {
      return
    }

    const fileNameFromUrl = getFileNameFromUrl(src)
    const filename = `ucc-galeria-${fileNameFromUrl}`
    downloadBtn.href = buildDownloadUrl(src, filename)
  }

  // Repõe o estado visual da imagem no modal
  function resetModalImageState() {
    if (!modalImg) {
      return
    }

    modalImg.style.transition = "transform 0.24s ease, opacity 0.24s ease"
    modalImg.style.transform = "translateX(0)"
    modalImg.style.opacity = "1"
  }

  // Mostra uma imagem no modal com base no índice recebido
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

    updateDownloadUrl(src)
    updateCounter()
    resetModalImageState()
  }

  // Fecha o modal e limpa o estado da imagem
  function closeModal() {
    if (!modal || !modalImg) {
      return
    }

    modal.style.display = "none"
    modalImg.src = ""
    modalImg.style.transform = "translateX(0)"
    modalImg.style.opacity = "1"
    document.body.style.overflow = ""
    isDraggingModal = false
  }

  // Faz a animação de saída/entrada quando se troca de imagem
  function animateImageChange(direction, onComplete) {
    if (!modalImg) {
      onComplete()
      return
    }

    const exitOffset = direction === "next" ? -70 : 70

    modalImg.style.transition = "transform 0.18s ease, opacity 0.18s ease"
    modalImg.style.transform = `translateX(${exitOffset}px)`
    modalImg.style.opacity = "0.35"

    window.setTimeout(() => {
      onComplete()

      const enterOffset = direction === "next" ? 70 : -70
      modalImg.style.transition = "none"
      modalImg.style.transform = `translateX(${enterOffset}px)`
      modalImg.style.opacity = "0.35"

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          modalImg.style.transition = "transform 0.22s ease, opacity 0.22s ease"
          modalImg.style.transform = "translateX(0)"
          modalImg.style.opacity = "1"
        })
      })
    }, 180)
  }

  // Avança para a imagem seguinte
  function showNextImage() {
    animateImageChange("next", () => {
      if (currentIndex + 1 >= images.length) {
        currentIndex = 0
      } else {
        currentIndex += 1
      }

      const src = images[currentIndex].dataset.full || images[currentIndex].src
      modalImg.src = src
      updateDownloadUrl(src)
      updateCounter()
    })
  }

  // Volta para a imagem anterior
  function showPreviousImage() {
    animateImageChange("prev", () => {
      if (currentIndex - 1 < 0) {
        currentIndex = images.length - 1
      } else {
        currentIndex -= 1
      }

      const src = images[currentIndex].dataset.full || images[currentIndex].src
      modalImg.src = src
      updateDownloadUrl(src)
      updateCounter()
    })
  }

  // Atualiza o texto que mostra quantas imagens foram escolhidas no input file
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

  // Atualiza o estado visual e o contador do modo de seleção múltipla
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
      toggleSelectionModeBtn.textContent = selectionMode
        ? "Cancelar seleção"
        : "Selecionar fotos"
    }
  }

  // Limpa todas as seleções atuais
  function clearSelection() {
    selectInputs.forEach((input) => {
      input.checked = false
    })

    updateBulkSelectionState()
  }

  // Clique na imagem:
  // - se estiver em modo seleção, seleciona/desseleciona
  // - se não estiver, abre o modal
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

  // Permite clicar no card para selecionar, mas evita conflito com imagem e checkbox
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

  // Atualiza o estado quando uma checkbox muda
  selectInputs.forEach((input) => {
    input.addEventListener("change", updateBulkSelectionState)
  })

  // Ativa ou desativa o modo de seleção
  if (toggleSelectionModeBtn) {
    toggleSelectionModeBtn.addEventListener("click", () => {
      selectionMode = !selectionMode

      if (!selectionMode) {
        clearSelection()
      }

      updateBulkSelectionState()
    })
  }

  // Atualiza o texto com a quantidade de imagens escolhidas para upload
  if (fileInput) {
    fileInput.addEventListener("change", updateSelectedCount)
  }

  // Fecha o modal
  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal)
  }

  // Navegação para a esquerda
  if (prevBtn) {
    prevBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      showPreviousImage()
    })
  }

  // Navegação para a direita
  if (nextBtn) {
    nextBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      showNextImage()
    })
  }

  // Fecha o modal se o clique for fora da imagem
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeModal()
      }
    })
  }

  // Swipe no telemóvel com arrasto visual da imagem
  if (modalContent && modalImg) {
    modalContent.addEventListener("touchstart", (e) => {
      if (!modal || modal.style.display !== "flex" || selectionMode) {
        return
      }

      touchStartX = e.changedTouches[0].screenX
      touchCurrentX = touchStartX
      isDraggingModal = true
      modalImg.style.transition = "none"
    }, { passive: true })

    modalContent.addEventListener("touchmove", (e) => {
      if (!isDraggingModal || !modalImg) {
        return
      }

      touchCurrentX = e.changedTouches[0].screenX
      const diffX = touchCurrentX - touchStartX
      const limitedDiff = Math.max(Math.min(diffX, 120), -120)

      modalImg.style.transform = `translateX(${limitedDiff}px)`
      modalImg.style.opacity = `${Math.max(0.55, 1 - Math.abs(limitedDiff) / 220)}`
    }, { passive: true })

    modalContent.addEventListener("touchend", () => {
      if (!isDraggingModal || !modalImg) {
        return
      }

      const swipeDistance = touchCurrentX - touchStartX
      const minSwipeDistance = 60
      isDraggingModal = false

      if (Math.abs(swipeDistance) >= minSwipeDistance) {
        if (swipeDistance < 0) {
          showNextImage()
        } else {
          showPreviousImage()
        }

        return
      }

      resetModalImageState()
    }, { passive: true })

    modalContent.addEventListener("touchcancel", () => {
      isDraggingModal = false
      resetModalImageState()
    }, { passive: true })
  }

  // Atalhos de teclado no modal
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

  updateSelectedCount()
  updateBulkSelectionState()

  // Handler para mostrar loading durante upload de fotos
  if (uploadForm && uploadBtn) {
    uploadForm.addEventListener("submit", (e) => {
      const hasImages = fileInput && fileInput.files && fileInput.files.length > 0

      if (!hasImages) {
        e.preventDefault()
        return
      }

      // Desabilitar botão
      uploadBtn.disabled = true
      uploadBtn.style.opacity = "0.6"
      uploadBtn.style.cursor = "not-allowed"

      // Guardar texto original
      const originalText = uploadBtn.textContent

      // Mostrar spinner + texto
      uploadBtn.innerHTML = `
        <span style="display: inline-flex; align-items: center; gap: 8px;">
          <span class="spinner" style="
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
          "></span>
          A carregar...
        </span>
      `

      // Se o formulário não submeter num timeout razoável, reabilitar
      const timeoutId = setTimeout(() => {
        uploadBtn.disabled = false
        uploadBtn.style.opacity = "1"
        uploadBtn.style.cursor = "pointer"
        uploadBtn.textContent = originalText
      }, 30000) // 30 segundos

      // Limpar timeout se o formulário submeter realmente
      uploadForm.addEventListener("submit", () => clearTimeout(timeoutId), { once: true })
    })
  }
})

// Animação de spinner
const style = document.createElement("style")
style.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`
document.head.appendChild(style)