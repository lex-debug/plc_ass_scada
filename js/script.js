document.addEventListener('DOMContentLoaded', function() {
    // Create a Chart.js instance
    var ctx = document.getElementById('graph').getContext('2d');
    var chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Data',
                data: [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true
                },
                y: {
                    display: true
                }
            }
        }
    });

    // Fetch data from the server
    function fetchData() {
        fetch('http://localhost/data.php')
        .then(response => response.json())
        .then(data => {
            // Update the chart with new data
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.values;
            chart.update();
        });
    }

    // Fetch data initially and then every 1 second
    fetchData();
    setInterval(fetchData, 1000);
});