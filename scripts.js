document.getElementById("data-form").addEventListener("submit", function (event) {
    event.preventDefault();

    var formData = new FormData();
    formData.append("file", document.getElementById("file-input").files[0]);

    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // عرض النص التحليلي
            document.getElementById("text-analysis").innerText = data.textAnalysis;

            // عرض الرسم البياني
            var ctx = document.getElementById('data-chart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'درجة الحرارة',
                        data: data.temperatureData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        fill: false
                    },
                    {
                        label: 'ضغط الدم',
                        data: data.bloodPressureData,
                        borderColor: 'rgba(153, 102, 255, 1)',
                        fill: false
                    },
                    {
                        label: 'السكري',
                        data: data.diabetesData,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            beginAtZero: true
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Error analyzing data:", error));
});
