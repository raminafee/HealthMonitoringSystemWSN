document.getElementById("data-form").addEventListener("submit", function (event) {
    event.preventDefault();  // منع الإرسال الافتراضي للنموذج

    var formData = new FormData();
    formData.append("file", document.getElementById("file-input").files[0]);  // إضافة الملف إلى FormData

    fetch('/analyze3', {
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
            // عرض النص التحليلي
            document.getElementById("text-analysis").innerText = data.textAnalysis;

            // عرض الرسم البياني
            document.getElementById("data-chart").src = 'data:image/png;base64,' + data.imageBase64;
        })
        .catch(error => {
            console.error("Error analyzing data:", error);
            alert("حدث خطأ: " + error.message);  // عرض الخطأ في حال فشل الطلب
        });
});
