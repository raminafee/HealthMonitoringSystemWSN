document.getElementById("data-form").addEventListener("submit", function (event) {
    event.preventDefault();  

    var formData = new FormData();
    formData.append("file", document.getElementById("file-input").files[0]);  

    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => { throw new Error(errorData.error || 'خطأ غير معروف'); });
            }
            return response.json();
        })
        .then(data => {
           
            document.getElementById("text-analysis").innerText = data.textAnalysis;

          
            document.getElementById("data-chart").src = 'data:image/png;base64,' + data.imageBase64;
        })
        .catch(error => {
            console.error("Error analyzing data:", error);
            alert("حدث خطأ: " + error.message);  
        });
});
