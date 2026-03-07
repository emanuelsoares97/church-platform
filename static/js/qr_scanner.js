function getCookie(name){
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if(parts.length === 2){
        return parts.pop().split(";").shift();
    }
    return "";
}

function extractTicketCode(rawValue){

    if(!rawValue) return "";

    const clean = rawValue.trim();

    if(!clean) return "";

    try{
        const parsed = new URL(clean);
        const parts = parsed.pathname.split("/").filter(Boolean);
        return parts[parts.length - 1] || "";
    }
    catch(e){
        return clean;
    }

}

document.addEventListener("DOMContentLoaded", function(){

    const manualInput = document.getElementById("manualTicketInput");
    const manualBtn = document.getElementById("openManualTicket");

    const feedbackBox = document.getElementById("scanFeedback");
    const feedbackTitle = document.getElementById("scanFeedbackTitle");
    const feedbackText = document.getElementById("scanFeedbackText");

    const scanCheckinUrl = window.scanCheckinUrl;
    const csrftoken = getCookie("csrftoken");

    let scannerLocked = false;

    function setFeedback(type, title, text){

        if(!feedbackBox) return;

        feedbackBox.className = `scanFeedback scanFeedback--${type}`;
        feedbackTitle.textContent = title;
        feedbackText.textContent = text;
    }

    function vibrateSuccess(){
        if(navigator.vibrate){
            navigator.vibrate([120, 60, 120]);
        }
    }

    function vibrateError(){
        if(navigator.vibrate){
            navigator.vibrate([220]);
        }
    }

    function resetScannerState(){
        scannerLocked = false;

        if(manualInput){
            manualInput.value = "";
            manualInput.blur();
        }

        setFeedback("idle", "Pronto para ler", "Aguardando leitura do próximo bilhete.");
    }

    async function handleTicket(ticketCode){

        const cleanCode = extractTicketCode(ticketCode);

        if(!cleanCode || scannerLocked) return;

        scannerLocked = true;

        setFeedback("loading", "A validar bilhete...", "Espera um momento.");

        try{
            const response = await fetch(scanCheckinUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: new URLSearchParams({
                    ticket_code: cleanCode
                }).toString()
            });

            const data = await response.json();

            // se estiver tudo ok, faz check-in automatico e fica no scanner
            if(data.ok){
                setFeedback(
                    "success",
                    "Check-in confirmado",
                    `${data.participant_name} • ${data.event_title}`
                );
                vibrateSuccess();

                setTimeout(() => {
                    resetScannerState();
                }, 2200);

                return;
            }

            // se o pagamento estiver pendente, abre logo a pagina do grupo
            if(data.status === "payment_pending"){
                vibrateError();

                if(data.lookup_url){
                    window.location.href = data.lookup_url;
                    return;
                }
            }

            // se ja fez check-in, mostra aviso no scanner e nao redireciona
            if(data.status === "already_checked_in"){
                setFeedback(
                    "warn",
                    "Check-in já realizado",
                    `${data.participant_name} • ${data.ticket_code}`
                );
                vibrateError();

                setTimeout(() => {
                    resetScannerState();
                }, 2200);

                return;
            }

            // se nao encontrar o bilhete, mostra erro
            if(data.status === "not_found"){
                setFeedback(
                    "error",
                    "Bilhete não encontrado",
                    cleanCode
                );
                vibrateError();

                setTimeout(() => {
                    resetScannerState();
                }, 2200);

                return;
            }

            // fallback para qualquer outro caso
            setFeedback(
                "error",
                "Não foi possível validar",
                data.message || "Tenta novamente."
            );
            vibrateError();

            setTimeout(() => {
                resetScannerState();
            }, 2200);

        }
        catch(error){
            console.error("Erro ao validar bilhete:", error);

            setFeedback(
                "error",
                "Erro de ligação",
                "Não foi possível comunicar com o servidor."
            );
            vibrateError();

            setTimeout(() => {
                resetScannerState();
            }, 2200);
        }

    }

    // abrir manualmente pelo botao
    manualBtn?.addEventListener("click", function(){
        handleTicket(manualInput.value);
    });

    // permitir ENTER no input manual
    manualInput?.addEventListener("keydown", function(e){
        if(e.key === "Enter"){
            e.preventDefault();
            handleTicket(manualInput.value);
        }
    });

    function onScanSuccess(decodedText){
        handleTicket(decodedText);
    }

    const html5QrCode = new Html5Qrcode("qr-reader");

    Html5Qrcode.getCameras().then(devices => {

        if(devices && devices.length){
            html5QrCode.start(
                { facingMode: "environment" },
                {
                    fps: 10,
                    qrbox: 260
                },
                onScanSuccess
            );
        }
        else{
            setFeedback(
                "error",
                "Câmara não encontrada",
                "Não foi possível detetar uma câmara neste dispositivo."
            );
        }

    }).catch(err => {
        console.error("Erro ao iniciar câmera:", err);

        setFeedback(
            "error",
            "Erro ao abrir câmara",
            "Verifica as permissões do navegador e tenta novamente."
        );
    });

});