(function () {
    const transcriptBtn = document.getElementById('brochure-transcript-btn'),
        transcriptContainer = document.getElementById('brochure-transcript'),
        transcriptShownClass = 'transcript-shown';
    
    function showContainer() {
        transcriptBtn.classList.add(transcriptShownClass);
        transcriptContainer.classList.add(transcriptShownClass);
    }// end showContainer()
    
    function hideContainer() {
        transcriptBtn.classList.remove(transcriptShownClass);
        transcriptContainer.classList.remove(transcriptShownClass);
    }// end hideContainer()
    
    function setButtonToView() {
        transcriptBtn.setAttribute('alt', 'Click to view video transcript');
        transcriptBtn.setAttribute('aria-expanded', 'false');
        transcriptBtn.innerHTML = 'View Video Transcript';
    }// end setButtonToView()
    
    function setButtonToHide() {
        transcriptBtn.setAttribute('alt', 'Click to hide video transcript');
        transcriptBtn.setAttribute('aria-expanded', 'true');
        transcriptBtn.innerHTML = 'Hide Video Transcript';
    }// end setButtonToHide()
    
    function handleButtonClick() {
        if (transcriptBtn.classList.contains(transcriptShownClass)) {
            hideContainer();
            setButtonToView();
        } else {
            showContainer();
            setButtonToHide();
        }// end if/else
    }// end handleButtonClick()
    
    if (transcriptBtn) {
        transcriptBtn.addEventListener('click', handleButtonClick);
    }// end if
})();

